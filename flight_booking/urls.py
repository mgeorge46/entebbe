from django.urls import path
from . import views

urlpatterns = [
    path('estimate/', views.submit_booking_form, name='booking_planning'),
    # Include other URL patterns if any
    path('estimates/', views.booking_success, name='booking_success'),
]
