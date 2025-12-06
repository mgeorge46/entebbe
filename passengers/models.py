from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from flight_dispatch.models import Flight

TRIP_TYPES = (('one-way', 'One Way'), ('round-trip', 'Round Trip'),)
GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'),)
STATUS_CHOICES = (('Active', 'Active'), ('Deactivated', 'Deactivated'),)
BOOKING_STATUS = (('', '---------'), ('Active', 'Active'), ('Cancelled', 'Cancelled'), ('Missed', 'Missed'),)


class Passenger(models.Model):
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=255)
    national_id = models.CharField(max_length=255, unique=True)
    passport_number = models.CharField(max_length=255, unique=True)
    passport_issuing_country = models.CharField(max_length=255)
    passport_expiration_date = models.DateField()
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    passenger_comments_update = models.CharField(_('Comments for Updating'), max_length=500, blank=True, null=True)
    immigration_details = models.CharField(max_length=255, blank=True, null=True)
    special_requirements = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True, null=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    def __str__(self):
        return self.full_name


class PassengerBooking(models.Model):
    flight_number = models.ForeignKey(Flight, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    passenger_id = models.ForeignKey(Passenger, on_delete=models.CASCADE, verbose_name=_('Passenger'))
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPES)
    return_flight = models.ForeignKey(Flight, on_delete=models.CASCADE, blank=True, null=True,
                                      related_name='return_flight', )
    multi_city_flights = models.ManyToManyField(Flight, related_name='multicity_flight', verbose_name=_('Multi City '
                                                                                                        'Flights'))
    allowed_weight = models.DecimalField(_('Allowed Maximum Weight'), max_digits=10, decimal_places=2, blank=True, null=True)
    max_check_bags = models.PositiveIntegerField(_('Allowed Maximum Pieces'), blank=True, null=True)
    checked_in_weight = models.DecimalField(_('Checked in Weight'), max_digits=10, decimal_places=2, blank=True, null=True)
    checked_in_bags = models.PositiveIntegerField(_('Number of Bags Checked in'), blank=True, null=True)
    booking_comments = models.TextField(_('Booking Comments'), blank=True, null=True)
    booking_ticket_id = models.CharField(_('Ticket ID'), max_length=100, blank=False, null=False,
                                         unique=False)
    booking_reference = models.CharField(_('Booking Reference'), max_length=100, blank=False, null=False)
    update_comments = models.CharField(_('Update Comments'), max_length=500, blank=True, null=True)
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='Active')
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    def __str__(self):
        return f'{self.flight_number.flight_number}-{self.passenger_id}'


class PassengerGroup(models.Model):
    group_name = models.CharField(_('Group Name'), max_length=120, blank=False, null=False, unique=True)
    group_status = models.CharField(_('Group Status'), max_length=20, choices=STATUS_CHOICES, default='Active')
    passengers_ids = models.ManyToManyField(Passenger, blank=True, verbose_name=_('Passengers'))
    group_updating_comments = models.TextField(_('Comments'), blank=True, null=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    def __str__(self):
        return self.group_name
