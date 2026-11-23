from faker import Faker

import random
import threading
from concurrent.futures import ThreadPoolExecutor
from movies.models import Genre, Country, Director, Movie, Rating, Review
from django.contrib.auth.models import User
from django.db import connection
from datetime import date, datetime, time, timedelta
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Max

fake = Faker('ru_RU')
START_DATE = date(1995, 1, 1)
END_DATE = date.today()

GENRES = ['драма', 'комедия', 'боевик', 'фантастика', 'ужасы', 'триллер',
          'мелодрама', 'детектив', 'приключения', 'фэнтези', 'документальный',
          'анимация', 'мюзикл', 'вестерн', 'военный', 'исторический',
          'криминал', 'семейный', 'спорт', 'биография']
COUNTRIES = ['США', 'Россия', 'Великобритания', 'Франция', 'Германия', 'Италия',
             'Испания', 'Япония', 'Китай', 'Индия', 'Канада', 'Австралия',
             'Бразилия', 'Мексика', 'Южная Корея', 'Швеция', 'Дания',
             'Норвегия', 'Польша', 'Турция']
RATING_WEIGHTS = [1, 1, 2, 3, 5, 8, 10, 12, 10, 7]

def _aware(dt):
    """Faker отдаёт naive datetime; трактуем как локальное время."""
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def _local_naive(dt):
    """aware → naive в локальной TZ (для faker)."""
    return timezone.localtime(dt).replace(tzinfo=None) if timezone.is_aware(dt) else dt

def gen_directors(n=10):
    objs = [Director(
        full_name=fake.name(),
        short_biography=fake.text(max_nb_chars=400) if random.random() < 0.7 else None,
        date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=95)
                       if random.random() < 0.9 else None,
    ) for _ in range(n)]
    Director.objects.bulk_create(objs, batch_size=500)
    connection.close()
    print(f'  directors: {n}')
    pass

def gen_genres():
    if (Genre.objects.exists()):
        return
    Genre.objects.bulk_create(
        [Genre(title=g) for g in GENRES]
    )
    connection.close()

def gen_countries():
    if (Country.objects.exists()):
        return
    Country.objects.bulk_create(
        [Country(title=c) for c in COUNTRIES]
    )
    connection.close()

def gen_users(n=100):
    pwd = make_password('password123')
    objs = [User(
        username=f'{fake.user_name()}_{fake.uuid4()}',
        password=pwd,
        email=fake.email(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        date_joined=_aware(fake.date_time_between(
            start_date=START_DATE, end_date='now')),
    ) for _ in range(n)]
    User.objects.bulk_create(objs, batch_size=100)
    connection.close()
    print(f'  users: {n}')
    pass

def gen_movies(n=50):
    dir_ids = list(Director.objects.values_list('id', flat=True))
    gen_ids = list(Genre.objects.values_list('id', flat=True))
    cnt_ids = list(Country.objects.values_list('id', flat=True))

    max_id_before = Movie.objects.aggregate(m=Max('id'))['m'] or 0
    movies = [Movie(
        title=fake.sentence(nb_words=3).rstrip('.').capitalize(),
        date_of_release=fake.date_between(start_date=date(1980, 1, 1),
                                          end_date=END_DATE),
        brief_information=fake.text(max_nb_chars=500) if random.random() < 0.6 else None,
    ) for _ in range(n)]
    Movie.objects.bulk_create(movies, batch_size=500)

    mids = list(Movie.objects.filter(id__gt=max_id_before)
                .values_list('id', flat=True))
    d_th, g_th, c_th = (Movie.directors.through,
                        Movie.genres.through,
                        Movie.countries.through)
    d_links, g_links, c_links = [], [], []
    for mid in mids:
        for did in random.sample(dir_ids, random.randint(1, 3)):
            d_links.append(d_th(movie_id=mid, director_id=did))
        for gid in random.sample(gen_ids, random.randint(1, 3)):
            g_links.append(g_th(movie_id=mid, genre_id=gid))
        for cid in random.sample(cnt_ids, random.randint(1, 2)):
            c_links.append(c_th(movie_id=mid, country_id=cid))
    d_th.objects.bulk_create(d_links, batch_size=1000)
    g_th.objects.bulk_create(g_links, batch_size=1000)
    c_th.objects.bulk_create(c_links, batch_size=1000)
    connection.close()
    print(f'  movies: {n}')

def _ratings_chunk(users_data, movies_data, per_user):
    objs = []
    now_naive = datetime.now()
    for uid, u_joined in users_data:
        u_joined_d = timezone.localtime(u_joined).date() \
            if timezone.is_aware(u_joined) else u_joined.date()
        for mid, m_release in random.sample(movies_data, per_user):
            # оценка не раньше регистрации пользователя и выхода фильма
            start_dt = datetime.combine(max(u_joined_d, m_release), time.min) \
                       + timedelta(seconds=1)
            if start_dt >= now_naive:
                continue
            created = _aware(fake.date_time_between(
                start_date=start_dt, end_date=now_naive))
            objs.append(Rating(
                movie_id=mid, user_id=uid,
                rating_value=random.choices(range(1, 11), RATING_WEIGHTS)[0],
                created_at=created,
            ))
    Rating.objects.bulk_create(objs, batch_size=400)
    connection.close()

def gen_ratings(total=500, per_user=10, workers=10):
    users = list(User.objects.filter(ratings__isnull=True)
                 .values_list('id', 'date_joined'))
    movies = list(Movie.objects.values_list('id', 'date_of_release'))
    need = min(total // per_user, len(users))
    users = random.sample(users, need)
    size = max(1, len(users) // workers)
    chunks = [users[i:i + size] for i in range(0, len(users), size)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda c: _ratings_chunk(c, movies, per_user), chunks))
    print(f'  ratings: ~{need * per_user}')

def _reviews_chunk(data):
    objs = []
    now_naive = datetime.now()
    for rid, r_created in data:
        # рецензия не раньше оценки
        start_naive = _local_naive(r_created) + timedelta(seconds=1)
        if start_naive >= now_naive:
            continue
        created = _aware(fake.date_time_between(
            start_date=start_naive, end_date=now_naive))
        objs.append(Review(
            rating_id=rid,
            text=fake.text(max_nb_chars=800),
            is_spoiler=random.random() < 0.1,
            created_at=created,
        ))
    Review.objects.bulk_create(objs, batch_size=400)
    connection.close()

def gen_reviews(n=50, workers=10):
    data = list(Rating.objects.filter(reviews__isnull=True)
                .values_list('id', 'created_at'))
    chosen = random.sample(data, min(n, len(data)))
    size = max(1, len(chosen) // workers)
    chunks = [chosen[i:i + size] for i in range(0, len(chosen), size)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(_reviews_chunk, chunks))
    print(f'  reviews: {len(chosen)}')

def generate_all():
    print('=== Generation started ===')
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs = [ex.submit(gen_directors), ex.submit(gen_genres),
              ex.submit(gen_countries), ex.submit(gen_users)]
        for f in fs:
            f.result()
    gen_movies()
    gen_ratings()
    gen_reviews()
    print('=== Generation finished ===')