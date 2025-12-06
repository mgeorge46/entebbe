from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Max
from django.urls import reverse
from django.shortcuts import render, redirect
from django.views.generic import DetailView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import PassengerCreationForm, BookingCreationForm, PassengerGroupCreationForm
from .models import Passenger, PassengerBooking, PassengerGroup
from django.db.models import Q
from django.utils import timezone


class PassengerListView(LoginRequiredMixin, ListView):
    model = Passenger
    template_name = 'passengers/passenger_list.html'
    context_object_name = 'passengers'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search_query')

        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(date_of_birth__icontains=search_query) |
                Q(nationality__icontains=search_query) |
                Q(passport_number__icontains=search_query) |
                Q(phone_number__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(emergency_contact_number__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        items_per_page = self.request.GET.get('items_per_page')

        if items_per_page and items_per_page.isdigit():
            self.paginate_by = int(items_per_page)

        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get('page_size')
        page_obj = paginator.get_page(page_number)

        # Prefetch related bookings to optimize queries
        queryset = queryset.prefetch_related('passengerbooking_set')

        # Fetch the last flight for each passenger
        passenger_flights_dict = {}
        for passenger in queryset:
            last_flight = passenger.passengerbooking_set.aggregate(last_flight=Max('flight_number'))['last_flight']
            passenger_flights_dict[passenger.id] = last_flight

        # Get the search query or set a default value
        search_query = self.request.GET.get('search_query', '')

        context['page_obj'] = page_obj
        context['passenger_flights'] = passenger_flights_dict
        context['search_query'] = search_query

        return context


class PassengerDetailView(LoginRequiredMixin, DetailView):
    model = Passenger
    template_name = 'passengers/passenger_details.html'
    context_object_name = 'passenger_details'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        passenger = self.object
        # Retrieve the last flight of the passenger
        last_flight = passenger.booking_set.aggregate(
            last_flight_date=Max('flight_number__departure_time'),
            last_flight_number=Max('flight_number__flight_number')
        )
        # Pass the last flight date and flight number to the context
        context['last_flight_date'] = last_flight['last_flight_date']
        context['last_flight_number'] = last_flight['last_flight_number']
        return context


class PassengerUpdateView(LoginRequiredMixin, UpdateView):
    model = Passenger
    fields = ['full_name', 'gender', 'date_of_birth', 'nationality', 'national_id', 'passport_number',
              'passport_issuing_country', 'passport_expiration_date', 'address', 'phone_number', 'email',
              'immigration_details', 'special_requirements', 'emergency_contact_name',
              'emergency_contact_number', 'passenger_comments_update']
    template_name = 'passengers/passenger_update.html'
    context_object_name = 'passenger_update'

    def get_initial(self):
        initial = super().get_initial()
        initial['passenger_comments_update'] = ''  # Set the update_comments field to an empty value
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['passenger_comments_update'].required = True
        return form

    def form_valid(self, form):
        if self.request.method == 'POST' and 'submit' in self.request.POST:
            form.instance.updated_by = self.request.user.username
            form.instance.updated_date = timezone.now()
            messages.success(self.request, 'Passenger Edited Successfully')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('passenger_details', kwargs={'pk': self.object.pk})


def is_aircraft_capacity_reached(aircraft):
    active_bookings_count = PassengerBooking.objects.filter(
        flight_number__aircraft=aircraft,
        booking_status='Active'
    ).count()
    return active_bookings_count >= aircraft.seating_capacity


@login_required
def add_passenger_booking(request):
    if request.method == 'POST':
        form = PassengerCreationForm(request.POST)
        if form.is_valid():
            passenger = form.save(commit=False)
            passenger.added_by = request.user
            group_name = form.cleaned_data['group_name']
            booking_reference = form.cleaned_data['booking_reference']
            seat_number = form.cleaned_data['seat_number']
            trip_type = form.cleaned_data['trip_type']
            flight_number = form.cleaned_data['flight_number']
            return_flight = form.cleaned_data.get('return_flight', None)

            # Check if the aircraft capacity is reached
            if is_aircraft_capacity_reached(flight_number.aircraft):
                messages.error(request, "The aircraft capacity has been reached. Cannot add the booking.")
                return render(request, 'passengers/passenger_add.html', {'form': form})

            # Check if a passenger is already booked on the same flight
            if PassengerBooking.objects.filter(passenger_id=passenger, flight_number=flight_number).exists():
                messages.error(request, "This passenger has already been booked on this flight.")
                return render(request, 'passengers/passenger_add.html', {'form': form})

            '''if Booking.objects.filter(passenger_id=passenger, flight_number=flight_number, status='Active').exists():
                messages.error(request, "This passenger has already been booked on this flight with an active status.")
                return render(request, 'passengers/passenger_add.html', {'form': form})'''

            # Check if the trip type is round-trip
            if trip_type == 'round-trip':
                # Check if a return flight is selected
                if return_flight is None:
                    messages.error(request, "Please select a return flight for a round-trip booking.")
                    return render(request, 'passengers/passenger_add.html', {'form': form})

                # Check if the return flight's destination is equivalent to the outgoing flight's origin
                if return_flight.destination != flight_number.origin:
                    messages.error(request,
                                   "The return flight's destination must be equivalent to the outgoing flight's origin.")
                    return render(request, 'passengers/passenger_add.html', {'form': form})

                # Check if the return flight's origin is equivalent to the outgoing flight's destination
                if return_flight.origin != flight_number.destination:
                    messages.error(request,
                                   "The return flight's origin must be equivalent to the outgoing flight's destination.")
                    return render(request, 'passengers/passenger_add.html', {'form': form})

            # Create a booking
            booking = PassengerBooking(
                flight_number=flight_number,
                seat_number=seat_number,
                trip_type=trip_type,
                passenger_id=passenger,
                added_by=passenger.added_by,
                return_flight=return_flight
            )
            # Create a group
            if group_name:
                # Get or create the PassengerGroup
                group, _ = PassengerGroup.objects.get_or_create(group_name=group_name)
                group.passengers_ids.add(passenger)
                group.save()

            messages.success(request, 'Flight Booked Successfully for the passenger')
            passenger.save()
            booking.save()
            booking.booking_reference.set(booking_reference)
            return redirect('passenger_list')
    else:
        form = PassengerCreationForm()

    return render(request, 'passengers/passenger_add.html', {'form': form})


class BookingListView(LoginRequiredMixin, ListView):
    model = PassengerBooking
    template_name = 'passengers/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 50
    ordering = ['-record_date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bookings = self.get_queryset()
        page_size = int(self.request.GET.get('page_size', self.paginate_by))
        paginator = Paginator(bookings, page_size)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    model = PassengerBooking
    template_name = 'passengers/booking_details.html'
    context_object_name = 'booking_details'


class BookingUpdateView(LoginRequiredMixin, UpdateView):
    model = PassengerBooking
    fields = ['flight_number', 'seat_number', 'passenger_id', 'passenger_relate_id', 'trip_type', 'return_flight',
              'booking_comments', 'update_comments', 'booking_status']
    template_name = 'passengers/booking_update.html'
    context_object_name = 'booking_update'

    def get_initial(self):
        initial = super().get_initial()
        initial['update_comments'] = ''  # Set the update_comments field to an empty value
        return initial

    def form_valid(self, form):
        if self.request.method == 'POST' and 'submit' in self.request.POST:
            form.instance.updated_by = self.request.user.username
            form.instance.updated_date = timezone.now()
            update_comments = form.cleaned_data['update_comments']
            if not update_comments:
                form.add_error('update_comments', 'You cannot Update a record without a reason Kindly add it !.')
                return self.form_invalid(form)

            # Additional checks
            passenger_id = form.cleaned_data.get('passenger_id')
            flight_number = form.cleaned_data.get('flight_number')
            return_flight = form.cleaned_data.get('return_flight')
            trip_type = form.cleaned_data.get('trip_type')

            # Check if the aircraft capacity is reached
            if is_aircraft_capacity_reached(form.cleaned_data['flight_number'].aircraft):
                form.add_error(None, "The aircraft capacity has been reached. Cannot update the booking.")
                return self.form_invalid(form)

            # Check if a passenger is already booked on the same flight
            if PassengerBooking.objects.filter(passenger_id=passenger_id, flight_number=flight_number).exclude(
                    pk=self.object.pk).exists():
                form.add_error('flight_number', "This passenger has already been booked on this flight.")
                return self.form_invalid(form)

            # Check if the trip type is round-trip
            if trip_type == 'round-trip':
                # Check if a return flight is selected
                if return_flight is None:
                    form.add_error('return_flight', "Please select a return flight for a round-trip booking.")
                    return self.form_invalid(form)

                # Check if the return flight is in the future
                if return_flight.departure_time <= timezone.now():
                    form.add_error('return_flight', "The return flight must have a future departure date.")
                    return self.form_invalid(form)

                # Check if the return flight's departure date is later than the outgoing flight's departure date
                if return_flight.departure_time <= flight_number.departure_time:
                    form.add_error('return_flight', "The return flight must depart after the outgoing flight.")
                    return self.form_invalid(form)

                # Check if the return flight and the outgoing flight have different destinations
                if return_flight.destination == flight_number.destination:
                    form.add_error('return_flight', "The return flight and the outgoing flight must have different "
                                                    "destinations.")
                    return self.form_invalid(form)
                if return_flight.destination != flight_number.origin:
                    form.add_error(
                        "The return flight's destination must be equivalent to the outgoing flight's origin.")

                    # Check if the return flight's origin is equivalent to the outgoing flight's destination
                if return_flight.origin != flight_number.destination:
                    form.add_error(
                        "The return flight's origin must be equivalent to the outgoing flight's destination.")

            messages.success(self.request, 'Booking Edited Successfully')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('booking_details', kwargs={'pk': self.object.pk})


@login_required
def add_booking(request):
    if request.method == 'POST':
        form = BookingCreationForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.added_by = request.user
            # Check if the aircraft capacity is reached
            if is_aircraft_capacity_reached(booking.flight_number.aircraft):
                messages.error(request, "The aircraft capacity has been reached. Cannot add the booking.")
                return redirect('add_booking')

            booking.save()
            messages.success(request, 'Passenger Booking Created Successfully')
            return redirect('booking_list')
    else:
        form = BookingCreationForm()
    return render(request, 'passengers/booking_add.html', {'form': form})


class GroupListView(LoginRequiredMixin, ListView):
    model = PassengerGroup
    template_name = 'passengers/group_list.html'
    context_object_name = 'groups'
    paginate_by = 50


class PassengerGroupUpdateView(LoginRequiredMixin, UpdateView):
    model = PassengerGroup
    template_name = 'passengers/group_update.html'
    fields = ['group_name', 'group_status', 'passengers_ids']
    context_object_name = 'group_update'


class PassengerGroupDetailView(LoginRequiredMixin, DetailView):
    model = PassengerGroup
    template_name = 'passengers/group_details.html'
    context_object_name = 'group_details'


@login_required
def create_group(request):
    if request.method == 'POST':
        form = PassengerGroupCreationForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.added_by = request.user
            group.save()
            return redirect('group_list')
    else:
        form = PassengerGroupCreationForm()

    return render(request, 'passengers/group_add.html', {'form': form})
