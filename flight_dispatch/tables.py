import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html
from .models import Flight


class FlightTable(tables.Table):
    flight_number = tables.Column(verbose_name="Flight Number")
    origin = tables.Column(verbose_name="Origin")
    destination = tables.Column(verbose_name="Destination")
    departure_time = tables.Column(verbose_name="Departure")
    flight_status = tables.Column(verbose_name="Status")
    actions = tables.Column(empty_values=[], orderable=False, verbose_name="Actions")

    class Meta:
        model = Flight
        template_name = "django_tables2/bootstrap.html"
        fields = ('flight_number', 'origin', 'destination', 'departure_time', 'flight_status', 'actions')
        sequence = ('flight_number', 'origin', 'destination', 'departure_time', 'flight_status', 'actions')
        order_by = ('departure_time',)

    def render_actions(self, record):
        return format_html(
            '<a href="{}"><i class="fa fa-eye fa-1x text-primary border-primary" title="View Details"aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="{}"><i class="fa fa-pencil-square-o fa-1x text-secondary border-secondary" title="Edit" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;'
            '<a href="#"><i class="fa fa-cog fa-1x text-danger border-danger" title="Maintenance" aria-hidden="true"></i></a>&nbsp;&nbsp;&nbsp;',
            reverse('flight_details', args=[record.flight_number]),
            reverse('flight_update', args=[record.pk])
        )
