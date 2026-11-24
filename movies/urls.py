from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_data_view, name='generate_data'),
    path('counts/', views.show_counts_view, name='show_counts'),
    path('emulator/start/', views.start_emulator_view),
    path('emulator/stop/', views.stop_emulator_view),
    path('emulator/status/', views.emulator_status_view),
]