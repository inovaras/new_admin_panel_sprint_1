import io
import os
import psycopg
from dotenv import load_dotenv


if __name__ == '__main__':
    env_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
    load_dotenv(dotenv_path=env_path)
    dsn = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'options': '-c search_path=content',
    }
    with psycopg.connect(**dsn) as conn, conn.cursor() as cursor:
        # Очищаем таблицу в БД, чтобы загружать данные в пустую таблицу
        cursor.execute("""TRUNCATE content.temp_table""")

        # Одиночный insert
        data = ('ca211dbc-a6c6-44a5-b238-39fa16bbfe6c', 'Иван Иванов')
        cursor.execute("""INSERT INTO content.temp_table (id, name) VALUES (%s, %s)""", data)

        # Множественный insert
        # Его можно выполнить с помощью функции execute_values, которая внутри себя
        # подготавливает параметры для VALUES через cursor.mogrify.
        # Это позволяет без опаски передавать параметры на вставку:
        # mogrify позаботится об экранировании и подстановке нужных типов.
        data = [
            ('b8531efb-c49d-4111-803f-725c3abc0f5e', 'Василий Васильевич'),
            ('2d5c50d0-0bb4-480c-beab-ded6d0760269', 'Пётр Петрович'),
        ]
        cursor.executemany('INSERT INTO content.temp_table (id, name) VALUES (%s, %s)', data)

        # Пример использования UPSERT — обновляем уже существующую запись
        data = ('ca211dbc-a6c6-44a5-b238-39fa16bbfe6c', 'Иван Петров')
        cursor.execute(
        """
        INSERT INTO content.temp_table (id, name)
        VALUES (%s, %s)
        ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name
        """,
            data,
        )

        cursor.execute("""SELECT name FROM content.temp_table WHERE id = 'ca211dbc-a6c6-44a5-b238-39fa16bbfe6c'""")
        result = cursor.fetchone()
        print('Результат выполнения команды UPSERT ', result)

        # Используем команду COPY
        # Для работы COPY требуется взять данные из файла или подготовить файловый объект через io.StringIO
        cursor.execute("""TRUNCATE content.temp_table""")
        data = io.StringIO()
        data.write('ca211dbc-a6c6-44a5-b238-39fa16bbfe6c,Михаил Михайлович')
        data.seek(0)

        with cursor.copy("""COPY content.temp_table FROM STDIN (FORMAT 'csv', HEADER false)""") as copy:
            copy.write(data.read())

        cursor.execute("""SELECT name FROM content.temp_table WHERE id = 'ca211dbc-a6c6-44a5-b238-39fa16bbfe6c'""")
        result = cursor.fetchone()
        print('Результат выполнения команды COPY ', result)