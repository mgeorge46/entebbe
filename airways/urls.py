from django.urls import path
from . import views

urlpatterns = [
    path('whiteboard/', views.ops_board, name='flight_calendar'),
    path('dashboard/',views.eaw_home, name='ops_dash'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('api/events/', views.events_api, name='events_api'),

]
