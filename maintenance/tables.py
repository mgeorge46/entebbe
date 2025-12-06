# tables.py
import django_tables2 as tables
from .models import Aircraft
from flight_dispatch.models import Flight
from django.utils.html import format_html
from django.urls import reverse
from .models import AircraftSubComponent, AircraftMainComponent, AircraftSub2Component, AircraftSub3Component, \
    AircraftMaintenanceTechLog, FlightTechLog
from django.contrib.contenttypes.models import ContentType


# from django_tables2.utils import A  # alias for Accessor


class AircraftTable(tables.Table):
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = Aircraft
        template_name = "django_tables2/bootstrap.html"
        fields = (
            'abbreviation', 'registration_number', 'aircraft_model', 'seating_capacity', 'aircraft_status')
        sequence = (
            'abbreviation', 'registration_number', 'aircraft_model', 'seating_capacity', 'aircraft_status')
        order_by = ('record_date',)
        attrs = {"class": "table"}

    def render_actions(self, record):
        return format_html(
            '<a href="{}"><i class="fa fa-eye fa-1x text-primary border-primary" title="View Details"aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-pencil-square-o fa-1x text-secondary border-secondary" title="Edit" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;',
            reverse('aircraft_detail', args=[record.registration_number]),
            reverse('aircraft_edit', args=[record.pk])
        )


class Sub3ComponentTable(tables.Table):
    component_name = tables.Column(verbose_name='Sub-Component')
    item_calender = tables.Column(verbose_name='Calender')
    item_cycle = tables.Column(verbose_name='Cycles')
    # parent_component__component_name = tables.Column(verbose_name='Main Component')
    # parent_component__aircraft_attached = tables.Column(verbose_name='Aircraft')
    maintenance_hours = tables.Column(verbose_name='Hours')
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = AircraftSub3Component
        fields = ('component_name', 'maintenance_hours',)
        attrs = {'class': 'table'}

    def render_actions(self, record):
        model_name = ContentType.objects.get_for_model(record).model
        return format_html(
            '<a href="{}"><i class="fa fa-eye fa-1x text-primary border-primary" title="View Details"aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-pencil-square-o fa-1x text-secondary border-secondary" title="Edit" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-clone" text-warning border-warning" title="Clone" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="#"><i class="fa fa-cog fa-1x text-danger border-danger" title="Maintenance" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;',
            reverse('aircraft_sub3_components_detail', args=[record.pk]),
            reverse('sub3_components_edit', args=[record.pk]),
            reverse('clone_component_generic', args=[model_name, record.pk]),
            reverse('add_aircraft_sub_component', args=[record.parent_sub2_component.pk])

        )

    def filter_queryset(self, qs):
        if self._only_show_subcomponents_of_main_component:
            qs = qs.filter(parent_sub2_component=self._only_show_subcomponents_of_main_component)
        return qs


class Sub2ComponentTable(tables.Table):
    component_name = tables.Column(verbose_name='Sub-Component')
    item_calender = tables.Column(verbose_name='Calender')
    item_cycle = tables.Column(verbose_name='Cycles')
    # parent_component__component_name = tables.Column(verbose_name='Main Component')
    # parent_component__aircraft_attached = tables.Column(verbose_name='Aircraft')
    maintenance_hours = tables.Column(verbose_name='Hours')
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = AircraftSub2Component
        fields = ('component_name', 'maintenance_hours',)
        attrs = {'class': 'table'}

    def render_actions(self, record):
        model_name = ContentType.objects.get_for_model(record).model
        return format_html(
            '<a href="{}"><i class="fa fa-eye fa-1x text-primary border-primary" title="View Details"aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-pencil-square-o fa-1x text-secondary border-secondary" title="Edit" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-plus-square fa-1x text-warning border-warning" title="Add" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-clone" text-warning border-warning" title="Clone" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="#"><i class="fa fa-cog fa-1x text-danger border-danger" title="Maintenance" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;',
            reverse('aircraft_sub3_components_list', args=[record.pk]),
            reverse('aircraft_sub2_components_update', args=[record.pk]),
            reverse('add_aircraft_sub_component', args=[record.parent_sub_component.pk]),
            reverse('clone_component_generic', args=[model_name, record.pk]),
            reverse('add_aircraft_sub_component', args=[record.parent_sub_component.pk])

        )

    def filter_queryset(self, qs):
        if self._only_show_subcomponents_of_main_component:
            qs = qs.filter(parent_sub_component=self._only_show_subcomponents_of_main_component)
        return qs


