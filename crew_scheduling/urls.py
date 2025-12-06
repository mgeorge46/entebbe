# myapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('scheduling/', views.crew_scheduling, name='manage_crew_scheduling'),
]
