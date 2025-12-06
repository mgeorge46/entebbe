from django.urls import path
from .views import PassengerListView,PassengerDetailView,PassengerUpdateView, BookingUpdateView, BookingListView,\
    BookingDetailView, PassengerGroupUpdateView, PassengerGroupDetailView,GroupListView

from . import views

urlpatterns = [
    path('add', views.add_passenger_booking, name='passenger_create'),
    path('list', PassengerListView.as_view(), name='passenger_list'),
    path('details/<int:pk>', PassengerDetailView.as_view(), name='passenger_details'),
    path('update/<int:pk>', PassengerUpdateView.as_view(), name='passenger_update'),
    # booking urls
    path('bookings/list', BookingListView.as_view(), name='booking_list'),
    path('bookings/add/', views.add_booking, name='add_booking'),
    path('booking/details/<int:pk>', BookingDetailView.as_view(), name='booking_details'),
    path('booking/update/<int:pk>', BookingUpdateView.as_view(), name='booking_update'),
    # group urls
    path('groups/list', GroupListView.as_view(), name='group_list'),
    path('groups/add', views.create_group, name='create_group'),
    path('groups/update/<int:pk>', PassengerGroupUpdateView.as_view(), name='group_update'),
    path('groups/details/<int:pk>', PassengerGroupDetailView.as_view(), name='group_details'),


]
