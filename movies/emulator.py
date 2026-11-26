import random
import threading
import time

from concurrent.futures import ThreadPoolExecutor
from faker import Faker

from django.contrib.auth.models import User
from django.db import close_old_connections, IntegrityError
from django.utils import timezone
from django.db.models import F, Avg, FloatField
from django.db.models.functions import Cast, Round

from datetime import timedelta

from movies.models import Director, Genre, Country, Movie, Rating, Review


fake = Faker('ru_RU')

WORKERS = 1
CRUD_WEIGHTS = [15, 70, 10, 5]

stop_event = threading.Event()
emulator_thread = None
emulator_lock = threading.Lock()

def random_obj(model):
    # return model.objects.order_by('?').first()
    min_obj = model.objects.earliest("id")
    max_obj = model.objects.latest("id")

    return random.choice([min_obj, max_obj])


def execute(func):
    result = func()
    return list(result) if hasattr(result, 'query') else result



def create_rating():
    user = random_obj(User)
    movie = random_obj(Movie)

    if user and movie:
        Rating.objects.create(
            user=user,
            movie=movie,
            rating_value=random.randint(1, 10),
            created_at=timezone.now()
        )


def create_review():
    rating = random_obj(Rating)

    if rating:
        Review.objects.create(
            rating=rating,
            text=fake.text(max_nb_chars=800),
            is_spoiler=random.choice([True, False]),
            created_at=timezone.now()
        )


def create_movie_director():
    movie = random_obj(Movie)
    director = random_obj(Director)

    if movie and director:
        movie.directors.add(director)


def create_movie_genre():
    movie = random_obj(Movie)
    genre = random_obj(Genre)

    if movie and genre:
        movie.genres.add(genre)


def create_movie_country():
    movie = random_obj(Movie)
    country = random_obj(Country)

    if movie and country:
        movie.countries.add(country)


def create_user():
    User.objects.create_user(
        username=f'{fake.user_name()}_{fake.uuid4()}',
        email=fake.email(),
        password=fake.password(random.randint(4, 16)),
        first_name=fake.first_name(),
        last_name=fake.last_name()
    )


def create_director():
    Director.objects.create(
        full_name=fake.name(),
        short_biography=fake.text(max_nb_chars=400),
        date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=95)
    )


def create_movie():
    Movie.objects.create(
        title=fake.sentence(nb_words=3).rstrip('.').capitalize(),
        date_of_release=fake.date_between(start_date='-25y', end_date='-1y'),
        brief_information=fake.text(max_nb_chars=500)
    )


# -------------------- READ --------------------

def get_movies_by_genre():
    genre = random_obj(Genre)
    if genre:
        return list(Movie.objects.filter(
            genres=genre
        ).order_by('-date_of_release')[:5])


def get_movies_by_director():
    director = random_obj(Director)
    if director:
        return list(Movie.objects.filter(
            directors=director
        ).order_by('-date_of_release')[:5])


def get_movies_by_country():
    country = random_obj(Country)
    if country:
        return list(Movie.objects.filter(
            countries=country
        ).order_by('-date_of_release')[:5])


def get_directors_movie():
    movie = random_obj(Movie)
    if movie:
        return list(movie.directors.all())


def get_genres_movie():
    movie = random_obj(Movie)
    if movie:
        return list(movie.genres.all())


def get_countries_movie():
    movie = random_obj(Movie)
    if movie:
        return list(movie.countries.all())


def get_count_ratings_movie():
    movie = random_obj(Movie)
    if movie:
        return movie.ratings.count()


def get_avg_rating_movie():
    movie = random_obj(Movie)
    if movie:
        return movie.ratings.aggregate(
            avg=Round(Avg(Cast('rating_value', FloatField())), 1)
        )['avg']


def get_user_reviews():
    user = random_obj(User)
    if user:
        return list(Review.objects.filter(rating__user=user))


def get_user_info():
    user = random_obj(User)
    if user:
        return User.objects.filter(pk=user.id).first()


def get_5_new_films():
    return list(Movie.objects.order_by('-date_of_release')[:5])