class SubComponentTable(tables.Table):
    component_name = tables.Column(verbose_name='Sub-Component')
    item_calender = tables.Column(verbose_name='Calender')
    item_cycle = tables.Column(verbose_name='Cycles')
    # parent_component__component_name = tables.Column(verbose_name='Main Component')
    # parent_component__aircraft_attached = tables.Column(verbose_name='Aircraft')
    maintenance_hours = tables.Column(verbose_name='Hours')
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = AircraftSubComponent
        fields = ('component_name', 'maintenance_hours',)
        attrs = {'class': 'table'}

    def render_actions(self, record):
        model_name = ContentType.objects.get_for_model(record).model
        return format_html(
            '<a href="{}"><i class="fa fa-eye fa-1x text-primary border-primary" title="View Details"aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-pencil-square-o fa-1x text-secondary border-secondary" title="Edit" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-plus-square fa-1x text-warning border-warning" title="Add" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-clone" text-warning border-warning" title="Clone" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="#"><i class="fa fa-cog fa-1x text-danger border-danger" title="Maintenance" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;',
            reverse('aircraft_sub2_components_list', args=[record.pk]),
            reverse('aircraft_sub_components_update', args=[record.pk]),
            reverse('add_aircraft_sub2_component', args=[record.pk]),
            reverse('clone_component_generic', args=[model_name, record.pk]),
            reverse('add_aircraft_sub_component', args=[record.parent_component.pk])

        )

    def filter_queryset(self, qs):
        if self._only_show_subcomponents_of_main_component:
            qs = qs.filter(parent_component=self._only_show_subcomponents_of_main_component)
        return qs


class MainComponentTable(tables.Table):
    component_name = tables.Column(verbose_name="Component Name")
    maintenance_hours = tables.Column(verbose_name="Maintenance Hours")
    install_date = tables.Column(verbose_name="Install Date")
    aircraft_attached = tables.Column(accessor='aircraft_attached.abbreviation', verbose_name="Aircraft")
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = AircraftMainComponent
        fields = ('component_name', 'maintenance_hours', 'aircraft_attached', 'install_date')
        attrs = {"class": "table"}

    def render_actions(self, record):
        model_name = ContentType.objects.get_for_model(record).model
        return format_html(
            '<a href="{}"><i class="fa fa-eye fa-1x text-primary border-primary" title="View Details"aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-pencil-square-o fa-1x text-secondary border-secondary" title="Edit" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-plus-square fa-1x text-warning border-warning" title="Add Sub-Component" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-clone" text-warning border-warning" title="Clone" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="#"><i class="fa fa-cog fa-1x text-danger border-danger" title="Maintenance" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;',
            reverse('aircraft_sub_components_list', args=[record.pk]),
            reverse('aircraft_main_components_update', args=[record.pk]),
            reverse('add_aircraft_sub_component', args=[record.pk]),
            reverse('clone_component_generic', args=[model_name, record.pk]),
        )


# Techlog tables:
class AircraftMaintenanceTechLogTable(tables.Table):
    aircraft = tables.Column(verbose_name="Aircraft")
    arrival_date = tables.Column(verbose_name="Maintenance Date")
    on_block = tables.Column(verbose_name="On Block")
    ac_type = tables.Column(verbose_name="AC Type")
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = AircraftMaintenanceTechLog
        fields = ('aircraft', 'arrival_date', 'on_block', 'ac_type')
        attrs = {"class": "table"}

    def render_actions(self, record):
        return format_html(
            '<a href="{}"><i class="fa fa-eye" title="View"></i></a>&nbsp;'
            '<a href="{}"><i class="fa fa-pencil-square-o" title="Edit"></i></a>&nbsp;'
            '<a href="#"><i class="fa fa-trash" title="Delete"></i></a>',
            reverse('maintenance_techlog_detail', args=[record.pk]),
            reverse('update_aircraft_maintenance_techlog', args=[record.pk]),
            # reverse('aircraft_maintenance_delete', args=[record.pk])
        )


class FlightTechLogTable(tables.Table):
    flight_leg = tables.Column(verbose_name="Flight Leg")
    aircraft = tables.Column(verbose_name="Aircraft")
    departure_airport = tables.Column(verbose_name="Take Off")
    departure_date = tables.Column(verbose_name="Landing")
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = FlightTechLog
        fields = ('flight_leg', 'aircraft', 'departure_airport', 'departure_date')
        attrs = {"class": "table"}

    def render_actions(self, record):
        return format_html(
            '<a href="#"><i class="fa fa-eye" title="View"></i></a>&nbsp;'
            '<a href="#"><i class="fa fa-pencil-square-o" title="Edit"></i></a>&nbsp;'
            '<a href="#"><i class="fa fa-trash" title="Delete"></i></a>',
            # reverse('flight_techlog_view', args=[record.pk]),
            # reverse('flight_techlog_edit', args=[record.pk]),
            # reverse('flight_techlog_delete', args=[record.pk])
        )

class FlightTablePendingTechlog(tables.Table):
    flight_number = tables.Column(verbose_name="Flight Number")
    origin = tables.Column(verbose_name="Origin")
    departure_time = tables.Column(verbose_name="Departure Time")
    flight_booking_reference = tables.Column(verbose_name="Flight Reference")
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = Flight
        fields = ('flight_number', 'origin', 'departure_time', 'flight_booking_reference')
        attrs = {"class": "table"}
    def render_actions(self, record):
        return format_html(
            '<a href="{}"><i class="fa fa-eye" title="View"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-pencil-square-o" title="Edit"></i></a>&nbsp&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-check" title="Complete" aria-hidden="true"></i></a>',
            reverse('flight_details', args=[record.flight_number]),
            reverse('flight_update', args=[record.pk]),
            reverse('create_flighttechlog', args=[record.aircraft.registration_number])
        )

