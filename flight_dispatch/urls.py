from django.urls import path
from .views import FlightDetailView, FlightUpdateView
from . import views

urlpatterns = [
    path('add/', views.create_flight, name='flight_create'),
    path('list/', views.flight_list, name='flight_list'),
    path('schedule/details/<slug:flight_number>/', FlightDetailView.as_view(), name='flight_details'),
    path('schedule/update/<int:pk>', FlightUpdateView.as_view(), name='flight_update'),
    # Flight Schedule
    path('api/flights/', views.get_flights, name='flight_calendar_api'),


]
