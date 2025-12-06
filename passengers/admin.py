from django.contrib import admin

# Register your models here.
from .models import Passenger,PassengerBooking,PassengerGroup
admin.site.register(Passenger)
admin.site.register(PassengerGroup)
admin.site.register(PassengerBooking)

