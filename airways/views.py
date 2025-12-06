from django.contrib.auth.decorators import login_required
from django.shortcuts import render
# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import Event
from flight_dispatch.models import Flight


@login_required
def eaw_home(request):
    return render(request, 'pages/ops_dash.html', {'title': 'Entebbe Airways'})
@login_required
def whiteboard(request):
    return render(request, 'pages/white_board.html', {'title': 'Flight Schedule'})


def calendar_view(request):
    return render(request, 'pages/calendar.html')


# noinspection PyInterpreter
def events_api(request):
    events = Event.objects.all()
    data = [{'title': e.title, 'start': e.start_time, 'end': e.end_time} for e in events]
    return JsonResponse(data, safe=False)


@login_required
def ops_board(request):

    flights = Flight.objects.all()
    flight_data = []

    for flight in flights:
        flight_data.append({
            'title': flight.flight_number + " - " + flight.origin.name + " to " + flight.destination.name,
            'start': flight.departure_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': flight.arrival_time.strftime('%Y-%m-%dT%H:%M:%S'),
            # 'description': str(flight),
            'className': 'bg-primary'
        })

    context = {'flight_data': flight_data}
    return render(request, 'pages/white_board.html', context)
