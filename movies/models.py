import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField('name', max_length=255)
    description = models.TextField('description', blank=True)

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField('full_name', max_length=255)

    class Meta:
        db_table = "content\".\"person"
        verbose_name = 'Актёр'
        verbose_name_plural = 'Актёры'


class Filmwork(UUIDMixin, TimeStampedMixin):
    title = models.CharField('title', max_length=255)
    description = models.TextField('description', blank=True)
    creation_date = models.DateField()
    rating = models.FloatField('rating', blank=True,
                              validators=[MinValueValidator(0),
                                          MaxValueValidator(100)])
    type = models.CharField('type', max_length=255)
    genres = models.ManyToManyField(Genre, through='GenreFilmwork')
    persons = models.ManyToManyField(Person, through='PersonFilmwork')

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = 'Кинопроизведение'
        verbose_name_plural = 'Кинопроизведения'


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        unique_together = (('film_work_id', 'genre_id'),)
        verbose_name = 'Жанр фильма'
        verbose_name_plural = 'Жанры фильма'


class PersonFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    role = models.TextField('role')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        unique_together = (('film_work_id', 'person_id'),)
        verbose_name = 'Актёр'
        verbose_name_plural = 'Актёры'