def get_5_by_rating():
    # return list(
    #     Movie.objects.annotate(
    #         avg_rating=Round(
    #             Avg('ratings__rating_value', output_field=FloatField()), 1
    #         )
    #     ).order_by('-avg_rating')[:5]
    # )
    raw_sql = """
        WITH TopMovies AS (
            SELECT TOP 5
                movie_id,
                ROUND(AVG(CONVERT(float, rating_value)), 1) AS avg_rating
            FROM [movies_rating]
            GROUP BY movie_id
            ORDER BY avg_rating DESC
        )
        SELECT
            m.id,
            m.title,
            m.date_of_release,
            m.brief_information,
            tm.avg_rating
        FROM [movies_movie] AS m
        INNER JOIN TopMovies AS tm ON m.id = tm.movie_id
        ORDER BY tm.avg_rating DESC
    """
    return list(Movie.objects.raw(raw_sql))


def get_5_old_directors():
    return list(Director.objects.order_by('date_of_birth')[:5])


def get_user_ratings():
    user = random_obj(User)
    if user:
        return list(Rating.objects.filter(user=user))


def get_movie_by_title_and_date():
    movie = random_obj(Movie)
    if movie:
        return Movie.objects.filter(
            title=movie.title,
            date_of_release=movie.date_of_release
        ).first()


# -------------------- UPDATE --------------------

def update_movies_title():
    movie = random_obj(Movie)
    if movie:
        movie.title = fake.sentence(nb_words=3).rstrip('.').capitalize()
        movie.save(update_fields=['title'])


def update_movies_brief_info():
    movie = random_obj(Movie)
    if movie:
        movie.brief_information = fake.text(max_nb_chars=500)
        movie.save(update_fields=['brief_information'])


def update_movies_date():
    movie = random_obj(Movie)
    if movie:
        movie.date_of_release += timedelta(days=random.randint(5, 30))
        movie.save(update_fields=['date_of_release'])


def update_directors_full_name():
    director = random_obj(Director)
    if director:
        director.full_name = fake.name()
        director.save(update_fields=['full_name'])


def update_directors_short_biography():
    director = random_obj(Director)
    if director:
        director.short_biography = fake.text(max_nb_chars=400)
        director.save(update_fields=['short_biography'])


def update_directors_birthday():
    director = random_obj(Director)
    if director:
        director.date_of_birth += timedelta(days=random.randint(5, 30))
        director.save(update_fields=['date_of_birth'])


def update_user_password():
    user = random_obj(User)
    if user:
        user.set_password(fake.password(random.randint(4, 16)))
        user.save(update_fields=['password'])


def update_user_is_active():
    user = random_obj(User)
    if user:
        user.is_active = False
        user.save(update_fields=['is_active'])


def update_user_first_name():
    user = random_obj(User)
    if user:
        user.first_name = fake.first_name()
        user.save(update_fields=['first_name'])


def update_user_last_name():
    user = random_obj(User)
    if user:
        user.last_name = fake.last_name()
        user.save(update_fields=['last_name'])


def update_user_first_and_last_names():
    user = random_obj(User)
    if user:
        user.first_name = fake.first_name()
        user.last_name = fake.last_name()
        user.save(update_fields=['first_name', 'last_name'])


def update_user_status_to_admin():
    user = random_obj(User)
    if user:
        user.is_staff = not user.is_staff
        user.save(update_fields=['is_staff'])


def update_rating_value():
    rating = random_obj(Rating)
    if rating:
        rating.rating_value = random.randint(1, 10)
        rating.save(update_fields=['rating_value'])


def update_review_text():
    review = random_obj(Review)
    if review:
        review.text = fake.text(max_nb_chars=800)
        review.save(update_fields=['text'])


def update_review_is_spoiler():
    review = random_obj(Review)
    if review:
        review.is_spoiler = not review.is_spoiler
        review.save(update_fields=['is_spoiler'])


# -------------------- DELETE --------------------

def delete_rating():
    obj = random_obj(Rating)
    if obj:
        obj.delete()


def delete_review():
    obj = random_obj(Review)
    if obj:
        obj.delete()


def delete_movie():
    obj = random_obj(Movie)
    if obj:
        obj.delete()


def delete_director():
    obj = random_obj(Director)
    if obj:
        obj.delete()


def delete_user():
    obj = random_obj(User)
    if obj:
        obj.delete()


def delete_movie_director():
    obj = random_obj(Movie)
    if obj:
        obj.directors.remove(random_obj(Director))


