import random
import threading
import time

from concurrent.futures import ThreadPoolExecutor
from faker import Faker

from django.contrib.auth.models import User
from django.db import close_old_connections, IntegrityError
from django.utils import timezone

from movies.models import Director, Genre, Country, Movie, Rating, Review
from django.db.models import F, Avg, FloatField
from datetime import timedelta
from django.db.models.functions import Cast, Round


fake = Faker('ru_RU')

WORKERS = 10

CRUD_WEIGHTS = [15, 70, 10, 5]  # Create, Read, Update, Delete

stop_event = threading.Event()
emulator_thread = None

def random_obj(model, count = 1):
    return model.objects.order_by('?')[:count]
    
def create_rating():
    user = random_obj(User)
    movie = random_obj(Movie)
    Rating.objects.create(
        user=user,
        movie=movie,
        rating_value=random.randint(1, 10),
        created_at=timezone.now()
    )

def create_review():
    rating = random_obj(Rating)
    Review.objects.create(
        rating=rating,
        text=fake.text(max_nb_chars=800),
        is_spoiler=random.choice([True, False]),
        created_at=timezone.now()
    )

def create_movie_director():
    movie = random_obj(Movie)
    director = random_obj(Director)
    movie.directors.add(director)

def create_movie_genre():
    movie = random_obj(Movie)
    genre = random_obj(Genre) 
    movie.genres.add(genre)

def create_movie_country():
    movie = random_obj(Movie)
    country = random_obj(Country) 
    movie.countries.add(country)

def create_user():
    User.objects.create_user(
        username=f'{fake.user_name()}_{fake.uuid4()}',
        email=fake.email(),
        password=fake.password(random.randint(4,16)),
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )

def update_movies_title():
    movie = random_obj(Movie)
    movie.update(title = fake.sentence(nb_words=3).rstrip('.').capitalize())

def update_movies_brief_info():
    movie = random_obj(Movie)
    movie.update(brief_information=fake.text(max_nb_chars=500))

def update_movies_date():
    movie = random_obj(Movie)
    movie.update(date_of_release=F('date_of_release') + timedelta(days=random.randint(5, 30)))

def update_directors_full_name():
    director = random_obj(Director)
    director.update(full_name = fake.name())

def update_directors_short_biography():
    director = random_obj(Director)
    director.update(short_biography=fake.text(max_nb_chars=400))

def update_directors_birthday():
    director = random_obj(Director)
    director.update(date_of_birth=F('date_of_birth') + timedelta(days=random.randint(5, 30)))

def update_user_password():
    user = random_obj(User)
    user.set_password(fake.password(random.randint(4,16)))
    user.save(update_fields=['password'])

def update_user_is_active():
    user = random_obj(User)
    user.is_active = False
    user.save(update_fields=['is_active'])

def update_user_first_name():
    user = random_obj(User)
    user.update(first_name = fake.first_name())

def update_user_last_name():
    user = random_obj(User)
    user.update(last_name = fake.last_name())

def update_user_first_and_last_names():
    user = random_obj(User)
    user.update(
        first_name = fake.first_name(),
        last_name = fake.last_name()
    )

def update_user_last_login():
    user = random_obj(User)
    user.update(last_login = timezone.now())

def update_rating_value():
    rating = random_obj(Rating)
    rating.update(rating_value = random.randint(1,10))

def update_review_text():
    review = random_obj(Review)
    review.update(text = fake.text(max_nb_chars=800))

def update_review_is_spoiler():
    review = random_obj(Review)
    review.update(fake.text(max_nb_chars=800))

def get_movies_by_genre():
    genre = random_obj(Genre)
    Movie.objects.filter(genres=genre).order_by('-date_of_release')[:5]

def get_movies_by_director():
    director = random_obj(Director)
    Movie.objects.filter(directors=director).order_by('-date_of_release')[:5]

def get_movies_by_country():
    country = random_obj(Country)
    Movie.objects.filter(countries=country).order_by('-date_of_release')[:5]

def get_directors_movie():
    movie = random_obj(Movie)
    movie.directors.all

def get_genres_movie():
    movie = random_obj(Movie)
    movie.genres.all

def get_countries_movie():
    movie = random_obj(Movie)
    movie.directors.all

def get_count_ratings_movie():
    movie = random_obj(Movie)
    movie.ratings.count()

def get_avg_rating_movie():
    movie = random_obj(Movie)
    movie.aggregate(avg=Round(Avg(Cast('rating_value', FloatField())), 1))['avg']

def get_user_reviews():
    user = random_obj(User)
    Review.objects.filter(rating__user=user)

def get_user_info():
    user = random_obj(User)
    User.objects.filter(pk=user.id).first()

def get_5_new_films():
    Movie.objects.order_by('-date_of_release')[:5]

def get_5_by_rating():
    Movie.objects.annotate(
        avg_rating = Round(Avg(Cast('rating_value', FloatField())), 1)
    ).order_by('-avg_rating')[:5]

def get_5_old_directors():
    Director.objects.order_by('date_of_birth')[:5]

def get_user_ratings():
    user = random_obj(User)
    Rating.objects.filter(user = user)

def get_movie_by_title_and_date():
    movie = random_obj(Movie)
    Movie.objects.filter(title = movie.title, date_of_release = movie.date_of_release).first()

CREATE_POOL = [
    create_rating,
    create_review,
    create_movie_director,
    create_movie_genre,
    create_movie_country,
    create_user,
    lambda: Director.objects.create(
        full_name=fake.name(),
        short_biography=fake.text(max_nb_chars=400) if random.random() < 0.7 else None,
        date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=95)
    ),
    lambda: Movie.objects.create(
        title=fake.sentence(nb_words=3).rstrip('.').capitalize(),
        date_of_release=fake.date_between(start_date='-25y', end_date='-1y'),
        brief_information=fake.text(max_nb_chars=500)
    ),
]

UPDATE_POOL = [
    
]