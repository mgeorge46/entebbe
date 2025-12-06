from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

TRIP_TYPES = (('one-way', 'One Way'), ('round-trip', 'Round Trip'),)
GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'),)
STATUS_CHOICES = (('Active', 'Active'), ('Deactivated', 'Deactivated'),)
BOOKING_STATUS = (('', '---------'), ('Active', 'Active'), ('Cancelled', 'Cancelled'), ('Missed', 'Missed'),)


class CabinCrewGroup(models.Model):
    group_name = models.CharField(_('Group Name'), max_length=120, blank=False, null=False, unique=True)
    group_status = models.CharField(_('Group Status'), max_length=20, choices=STATUS_CHOICES, default='Active')
    crew_ids = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name=_('Passengers'))
    group_updating_comments = models.TextField(_('Comments'), blank=True, null=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='added_by_cabin_crew_group', )
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    def __str__(self):
        return self.group_name


