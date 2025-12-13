from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone as dj_timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

COMPONENT_STATUS = (('Attached', 'Attached'), ('Detached', 'Detached'), ('Stores', 'Stores'))
MAINTENANCE_TYPE = (('Class_A', 'Class A'), ('Class_B', 'Class B'), ('Class_C', 'Class C'), ('Class_D', 'Class D'))
MAINTENANCE_STATUS = (
    ('Operational', 'Operational'), ('Maintenance', 'Maintenance'), ('Re-Provisioned', 'Re-Provisioned'),)


class Airport(models.Model):
    name = models.CharField(_('Airport Name'), max_length=100)
    icao = models.CharField(_('ICAO Code'), max_length=50)
    iata = models.CharField(_('IATA Code'), max_length=50, unique=True)
    country_name = models.CharField(_('Country Name'), max_length=100)
    country_iso_alpha3 = models.CharField(_('Country ISO Alpha 3 Code'), max_length=3)
    country_iso_alpha2 = models.CharField(_('Country ISO Alpha 2 Code'), max_length=2)
    city_name = models.CharField(_('City Name'), max_length=100)
    latitude = models.DecimalField(_('Latitude'), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_('Longitude'), max_digits=9, decimal_places=6)
    elevation = models.DecimalField(_('Elevation'), max_digits=7, decimal_places=2, null=True, blank=True)
    timezone = models.CharField(_('Timezone'), max_length=100)
    time_shift = models.CharField(_('Time Shift'), max_length=100)
    sunset = models.TimeField(_('Sunset'), blank=True, null=True)
    sunrise = models.TimeField(_('Sunrise'), blank=True, null=True)
    runways = models.JSONField(_("Runways"), default=list)
    pcn = models.CharField(_('PCN'), max_length=50)
    lid = models.CharField(_('Local ID'), max_length=50, null=True, blank=True)
    email = models.EmailField(_('Email'), null=True, blank=True)
    tower_hours = models.CharField(_('Tower Hours'), max_length=100)
    phone = models.CharField(_('Phone'), max_length=50, null=True, blank=True)
    fax = models.CharField(_('Fax'), max_length=50, null=True, blank=True)
    website = models.URLField(_('Website'), null=True, blank=True)
    slug = models.SlugField()
    # Fields for internal record-keeping
    record_date = models.DateTimeField(_('Date Recorded'), default=dj_timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1, verbose_name="Added By")
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    update_comments = models.CharField(_('Update Comments'), max_length=500, null=True, blank=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.name, self.iata, self.timezone)


