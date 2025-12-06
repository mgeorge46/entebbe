from django.shortcuts import render
from django.core.serializers import serialize

import flight_dispatch.urls
from .models import Flight

def flight_calendar(request):
    flights = Flight.objects.all()
    flight_data = serialize('json', flights)
    context = {
        'flight_data': flight_data,
    }
    return render(request, 'flight_dispatch/flight_calendar.html', context)
