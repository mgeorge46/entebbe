from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render
from django_tables2 import RequestConfig
from flight_dispatch.models import Flight
from .tables import FlightsWithCrewTable, FlightsWithoutCrewTable

@login_required
def crew_scheduling(request):
    current_time = timezone.now()

    # Query for flights with both cabin and flight crew whose arrival_time is in the future
    queryset_with_crew = Flight.objects.exclude(cabin_crew=None).exclude(flight_crew=None).filter(arrival_time__gte=current_time)
    table_with_crew = FlightsWithCrewTable(queryset_with_crew)
    RequestConfig(request).configure(table_with_crew)

    # Query for flights without both cabin and flight crew whose arrival_time is in the future
    queryset_without_crew = (Flight.objects.filter(cabin_crew=None) | Flight.objects.filter(flight_crew=None)).filter(arrival_time__gte=current_time)
    table_without_crew = FlightsWithoutCrewTable(queryset_without_crew)
    RequestConfig(request).configure(table_without_crew)

    return render(request, 'crew_scheduling/crew_scheduling.html', {
        'table_with_crew': table_with_crew,
        'table_without_crew': table_without_crew
    })

