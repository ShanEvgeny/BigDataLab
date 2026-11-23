from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_data_view, name='generate_data'),
]