from faker import Faker

import random
import threading
from concurrent.futures import ThreadPoolExecutor
from movies.models import Genre, Country, Director, Movie, Rating, Review
from django.contrib.auth.models import User
from itertools import islice
from django.db import transaction, close_old_connections, connection

BASE_URL = 'http://127.0.0.1:8000/api/'
fake = Faker('ru_RU')

# lock = threading.Lock()

def create_genres():
    if (Genre.objects.exists()):
        return
    genres = [
        'Драма', 'Комедия', 'Боевик', 'Фантастика',
        'Триллер', 'Ужасы', 'Мелодрама', 'Детектив',
        'Приключения', 'Анимация', 'История', 'Фэнтези'
    ]
    Genre.objects.bulk_create(
        [Genre(title=g) for g in genres]
    )

def create_countries():
    if (Country.objects.exists()):
        return
    countries = [
        "Россия", "США", "Великобритания", "Франция", "Германия",
        "Италия", "Испания", "Канада", "Япония", "Китай",
        "Индия", "Австралия", "Бразилия", "Мексика", "Южная Корея",
        "Швеция", "Норвегия", "Польша", "Турция", "Аргентина"
    ]
    Country.objects.bulk_create(
        [Country(title=c) for c in countries],
        batch_size=1000
    )

def create_directors():
    Director.objects.bulk_create([
        Director(
            full_name=fake.name(),
            short_biography=fake.paragraph(),
            date_of_birth=fake.date_of_birth(minimum_age=23, maximum_age=89)
        )
        for _ in range(1000)
    ])

def create_users():
    new_users = []
    for _ in range(1000):
        user = User(
            username=f"{fake.uuid4()}",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            date_joined=fake.date_between(start_date='-25y', end_date='today')
        )
        user.set_password(fake.password(length=random.randint(4, 16)))
        new_users.append(user)

    User.objects.bulk_create(new_users)

def create_movies():
    close_old_connections()
    directors = list(Director.objects.values_list('pk', flat=True))
    genres = list(Genre.objects.values_list('pk', flat=True))
    countries = list(Country.objects.values_list('pk', flat=True))
    movies = [
        Movie(
            title=fake.catch_phrase(),
            date_of_release=fake.date_between(start_date='-70y', end_date='-1y'),
            brief_information=fake.paragraph()
        )
        for _ in range(1000)
    ]
    with transaction.atomic():
        Movie.objects.bulk_create(movies)

        Movie.directors.through.objects.bulk_create([
            Movie.directors.through(
                movie_id=movie.id,
                director_id=d_id
            )
            for movie in movies
            for d_id in random.sample(directors, random.randint(1, 3))
        ])

        Movie.genres.through.objects.bulk_create([
            Movie.genres.through(
                movie_id=movie.id,
                genre_id=g_id
            )
            for movie in movies
            for g_id in random.sample(genres, random.randint(1, 5))
        ])

        Movie.countries.through.objects.bulk_create([
            Movie.countries.through(
                movie_id=movie.id,
                country_id=c_id
            )
            for movie in movies
            for c_id in random.sample(countries, random.randint(1, 5))
        ])
    close_old_connections()

def create_ratings():
    users = list(
        User.objects.values_list('pk', 'date_joined')
    )
    movies = list(
        Movie.objects.values_list('pk', 'date_of_release')
    )
    ratings = []
    for _ in range(1000):
        u_id, u_date_joined = random.choice(users)
        m_id, m_date_of_release = random.choice(movies)

        max_date = max(
            u_date_joined.date(),
            m_date_of_release
        )
        rating = Rating(
            user_id=u_id,
            movie_id=m_id,
            rating_value=random.randint(1, 10),
            created_at=fake.date_time_between(
                start_date=max_date,
                end_date='now'
            )
        )
        ratings.append(rating)
    insert_ratings(ratings)

def create_reviews():
    close_old_connections()
    fake = Faker('ru_RU')
    ratings = list(
        Rating.objects.all()
    )
    # Получение ID рейтингов, для которых уже существуют рецензии
    existing_rating_ids = set(
        Review.objects.values_list('rating_id', flat=True)
    )
    # Выбираем рейтинги, для которых ещё нет рецензий
    available_ratings = [
        rating
        for rating in ratings
        if rating.pk not in existing_rating_ids
    ]
    reviews_count = int(len(available_ratings) * 0.2)
    selected_ratings = random.sample(
        available_ratings,
        reviews_count
    )
    reviews = []
    for rating in selected_ratings:
        review = Review(
            rating_id=rating.pk,
            text=fake.paragraph(nb_sentences=random.randint(3, 8)),
            is_spoiler=random.choice([True, False])
        )

        reviews.append(review)

    Review.objects.bulk_create(
        reviews,
        batch_size=1000
    )
    close_old_connections()

def insert_ratings(ratings, batch_size=300):
    table = connection.ops.quote_name(
        Rating._meta.db_table
    )
    user_col = connection.ops.quote_name(
        Rating._meta.get_field('user').column
    )
    movie_col = connection.ops.quote_name(
        Rating._meta.get_field('movie').column
    )
    value_col = connection.ops.quote_name(
        Rating._meta.get_field('rating_value').column
    )
    date_col = connection.ops.quote_name(
        Rating._meta.get_field('created_at').column
    )
    inserted = 0
    iterator = iter(ratings)

    while batch := list(islice(iterator, batch_size)):
        unique = {}
        for rating in batch:
            unique[(rating.user_id, rating.movie_id)] = rating

        batch = list(unique.values())
        values = ', '.join(
            ['(%s, %s, %s, %s)'] * len(batch)
        )
        sql = f"""
            INSERT INTO {table}
                ({user_col}, {movie_col}, {value_col}, {date_col})
            SELECT
                source.user_id,
                source.movie_id,
                source.rating_value,
                source.created_at
            FROM (VALUES {values})
                AS source(user_id, movie_id, rating_value, created_at)
            WHERE NOT EXISTS (
                SELECT 1
                FROM {table} AS target WITH (UPDLOCK, HOLDLOCK)
                WHERE target.{user_col} = source.user_id
                  AND target.{movie_col} = source.movie_id
            );
        """
        params = []
        for rating in batch:
            params.extend([
                rating.user_id,
                rating.movie_id,
                rating.rating_value,
                rating.created_at,
            ])

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                inserted += cursor.rowcount

    return inserted

def run_task(func):
    close_old_connections()

    try:
        print(f'Начало выполнения: {func.__name__}')

        func()

        print(f'Завершение выполнения: {func.__name__}')

    finally:
        close_old_connections()

def generate_data():
    max_workers = 4

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(run_task, create_genres),
            executor.submit(run_task, create_countries)
        ]

        for future in futures:
            future.result()

        futures = [
            executor.submit(run_task, create_directors),
            executor.submit(run_task, create_users)
        ]

        for future in futures:
            future.result()

        executor.submit(run_task, create_movies).result()

        executor.submit(run_task, create_ratings).result()