from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from movies.generator_server import generate_data

@require_POST
def generate_data_view(request):
    try:
        generate_data()

        return JsonResponse({
            'status': 'success',
            'message': 'Генерация данных успешно завершена.'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
