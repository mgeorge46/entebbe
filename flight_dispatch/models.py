from django.conf import settings
from django.utils.translation import gettext as _
from maintenance.models import Aircraft, Airport
from django.db import models
from django.utils import timezone

TRIP_TYPES = (
    ('', '---------'),
    ('one-way', 'One Way'),
    ('round-trip', 'Round Trip'),
    # ('multicity', 'Multi City'),
)
TECH_LOG_STATUS = (
    ('Pending', 'Pending'),
    ('Completed', 'Completed'),
)

TRIP_STATUS = (
    ('Dispatched', 'Dispatched'),
    ('Scheduled', 'Scheduled'),
    ('Cancelled', 'Cancelled'),
    ('not-taken', 'Not Taken'),
    ('Dispatching', 'Dispatching'),
    ('OnTrip', 'OnTrip'),
    ('Delayed', 'Delayed'),
    ('Arrived', 'Arrived'),
    ('Completed', 'Completed')
)

METHOD_STATUS = (
    ('', '---------'),
    ('Automated', 'Automated'),
    ('Manual', 'Manual')
)


class Flight(models.Model):
    flight_number = models.CharField(_('Flight Number'), max_length=50, unique=True)
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE)
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='final_destination')
    departure_time = models.DateTimeField(_('Departure Time'))
    arrival_time = models.DateTimeField(_('Arrival Time'))
    return_departure_time = models.DateTimeField(_('Return Departure Time'), null=True, blank=True)
    return_arrival_time = models.DateTimeField(_(' Return Arrival Time'), null=True, blank=True)
    cabin_crew = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='cabin_crew_schedule', blank=True,
                                        verbose_name='Cabin Crew')
    flight_crew = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='flight_crew_schedule', blank=True,
                                         verbose_name='Flight Crew')
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, verbose_name=_('Aircraft'))
    trip_type = models.CharField(_('Trip Type'), max_length=20, choices=TRIP_TYPES, default='one-way')
    flight_status = models.CharField(_('Flight Status'), max_length=30, choices=TRIP_STATUS, blank=False, null=False,
                                     default='Scheduled')
    flight_dispatch_method = models.CharField(_('Dispatch Method'), max_length=30, choices=METHOD_STATUS,
                                              default='Automated')
    flight_leg_reference = models.CharField(_('Flight Booking Reference'), max_length=100, blank=False, null=False)
    flight_comments = models.CharField(_('Flight Comments'), max_length=500, null=True, blank=True)
    update_comments = models.CharField(_('Update Comments'), max_length=500, null=True, blank=True)
    record_date = models.DateTimeField(_('Date Recorded'), default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Added By'))
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)
    tech_log = models.CharField(max_length=20, blank=False, null=False, default='Pending', choices=TECH_LOG_STATUS)

    def __str__(self):
        return '{} - {} on {}  to {} on {}'.format(
            self.flight_number,
            self.origin.name,
            self.departure_time.strftime('%Y-%m-%d %H:%M:%S'),
            self.destination.name,
            self.arrival_time.strftime('%Y-%m-%d %H:%M:%S'),
        )