def delete_movie_genre():
    obj = random_obj(Movie)
    if obj:
        obj.genres.remove(random_obj(Genre))


def delete_movie_country():
    obj = random_obj(Movie)
    if obj:
        obj.countries.remove(random_obj(Country))


def delete_genre():
    obj = random_obj(Genre)
    if obj:
        obj.delete()


def delete_country():
    obj = random_obj(Country)
    if obj:
        obj.delete()


# -------------------- ПУЛЫ ОПЕРАЦИЙ --------------------

CREATE_POOL = [
    create_rating,
    create_review,
    create_movie_director,
    create_movie_genre,
    create_movie_country,
    create_user,
    create_director,
    create_movie,
    lambda: create_rating(),
    lambda: create_rating(),
    lambda: create_review(),
    lambda: create_movie_director(),
    lambda: create_movie_genre(),
    lambda: create_movie_country(),
    lambda: create_user(),
]

READ_POOL = [
    get_movies_by_genre,
    get_movies_by_director,
    get_movies_by_country,
    get_directors_movie,
    get_genres_movie,
    get_countries_movie,
    get_count_ratings_movie,
    get_avg_rating_movie,
    get_user_reviews,
    get_user_info,
    get_5_new_films,
    get_5_by_rating,
    get_5_old_directors,
    get_user_ratings,
    get_movie_by_title_and_date,
]

UPDATE_POOL = [
    update_movies_title,
    update_movies_brief_info,
    update_movies_date,
    update_directors_full_name,
    update_directors_short_biography,
    update_directors_birthday,
    update_user_password,
    update_user_is_active,
    update_user_first_name,
    update_user_last_name,
    update_user_first_and_last_names,
    update_user_status_to_admin,
    update_rating_value,
    update_review_text,
    update_review_is_spoiler,
]

DELETE_POOL = [
    delete_rating,
    delete_review,
    delete_movie,
    delete_director,
    delete_user,
    delete_movie_director,
    delete_movie_genre,
    delete_movie_country,
    delete_genre,
    delete_country,
    lambda: delete_rating(),
    lambda: delete_review(),
    lambda: delete_movie(),
    lambda: delete_director(),
    lambda: delete_user(),
]

QUERY_WEIGHTS = {
    'CREATE': [
        12, 7, 7, 7, 7, 12, 6, 8, 5, 5, 5, 4, 4, 4, 7
    ],
    'READ': [
        5, 5, 5, 4, 4, 4, 6, 5, 5, 6, 12, 12, 8, 8, 11
    ],
    'UPDATE': [
        10, 8, 5, 8, 6, 4, 5, 5, 8, 8, 8, 4, 8, 8, 5
    ],
    'DELETE': [
        60, 20, 0, 0, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0
    ]
}



# -------------------- ЗАПУСК ЭМУЛЯТОРА --------------------

POOLS = {
    'CREATE': CREATE_POOL,
    'READ': READ_POOL,
    'UPDATE': UPDATE_POOL,
    'DELETE': DELETE_POOL
}


def worker():
    while not stop_event.is_set():
        close_old_connections()

        try:
            operation = random.choices(
                list(POOLS.keys()),
                weights=CRUD_WEIGHTS
            )[0]

            func = random.choices(
                POOLS[operation],
                weights=QUERY_WEIGHTS[operation]
            )[0]

            execute(func)

        except IntegrityError:
            pass
        except Exception as e:
            print(f'Ошибка эмулятора: {e}')

        finally:
            close_old_connections()

        stop_event.wait(random.uniform(0.1, 1.5))


def run_emulator():
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(worker) for _ in range(WORKERS)]

        for future in futures:
            future.result()


def start_emulator():
    global emulator_thread

    with emulator_lock:
        if emulator_thread and emulator_thread.is_alive():
            return False

        stop_event.clear()
        emulator_thread = threading.Thread(
            target=run_emulator,
            daemon=True
        )
        emulator_thread.start()

    return True


def stop_emulator():
    stop_event.set()

    if emulator_thread and emulator_thread.is_alive():
        emulator_thread.join(timeout=3)

    return not emulator_thread or not emulator_thread.is_alive()


def emulator_status():
    return emulator_thread is not None and emulator_thread.is_alive()