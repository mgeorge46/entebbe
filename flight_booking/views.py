import requests
import json
from .forms import FlightBookingForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from .models import FlightBooking, Airport, Aircraft
from django.core.exceptions import ValidationError
from django.contrib import messages
from .flight_functions import calculate_flight, generate_unique_flight_number,generate_unique_flight_leg_reference


def submit_booking_form(request):
    if request.method == 'POST':
        # Extract data from the form submission
        from_airport_code = request.POST.get('from')
        to_airport_code = request.POST.get('to')
        aircraft_id = request.POST.get('aircraft')
        form_departure_time = request.POST.get('departure_time')
        pax = int(request.POST.get('numberOfPeople'))

        # Fetch the corresponding Airport and Aircraft instances
        try:
            from_airport = Airport.objects.get(iata=from_airport_code)
            to_airport = Airport.objects.get(iata=to_airport_code)
            aircraft = Aircraft.objects.get(update_comments=aircraft_id)
        except (Airport.DoesNotExist, Aircraft.DoesNotExist) as e:
            messages.error(request, "Invalid airport or aircraft selection.")
            return redirect('booking_planning')

        # Validate the number of passengers against the aircraft's seating capacity
        if pax > aircraft.seating_capacity:
            messages.error(request, "Number of passengers exceeds the aircraft's seating capacity.")
            return redirect('booking_planning')

        # Create the FlightBooking instance
        try:
            api_response = calculate_flight(from_airport.iata, to_airport.iata)
            flight_number = generate_unique_flight_number()
            flight_leg = generate_unique_flight_leg_reference()
            recent_flights = FlightBooking.objects.filter(flight_tracking_id=flight_leg).order_by('-record_date')[:10]
            flight_booking = FlightBooking.objects.create(
                flight_booking_number=flight_number,
                departure_time=form_departure_time,
                flight_tracking_id=flight_leg,
                airway_distance_true=api_response["distance"],
                fuel=api_response["fuel"],
                time=api_response["time"],
                route=api_response["route"],
                origin=from_airport,
                destination=to_airport,
                aircraft=aircraft,
                booking_pax=pax,
                added_by=request.user
            )
            flight_booking.save()
            messages.success(request, "Flight Estimates")
            return render(request, 'flight_booking/booking_success.html', {'api_response': api_response})
        except ValidationError as e:
            # generic validation errors
            messages.error(request, str(e))
            return redirect('booking_planning')
    else:
        # Handle GET request or other methods
        airports = Airport.objects.all()
        aircrafts = Aircraft.objects.all()
        return render(request, 'flight_booking/booking_flight.html', {'airports': airports, 'aircrafts': aircrafts})

def booking_success(request):
    airports = Airport.objects.all()
    aircrafts = Aircraft.objects.all()
    return render(request, 'flight_booking/booking_success.html', {'airports': airports, 'aircrafts': aircrafts})

@csrf_exempt
def ajax_flight_booking(request):
    if request.method == 'POST':
        # Extract data from request.POST
        from_airport = get_object_or_404(Airport, name=request.POST.get('from'))
        to_airport = get_object_or_404(Airport, name=request.POST.get('to'))
        aircraft = get_object_or_404(Aircraft, abbreviation=request.POST.get('aircraft'))
        booking_pax = int(request.POST.get('numberOfPeople'))

        if booking_pax > aircraft.seating_capacity:
            return JsonResponse({'error': 'Number of people exceeds the seating capacity of the selected aircraft.'},
                                status=400)

        # Create and save the FlightBooking instance
        FlightBooking.objects.create(
            origin=from_airport,
            destination=to_airport,
            aircraft=aircraft,
            booking_pax=booking_pax,
            # Add other fields as necessary
        )
        return JsonResponse({'success': 'Flight booked successfully!'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def booking_view(request):
    if request.method == 'POST':
        form = FlightBookingForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page or handle as needed
    else:
        form = FlightBookingForm()

    return render(request, 'flight_booking/booking_flight.html', {'form': form})


def booking(request):
    return render(request, 'flight_booking/booking_flight.html')
