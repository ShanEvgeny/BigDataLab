# import os
# import django

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
# django.setup()

# from django.contrib.auth.models import User
# from movies.generator_server import generate_all
# from movies.models import Director, Genre, Country, Movie, Rating, Review

# MODELS = [('Directors', Director), ('Genres', Genre), ('Countries', Country),
#           ('Movies', Movie), ('Users', User), ('Ratings', Rating),
#           ('Reviews', Review),('MovieDirectors', Movie.directors.through),
#           ('MovieGenres', Movie.genres.through),
#           ('MovieCountries', Movie.countries.through),]


# def show_counts():
#     print('\n--- Сгенерировано записей ---')
#     for name, model in MODELS:
#         print(f'  {name:<22}: {model.objects.count():>10}')


# def main():
#     while True:
#         print('\n1 - Запустить генерацию')
#         print('2 - Показать количество по таблицам')
#         print('0 - Выход')
#         c = input('> ').strip()
#         if c == '1':
#             generate_all()
#         elif c == '2':
#             show_counts()
#         elif c == '0':
#             break


# if __name__ == '__main__':
#     main()
import requests


BASE_URL = 'http://127.0.0.1:8000/api'


def generate_data():
    print('\nЗапуск генерации данных...')

    try:
        response = requests.post(
            f'{BASE_URL}/generate/',
            timeout=None
        )

        response.raise_for_status()

        data = response.json()

        print('\n' + data['message'])

    except requests.exceptions.RequestException as e:
        print(f'\nОшибка при обращении к серверу: {e}')

    except Exception as e:
        print(f'\nОшибка: {e}')


def show_counts():
    try:
        response = requests.get(
            f'{BASE_URL}/counts/',
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        print('\n--- Сгенерировано записей ---')

        for name, count in data['counts'].items():
            print(f'  {name:<22}: {count:>10}')

    except requests.exceptions.RequestException as e:
        print(f'\nОшибка при обращении к серверу: {e}')

def start_emulator():
    response = requests.post(f'{BASE_URL}/emulator/start/')
    print(response.json()['message'])


def stop_emulator():
    response = requests.post(f'{BASE_URL}/emulator/stop/')
    print(response.json()['message'])


def show_emulator_status():
    response = requests.get(f'{BASE_URL}/emulator/status/')
    data = response.json()

    print(
        'Эмулятор работает'
        if data['running']
        else 'Эмулятор остановлен'
    )


def main():
    while True:
        print('\n=== ГЛАВНОЕ МЕНЮ ===')
        print('1. Генерация данных')
        print('2. Просмотр количества записей')
        print('3. Запустить эмулятор')
        print('4. Остановить эмулятор')
        print('5. Состояние эмулятора')
        print('0. Выход')

        choice = input('Выберите действие: ')

        if choice == '1':
            generate_data()

        elif choice == '2':
            show_counts()

        elif choice == '3':
            start_emulator()

        elif choice == '4':
            stop_emulator()

        elif choice == '5':
            show_emulator_status()

        elif choice == '0':
            break

        else:
            print('Неверный пункт меню')


if __name__ == '__main__':
    main()