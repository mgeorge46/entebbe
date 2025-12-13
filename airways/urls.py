from django.urls import path
from . import views, whiteboard_views

urlpatterns = [
    path('dashboard/',views.eaw_home, name='ops_dash'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('api/events/', views.events_api, name='events_api'),
    # Whiteboard Calendar
    path('whiteboard/', whiteboard_views.whiteboard_calendar_view, name='whiteboard_calendar'),
    path('whiteboard/data/', whiteboard_views.whiteboard_calendar_data, name='whiteboard_calendar_data'),
    path('whiteboard/flight/<int:flight_id>/', whiteboard_views.get_flight_details, name='whiteboard_flight_details'),
    path('whiteboard/component/<str:component_type>/<int:component_id>/', whiteboard_views.get_component_details, name='whiteboard_component_details'),
    path('whiteboard/schedule-maintenance/', whiteboard_views.quick_schedule_maintenance, name='quick_schedule_maintenance'),
    path('whiteboard/stats/', whiteboard_views.whiteboard_stats, name='whiteboard_stats'),

]



