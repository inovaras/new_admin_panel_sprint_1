import logging
import os
import sqlite3
import sys
from dataclasses import dataclass
from typing import Generator, List

import psycopg
from dotenv import load_dotenv
from psycopg import ClientCursor
from psycopg import connection as _connection
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class FilmWork:
    id: str
    title: str
    description: str
    creation_date: str
    rating: float
    type: str
    created_at: str
    updated_at: str


@dataclass
class Genre:
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str


@dataclass
class Person:
    id: str
    full_name: str
    created_at: str
    updated_at: str


@dataclass
class GenreFilmWork:
    id: str
    genre_id: str
    film_work_id: str
    created_at: str


@dataclass
class PersonFilmWork:
    id: str
    film_work_id: str
    person_id: str
    role: str
    created_at: str


class SQLiteLoader:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.check_tables()

    def check_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.debug(f"Tables in the database: {tables}")
        if not tables:
            raise Exception("No tables found in the database. Please check your database file.")

    def load_film_works(self, batch_size: int = 100) -> Generator[List[FilmWork], None, None]:
        cursor = self.connection.cursor()
        cursor.row_factory = sqlite3.Row
        logger.debug("Executing query for film_work")
        cursor.execute("SELECT id, title, description, creation_date, rating, type, created_at, updated_at FROM film_work")
        while batch := cursor.fetchmany(batch_size):
            yield [FilmWork(**dict(row)) for row in batch]

    def load_genres(self, batch_size: int = 100) -> Generator[List[Genre], None, None]:
        cursor = self.connection.cursor()
        cursor.row_factory = sqlite3.Row
        logger.debug("Executing query for genre")
        cursor.execute("SELECT id, name, description, created_at, updated_at FROM genre")
        while batch := cursor.fetchmany(batch_size):
            yield [Genre(**dict(row)) for row in batch]

    def load_persons(self, batch_size: int = 100) -> Generator[List[Person], None, None]:
        cursor = self.connection.cursor()
        cursor.row_factory = sqlite3.Row
        logger.debug("Executing query for person")
        cursor.execute("SELECT id, full_name, created_at, updated_at FROM person")
        while batch := cursor.fetchmany(batch_size):
            yield [Person(**dict(row)) for row in batch]

    def load_genre_film_works(self, batch_size: int = 100) -> Generator[List[GenreFilmWork], None, None]:
        cursor = self.connection.cursor()
        cursor.row_factory = sqlite3.Row
        logger.debug("Executing query for genre_film_work")
        cursor.execute("SELECT id, genre_id, film_work_id, created_at FROM genre_film_work")
        while batch := cursor.fetchmany(batch_size):
            yield [GenreFilmWork(**dict(row)) for row in batch]

    def load_person_film_works(self, batch_size: int = 100) -> Generator[List[PersonFilmWork], None, None]:
        cursor = self.connection.cursor()
        cursor.row_factory = sqlite3.Row
        logger.debug("Executing query for person_film_work")
        cursor.execute("SELECT id, film_work_id, person_id, role, created_at FROM person_film_work")
        while batch := cursor.fetchmany(batch_size):
            yield [PersonFilmWork(**dict(row)) for row in batch]


class PostgresSaver:
    def __init__(self, connection: _connection):
        self.connection = connection

    def save_all_data(self, data: dict):
        self.save_film_works(data['film_works'])
        self.save_genres(data['genres'])
        self.save_persons(data['persons'])
        self.save_genre_film_works(data['genre_film_works'])
        self.save_person_film_works(data['person_film_works'])

    def save_film_works(self, film_works: List[FilmWork]):
        with self.connection.cursor() as cursor:
            for film_work in film_works:
                cursor.execute("""
                    INSERT INTO content.film_work (id, title, description, creation_date, rating, type, created, modified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (film_work.id, film_work.title, film_work.description, film_work.creation_date, film_work.rating, film_work.type, film_work.created_at, film_work.updated_at))

    def save_genres(self, genres: List[Genre]):
        with self.connection.cursor() as cursor:
            for genre in genres:
                cursor.execute("""
                    INSERT INTO content.genre (id, name, description, created, modified)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (genre.id, genre.name, genre.description, genre.created_at, genre.updated_at))

    def save_persons(self, persons: List[Person]):
        with self.connection.cursor() as cursor:
            for person in persons:
                cursor.execute("""
                    INSERT INTO content.person (id, full_name, created, modified)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (person.id, person.full_name, person.created_at, person.updated_at))

    def save_genre_film_works(self, genre_film_works: List[GenreFilmWork]):
        with self.connection.cursor() as cursor:
            for genre_film_work in genre_film_works:
                cursor.execute("""
                    INSERT INTO content.genre_film_work (id, genre_id, film_work_id, created)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (genre_film_work.id, genre_film_work.genre_id, genre_film_work.film_work_id, genre_film_work.created_at))

    def save_person_film_works(self, person_film_works: List[PersonFilmWork]):
        with self.connection.cursor() as cursor:
            for person_film_work in person_film_works:
                try:
                    cursor.execute("""
                        INSERT INTO content.person_film_work (id, film_work_id, person_id, role, created)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (person_film_work.id, person_film_work.film_work_id, person_film_work.person_id,
                          person_film_work.role, person_film_work.created_at))
                except psycopg.errors.UniqueViolation as e:
                    logger.debug(f"Ignoring duplicate entry: {e}")
                    self.connection.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error inserting record: {e}")
                    self.connection.rollback()
                    continue
                else:
                    self.connection.commit()


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)

    data = {
        'film_works': [],
        'genres': [],
        'persons': [],
        'genre_film_works': [],
        'person_film_works': []
    }

    for film_works_batch in sqlite_loader.load_film_works():
        data['film_works'].extend(film_works_batch)
    for genres_batch in sqlite_loader.load_genres():
        data['genres'].extend(genres_batch)
    for persons_batch in sqlite_loader.load_persons():
        data['persons'].extend(persons_batch)
    for genre_film_works_batch in sqlite_loader.load_genre_film_works():
        data['genre_film_works'].extend(genre_film_works_batch)
    for person_film_works_batch in sqlite_loader.load_person_film_works():
        data['person_film_works'].extend(person_film_works_batch)

    postgres_saver.save_all_data(data)


if __name__ == '__main__':
    env_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
    load_dotenv(dotenv_path=env_path)

    dsl = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'options': '-c search_path=content',
    }
    with sqlite3.connect('db.sqlite') as sqlite_conn:
        sqlite_conn.row_factory = sqlite3.Row
        with psycopg.connect(
            **dsl, row_factory=dict_row, cursor_factory=ClientCursor
        ) as pg_conn:
            load_from_sqlite(sqlite_conn, pg_conn)
