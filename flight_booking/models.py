from django.db import models
from maintenance.models import Aircraft, Airport
from django.utils.translation import gettext as _
from django.conf import settings
from django.utils import timezone

TRIP_TYPES = (
    ('', '---------'),
    ('one-way', 'One Way'),
    ('round-trip', 'Round Trip'),
    ('multicity', 'Multi City'),
)

TRIP_STATUS = (
    ('', '----------------'),
    ('requested', 'Requested'),
    ('rejected', 'EAW Rejected'),
    ('cancelled', 'Customer Cancelled'),
    ('confirmed', 'Confirmed')

)
class FlightBooking(models.Model):
    flight_booking_number = models.CharField(_('Flight Number'), max_length=50, unique=True, primary_key=True)
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='booking_origin')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='booking_final_destination')
    departure_time = models.DateTimeField(_('Departure Time'))
    arrival_time = models.DateTimeField(_('Arrival Time'), null=True, blank=True)
    return_departure_time = models.DateTimeField(_('Return Departure Time'), null=True, blank=True)
    return_arrival_time = models.DateTimeField(_(' Return Arrival Time'), null=True, blank=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, verbose_name=_('Aircraft'))
    trip_type = models.CharField(_('Trip Type'), max_length=20, choices=TRIP_TYPES, default='one-way')
    flight_tracking_id = models.CharField(_('Flight Booking Reference'), max_length=100, blank=False, null=False)
    flight_booking_status = models.CharField(_('Booking Status'), choices=TRIP_STATUS)
    booking_pax = models.PositiveSmallIntegerField(_('Booking Pax'))
    airway_distance = models.FloatField(null=True, blank=True)
    airway_distance_true = models.CharField(_('Airway Distance'), max_length=1000, null=True, blank=True)
    fuel = models.JSONField()
    time = models.JSONField()
    route = models.JSONField(_('Route'), default=list)
    update_comments = models.CharField(_('Update Comments'), max_length=500, null=True, blank=True)
    record_date = models.DateTimeField(_('Date Recorded'), default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Added By'))
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)
    validity_date = models.DateTimeField('Date Valid', null=True, blank=True, default=timezone.now)

    def __str__(self):
        return '{} - {} on {}  to {} on {}'.format(
            self.flight_booking_number,
            self.origin.name,
            self.departure_time.strftime('%Y-%m-%d %H:%M:%S'),
            self.destination.name,
            self.arrival_time.strftime('%Y-%m-%d %H:%M:%S'),
        )