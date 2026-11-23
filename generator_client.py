import requests


BASE_URL = 'http://127.0.0.1:8000/api/'


def generate_data():
    try:
        response = requests.post(
            BASE_URL + 'generate/',
            timeout=None
        )

        response.raise_for_status()

        data = response.json()

        print(data['message'])

    except requests.exceptions.RequestException as e:
        print(f'Ошибка запроса: {e}')

    except ValueError:
        print('Сервер вернул некорректный JSON.')


def main():
    while True:
        print('\n===== КОНСОЛЬНЫЙ КЛИЕНТ =====')
        print('1. Генерация данных')
        print('0. Выход')

        choice = input('Выберите действие: ')

        if choice == '1':
            generate_data()

        elif choice == '0':
            print('Завершение работы клиента.')
            break