class ComponentValidationMixin:
    def clean(self):
        model_class = self.__class__
        existing_record_with_name = model_class.objects.filter(
            component_name=self.component_name, component_status='Attached'
        ).exclude(pk=self.pk).exists()
        existing_record_with_part_number = model_class.objects.filter(
            part_number=self.part_number, component_status='Attached'
        ).exclude(pk=self.pk).exists()

        if existing_record_with_name or existing_record_with_part_number:
            raise ValidationError(
                "A record with the same component name or part number and status 'Attached' already exists.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Aircraft(models.Model):
    CRAFT_STATUS = (('Operational', 'Operational'), ('Maintenance', 'Maintenance'))
    abbreviation = models.CharField(_('Abbreviation'), max_length=20, unique=True)
    registration_number = models.CharField(_('Reg. No.r'), max_length=20, unique=True)
    aircraft_callsign = models.CharField(_('CallSign'), max_length=10)
    aircraft_model = models.CharField(_('Model'), max_length=100)
    aircraft_type = models.CharField(max_length=100)
    aircraft_variable = models.CharField(_('Variable'), max_length=10)
    aircraft_serial = models.CharField(_('Serial'), max_length=100)
    manufacturer = models.CharField(max_length=100)
    year_of_man = models.PositiveIntegerField(_('Year of Manufacture'), blank=False)
    seating_capacity = models.PositiveIntegerField()
    cabin_crew_capacity = models.PositiveIntegerField()
    flight_crew_capacity = models.PositiveIntegerField()
    takeoff_weight = models.DecimalField(_('Maximum Take Off Weight (MTOW)'), max_digits=10, decimal_places=2)
    taxi_weight = models.DecimalField(_('Maximum Taxi Weight (MTW)'), max_digits=10, decimal_places=2)
    landing_weight = models.DecimalField(_('Maximum Landing Weight (MLW)'), max_digits=10, decimal_places=2)
    zerofuel_weight = models.DecimalField(_('Maximum Zerofuel Weight (MZFW)'), max_digits=10, decimal_places=2)
    empty_weight = models.DecimalField(_('Operating Empty Weight (OEW)'), max_digits=10, decimal_places=2)
    max_available_Payload = models.DecimalField(_('Maximum Payload'), max_digits=10, decimal_places=2)
    aircraft_components_number = models.PositiveIntegerField(_('Number of Components'), blank=False, null=False)
    aircraft_status = models.CharField(_('Status'), max_length=100, choices=CRAFT_STATUS)
    maximum_main_components = models.DecimalField(_('Maximum Main Components'), max_digits=10, decimal_places=2, blank=True, null=True)
    maximum_sub_components = models.DecimalField(_('Maximum Sub Components'), max_digits=10, decimal_places=2, blank=True, null=True)
    a_hours = models.DecimalField(_('A Maintenance Hours'), max_digits=10, decimal_places=2, default=0, blank=True,
                                  null=True)
    b_hours = models.DecimalField(_('B Maintenance Hours'), max_digits=10, decimal_places=2, default=0, blank=True,
                                  null=True)
    c_hours = models.DecimalField(_('C Maintenance Hours'), max_digits=10, decimal_places=2, default=0, blank=True,
                                  null=True)
    d_hours = models.DecimalField(_('D Maintenance Hours'), max_digits=10, decimal_places=2, default=0, blank=True,
                                  null=True)
    a_check_hours_alert = models.DecimalField(_('A Check Alert Hours'), max_digits=10, decimal_places=2, null=True,
                                              blank=True)
    b_check_hours_alert = models.DecimalField(_('B Check alert Hours'), max_digits=10, decimal_places=2, null=True,
                                              blank=True)
    c_check_hours_alert = models.DecimalField(_('C Check alert Hours'), max_digits=10, decimal_places=2, null=True,
                                              blank=True)
    d_check_hours_alert = models.DecimalField(_('D Check alert Hours'), max_digits=10, decimal_places=2, null=True,
                                              blank=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    update_comments = models.CharField(_('Update Comments'), max_length=500, null=True, blank=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    def __str__(self):
        return self.abbreviation


class AircraftMaintenance(models.Model):
    main_type_schedule = models.CharField(_('Maintenance Type'), max_length=100, choices=MAINTENANCE_STATUS)
    aircraft_to_maintain = models.ForeignKey(Aircraft, on_delete=models.CASCADE, max_length=100)
    maintenance_type = models.CharField(_('Maintenance Type'), max_length=100, choices=MAINTENANCE_TYPE)
    maintenance_hours = models.DecimalField(_('Maintenance Hours'), max_digits=10, decimal_places=2, default=0,
                                            blank=False, null=False)
    maintenance_hours_added = models.DecimalField(_('Maintenance Hours Added'), max_digits=10, decimal_places=2,
                                                  default=0, blank=False, null=False)
    start_date = models.DateTimeField(_('Start Date'), blank=False, null=False)
    end_date = models.DateTimeField(_('End Date'), blank=False, null=False)
    next_maintenance_date = models.DateTimeField(_('Recommended Next Date'), blank=True, null=True)
    remarks = models.TextField(_('Maintenance Remarks'), blank=False, null=False, max_length=500, )
    maintenance_report = models.FileField(_('Maintenance Report'), blank=False, null=False)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    update_comments = models.CharField(_('Update Comments'), max_length=500, null=True, blank=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)


# Abstract base class for all components
class Component(ComponentValidationMixin, models.Model):
    component_name = models.CharField(_('Component Name'), max_length=50)
    maintenance_hours = models.DecimalField(_('Maintenance Hours'), max_digits=20, decimal_places=2, default=0,
                                            blank=False, null=False)
    component_make = models.CharField(_('Make (Ven Code))'), max_length=50)
    component_model = models.CharField(_('Component Model'), max_length=50)
    part_number = models.CharField(_('Part Number'), max_length=50, blank=False, null=False, default=' part number')
    serial_number = models.CharField(_('Serial Number'), max_length=50, null=False, blank=False, unique=True)
    description = models.CharField(_('Description'), max_length=50, blank=False, null=False, default=' component description ')
    lru = models.CharField(_('LRU'), max_length=50, blank=True)
    qec = models.CharField(_('OPT'), max_length=50, blank=True)
    item_owner = models.CharField(_('Owner'), max_length=50, blank=True)
    tsn = models.CharField(_('TSN'), max_length=50, blank=True, null=True)
    csn = models.CharField(_('CSN'), max_length=50, blank=True, null=True)
    ata = models.CharField(_('ATA'), max_length=50, blank=True, null=True)
    dom = models.CharField(_('DOM'), max_length=50, blank=True, null=True)
    install_date = models.DateField(_('Date Installed'), blank=False, null=False, default=timezone.now)
    delivery_date = models.DateField(_('Delivery Date'), blank=False, null=False, default=timezone.now)
    tsi = models.CharField(_('TSI'), max_length=50, blank=True, null=True)
    csi = models.CharField(_('CSI'), max_length=50, blank=True, null=True)
    qpa = models.CharField(_('QPA (Quantity)'), max_length=50, blank=True, null=True)
    component_location = models.CharField(_('Zone/Location'), max_length=250, blank=True, null=True)
    remarks = models.TextField(_('Task required after specified interval'), blank=True, null=True)
    maintenance_cycles = models.PositiveIntegerField(_('maintenance_cycles'), blank=True, null=True, default=0)
    item_calender = models.DateTimeField(_('Component Calendar'), blank=True, null=True)
    item_calender_months = models.PositiveIntegerField(_('Component Calendar in Months'), blank=True, null=True)
    item_cycle = models.PositiveIntegerField(_('Cycles'), blank=True, null=True, default=0)
    item_original_hours = models.DecimalField(_('Original Hours'), max_digits=20, decimal_places=2,
                                              blank=False, null=False)
    max_item_cycle = models.PositiveIntegerField(_('Max. Cycles'), blank=True, null=True)
    min_maintenance_hours = models.DecimalField(_('Min. Maintenance Hours'), max_digits=20, decimal_places=2,
                                                blank=True, null=True)
    maintenance_status = models.CharField(_('Maintenance Status'), max_length=100, choices=MAINTENANCE_STATUS,
                                          default='Attached')
    component_status = models.CharField(_('Component Status'), max_length=100, choices=COMPONENT_STATUS,
                                        default='Attached')
    date_detached = models.DateTimeField(_('Date Detached'), blank=True, null=True)
    date_re_provisioned = models.DateTimeField(_('Date Re-Provisioned'), blank=True, null=True)
    date_attached = models.DateTimeField(_('Date Attached'), blank=True, null=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    update_comments = models.CharField(_('Update Comments'), max_length=500, null=True, blank=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)
    next_maintenance_date = models.DateTimeField(_('Recommended Next Date'), blank=True, null=True)

    # Add reverse relation for maintenance records
    maintenance_records = GenericRelation('ComponentMaintenance', related_query_name='component')

    class Meta:
        abstract = True

    def __str__(self):
        return '{}-{}-{}-{}'.format(
            self.component_name,
            self.serial_number,
            self.part_number,
            self.component_status,
        )

    def save(self, *args, **kwargs):
        if not self.pk:  # checks if object is new and doesn't have a primary key yet
            self.item_original_hours = self.maintenance_hours
        super(Component, self).save(*args, **kwargs)


# Concrete classes for different component types
class AircraftMainComponent(Component):
    aircraft_attached = models.ForeignKey(Aircraft, on_delete=models.CASCADE, verbose_name='Aircraft Main Components')

    class Meta:
        verbose_name = _('Aircraft Main Component')
        verbose_name_plural = _('Aircraft Main Components')


class AircraftSubComponent(Component):
    parent_component = models.ForeignKey(AircraftMainComponent, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Aircraft Sub Component')
        verbose_name_plural = _('Aircraft Sub Components')


class AircraftSub2Component(Component):
    parent_sub_component = models.ForeignKey(AircraftSubComponent, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Aircraft Sub2 Component')
        verbose_name_plural = _('Aircraft Sub2 Components')


class AircraftSub3Component(Component):
    parent_sub2_component = models.ForeignKey(AircraftSub2Component, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Aircraft Sub3 Component')
        verbose_name_plural = _('Aircraft Sub3 Components')


class ComponentMaintenance(models.Model):
    main_type_schedule = models.CharField(_('Maintenance Type'), max_length=100, choices=MAINTENANCE_STATUS)
    
    # Generic relation to any component type
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    component_to_maintain = GenericForeignKey('content_type', 'object_id')
    
    maintenance_type = models.CharField(_('Maintenance Type'), max_length=100, choices=MAINTENANCE_TYPE)
    maintenance_hours = models.DecimalField(_('Maintenance Hours'), max_digits=10, decimal_places=2, default=0,
                                            blank=False, null=False)
    maintenance_hours_added = models.DecimalField(_('Maintenance Hours Added'), max_digits=10, decimal_places=2,
                                                  default=0, blank=False, null=False)
    start_date = models.DateTimeField(_('Start Date'), blank=False, null=False)
    end_date = models.DateTimeField(_('End Date'), blank=False, null=False)
    remarks = models.TextField(_('Maintenance Remarks'), blank=False, null=False, max_length=500)
    maintenance_report = models.FileField(_('Maintenance Report'), blank=False, null=False)
    # two state workflow for maintenance record
    maintenance_status = models.CharField(
        _('Maintenance Status'),
        max_length=20,
        choices=[
            ('Scheduled', 'Scheduled'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled'),
        ],
        default='Scheduled'
    )
    
    actual_start_date = models.DateTimeField(_('Actual Start Date'), blank=True, null=True)
    actual_end_date = models.DateTimeField(_('Actual End Date'), blank=True, null=True)
    actual_hours_added = models.DecimalField(_('Actual Hours Added'), max_digits=10, decimal_places=2, default=0)
    
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='completed_maintenances',
        blank=True,
        null=True
    )
    
    completion_date = models.DateTimeField(_('Completion Date'), blank=True, null=True)
    completion_remarks = models.TextField(_('Completion Remarks'), blank=True, null=True)
    completion_report = models.FileField(_('Completion Report'), blank=True, null=True)


    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    update_comments = models.CharField(_('Update Comments'), max_length=500, null=True, blank=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    class Meta:
        verbose_name = _('Component Maintenance')
        verbose_name_plural = _('Component Maintenances')
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['start_date']),
        ]

    def __str__(self):
        return f'{self.component_to_maintain} - {self.maintenance_type} ({self.start_date.date()})'

    # Helper properties to identify component type
    @property
    def component_type_name(self):
        """Returns human-readable component type name"""
        model_name = self.content_type.model
        type_map = {
            'aircraftmaincomponent': 'Main Component',
            'aircraftsubcomponent': 'Sub Component',
            'aircraftsub2component': 'Sub2 Component',
            'aircraftsub3component': 'Sub3 Component',
        }
        return type_map.get(model_name, 'Unknown Component')

    @property
    def component_level(self):
        """Returns the component hierarchy level with description"""
        model_name = self.content_type.model
        level_map = {
            'aircraftmaincomponent': 'Level 0 - Main Component',
            'aircraftsubcomponent': 'Level 1 - Sub Component',
            'aircraftsub2component': 'Level 2 - Sub Component',
            'aircraftsub3component': 'Level 3 - Sub Component',
        }
        return level_map.get(model_name, 'Unknown Level')

    @property
    def is_main_component(self):
        """Check if maintenance is for a main component"""
        return self.content_type.model == 'aircraftmaincomponent'

    @property
    def is_sub_component(self):
        """Check if maintenance is for a sub component (level 1)"""
        return self.content_type.model == 'aircraftsubcomponent'

    @property
    def is_sub2_component(self):
        """Check if maintenance is for a sub2 component (level 2)"""
        return self.content_type.model == 'aircraftsub2component'

    @property
    def is_sub3_component(self):
        """Check if maintenance is for a sub3 component (level 3)"""
        return self.content_type.model == 'aircraftsub3component'

    @property
    def component_hierarchy_level(self):
        """Returns numeric hierarchy level (0-3)"""
        model_name = self.content_type.model
        level_map = {
            'aircraftmaincomponent': 0,
            'aircraftsubcomponent': 1,
            'aircraftsub2component': 2,
            'aircraftsub3component': 3,
        }
        return level_map.get(model_name, -1)

    def get_component_model_class(self):
        """Returns the actual model class of the component"""
        return self.content_type.model_class()

    def get_component_details(self):
        """Returns a dictionary with component type information"""
        return {
            'type_name': self.component_type_name,
            'level': self.component_hierarchy_level,
            'level_description': self.component_level,
            'model_name': self.content_type.model,
            'is_main': self.is_main_component,
            'is_sub': self.is_sub_component,
            'is_sub2': self.is_sub2_component,
            'is_sub3': self.is_sub3_component,
        }
class CommonTechLogInfo(models.Model):
    aircraft = models.ForeignKey('Aircraft', on_delete=models.CASCADE, verbose_name="Aircraft", blank=True, null=True)
    off_block = models.CharField(_('Off Block'), max_length=50, blank=True)
    flight_log_number = models.PositiveIntegerField(_('Flight Log'), blank=True, null=True)
    on_block = models.CharField(_('On Block'), max_length=50, blank=True, null=True)
    oper = models.CharField(_('Oper'), max_length=50, blank=True, null=True)
    ac_type = models.CharField(_('AC Type'), max_length=50, blank=True, null=True)
    serve_type = models.CharField(_('Serve Type'), max_length=50, blank=True, null=True)
    per_day = models.PositiveIntegerField(_('Per Day'), blank=True, null=True)
    air_time = models.CharField(_('Air Time'), max_length=50, blank=True, null=True)
    cycles = models.CharField(_('Cycles'), max_length=50, blank=True, null=True)
    tsn = models.CharField(_('TSN'), max_length=50, blank=True, null=True)
    csn = models.CharField(_('CSN'), max_length=50, blank=True, null=True)
    flight_tech_log_comments = models.CharField(_('Tech log Comments'), max_length=500, blank=True)
    flight_time = models.CharField(_('Flight Time'), max_length=50, blank=True, null=True)
    land = models.CharField(_('Land'), max_length=50, blank=True)
    night_vfr = models.CharField(_('Night/VFR'), max_length=50, blank=True)
    uplift_dest = models.CharField(_('Uplift Dest'), max_length=50, blank=True, null=True)
    remarks = models.TextField(_('Remarks'), max_length=50, blank=True, null=True)
    files = models.FileField(_('Supporting Attachments'), blank=True, null=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    update_comments = models.CharField(_('Update Comments'), max_length=500, null=True, blank=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True, null=True)
    techlog_report = models.FileField(_('Tech log Report'), blank=True, null=True)
    arrival_date = models.DateTimeField(_('Arrival Date'), blank=True, null=True)

    class Meta:
        abstract = True


class AircraftMaintenanceTechLog(CommonTechLogInfo):
    departure_airport = models.CharField(_('Departure Airport'), max_length=50, blank=True)
    arrival_airport = models.CharField(_('Arrival Airport'), max_length=50, blank=True)


class FlightTechLog(CommonTechLogInfo):
    flight_leg = models.ForeignKey('flight_dispatch.Flight', on_delete=models.CASCADE, verbose_name="Leg")
    takeoff = models.DateTimeField(_('Take Off'), blank=False, null=False, default=timezone.now)
    landing = models.DateTimeField(_('Landing '), blank=False, null=False, default=timezone.now)
    departure_airport = models.CharField(_('Departure Airport'), max_length=50, blank=True)
    arrival_airport = models.CharField(_('Arrival Airport'), max_length=50, blank=True)
