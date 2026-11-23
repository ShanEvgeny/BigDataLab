from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from movies.generator_server import generate_all
from django.views.decorators.csrf import csrf_exempt

from movies.models import Genre, Country, Director, Movie, Rating, Review
from django.contrib.auth.models import User

@csrf_exempt
@require_POST
def generate_data_view(request):
    try:
        generate_all()
        return JsonResponse({
            'status': 'success',
            'message': 'Генерация данных успешно завершена.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_GET
def show_counts_view(request):
    counts = {
        'Directors': Director.objects.count(),
        'Genres': Genre.objects.count(),
        'Countries': Country.objects.count(),
        'Movies': Movie.objects.count(),
        'Users': User.objects.count(),
        'Ratings': Rating.objects.count(),
        'Reviews': Review.objects.count(),
        'MovieDirectors': Movie.directors.through.objects.count(),
        'MovieGenres': Movie.genres.through.objects.count(),
        'MovieCountries': Movie.countries.through.objects.count(),
    }

    return JsonResponse({
        'status': 'success',
        'counts': counts
    })
