from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import DetailView, UpdateView
from django_tables2 import RequestConfig

from passengers.models import PassengerBooking
from .forms import FlightForm, FlightSearchForm
from .models import Flight
from .tables import FlightTable
from flight_booking.flight_functions import generate_unique_flight_number


class FlightDetailView(LoginRequiredMixin, DetailView):
    model = Flight
    template_name = 'flight_dispatch/flight_detail.html'
    context_object_name = 'flight'
    slug_field = 'flight_number'
    slug_url_kwarg = 'flight_number'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flight = self.get_object()

        # calculate booked tickets where booking_status is 'Active'
        booked_tickets = PassengerBooking.objects.filter(flight_number=flight, booking_status='Active').count()
        if flight.return_flight:
            booked_tickets += PassengerBooking.objects.filter(return_flight=flight, booking_status='Active').count()

        # calculate other bookings where booking_status is not 'Active'
        other_bookings = PassengerBooking.objects.filter(flight_number=flight).exclude(booking_status='Active').count()
        if flight.return_flight:
            other_bookings += PassengerBooking.objects.filter(return_flight=flight).exclude(
                booking_status='Active').count()
        cabin_crew_members = flight.cabin_crew.all()
        flight_crew_members = flight.flight_crew.all()
        cabin_crew_number = cabin_crew_members.count()
        flight_crew_number = len(flight_crew_members)
        # calculate remaining seats
        remaining_seats = flight.aircraft.seating_capacity - booked_tickets

        context['seating_capacity'] = flight.aircraft.seating_capacity
        context['booked_tickets'] = booked_tickets
        context['remaining_seats'] = remaining_seats if remaining_seats > 0 else 0
        context['other_bookings'] = other_bookings
        context['cabin_crew_members'] = cabin_crew_members
        context['flight_crew_members'] = flight_crew_members
        context['cabin_crew_number'] = cabin_crew_number
        context['flight_crew_number'] = flight_crew_number

        return context


class FlightUpdateView(LoginRequiredMixin, UpdateView):
    model = Flight
    template_name = 'flight_dispatch/flight_update.html'
    context_object_name = 'aircraft'
    form_class = FlightForm

    # Set flight_number field to read-only
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['flight_number'].disabled = True
        form.fields['trip_type'].widget = forms.HiddenInput()  # Hide the trip_type field
        form.fields['update_comments'] = forms.CharField(required=True)
        return form

    def get_initial(self):
        initial = super().get_initial()
        initial['update_comments'] = ''  # Set the update_comments field to an empty value
        return initial

    def form_valid(self, form):
        if self.request.method == 'POST' and 'submit' in self.request.POST:
            flight = form.save(commit=False)
            flight.updated_by = self.request.user.username
            flight.updated_date = timezone.now()
            update_comments = form.cleaned_data['update_comments']
            if not update_comments:
                form.add_error('update_comments', 'Update comments are required.')
                return self.form_invalid(form)
            flight.save()
            form.save_m2m()
            messages.success(self.request, 'Flight Updated successfully.')
            return redirect('flight_details', flight_number=flight.flight_number)


@login_required
def create_flight(request):
    if request.method == 'POST':
        form = FlightForm(request.POST, new_flight=True)
        if form.is_valid():
            flight = form.save(commit=False)
            flight.added_by = request.user
            flight.save()
            messages.success(request, 'Flight Booked Successfully')

            if flight.trip_type == 'round-trip':
                # Generate a unique flight number
                flight_number = generate_unique_flight_number()

                return_flight = Flight(
                    flight_number=flight_number,
                    origin=flight.destination,
                    destination=flight.origin,
                    departure_time=flight.return_departure_time,
                    arrival_time=flight.return_arrival_time,
                    return_departure_time=None,
                    return_arrival_time=None,
                    aircraft=flight.aircraft,
                    trip_type='one-way',
                    flight_status='Scheduled',
                    flight_dispatch_method='Automated',
                    added_by=request.user,
                )
                return_flight.save()
                form.save_m2m()
                messages.success(request, 'Return Flight Booked Successfully')

            return redirect('flight_list')
    else:
        form = FlightForm(new_flight=True)

    return render(request, 'flight_dispatch/flight_schedule.html', {'form': form})


@login_required()
def flight_list(request):
    form = FlightSearchForm(request.GET)
    per_page = 50  # default value
    if form.is_valid():
        search_term = form.cleaned_data['search_term']
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
        per_page = form.cleaned_data['per_page']  # if form is valid, update the value
        flight_status = form.cleaned_data['flight_status']  # Fetch flight_status from form

        queryset = Flight.objects.all()

        if search_term:
            queryset = queryset.filter(
                Q(flight_number__icontains=search_term) |
                Q(origin__name__icontains=search_term) |
                Q(destination__name__icontains=search_term) |
                Q(flight_status__icontains=search_term)
            )

        if flight_status:
            queryset = queryset.filter(flight_status=flight_status)  # Filter by flight_status

        if date_from and date_to:
            queryset = queryset.filter(departure_time__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(departure_time__gte=date_from)
        elif date_to:
            queryset = queryset.filter(departure_time__lte=date_to)
    else:
        queryset = Flight.objects.all()

    table = FlightTable(queryset)
    RequestConfig(request, paginate={"per_page": per_page}).configure(table)

    return render(request, 'flight_dispatch/flight_list.html', {'table': table, 'form': form})


def get_flights(request):
    flights = Flight.objects.all()
    flight_data = []

    for flight in flights:
        flight_data.append({
            'id': flight.id,
            'title': flight.flight_number,
            'start': flight.departure_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': flight.arrival_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'description': str(flight)
        })

    return JsonResponse(flight_data, safe=False)



