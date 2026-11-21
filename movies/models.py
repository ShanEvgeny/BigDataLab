from django.db import models

from django.db import models
from django.utils import timezone

class Director(models.Model):
    id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    short_biography = models.TextField(null=True)
    date_of_birth = models.DateField(null=True)

class Genre(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)

class Country(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)

class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    date_of_release = models.DateField()
    brief_information = models.TextField(null=True)
    directors = models.ManyToManyField(Director, related_name='movies')
    genres = models.ManyToManyField(Genre, related_name='movies')
    countries = models.ManyToManyField(Country, related_name='movies')

class Rating(models.Model):
    id = models.AutoField(primary_key=True)
    rating_value = models.PositiveSmallIntegerField()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='ratings')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('movie', 'user')

class Review(models.Model):
    id = models.AutoField(primary_key=True)
    rating = models.OneToOneField(Rating, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    is_spoiler = models.BooleanField(default = False)
    created_at = models.DateTimeField(default=timezone.now)
