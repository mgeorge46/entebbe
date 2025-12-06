from accounts.models import LeaveRequest
from django import forms
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

from .models import Flight, Airport


class FlightForm(forms.ModelForm):
    ERROR_PAST_TIME = '{} cannot be in the past!'
    ERROR_TIME_SEQUENCE = '{} must be later than {}.'
    ERROR_TIME_DIFFERENCE = '{} must be quite ahead {}!'
    ERROR_SAME_ORIGIN_DESTINATION = 'Origin and destination cannot be the same!'
    ERROR_SAME_SCHEDULE = 'All Schedules cannot be the same!'

    class Meta:
        model = Flight
        fields = ['flight_number', 'trip_type', 'origin', 'destination', 'departure_time', 'arrival_time',
                  'return_departure_time', 'return_arrival_time', 'aircraft', 'flight_dispatch_method',
                  'flight_comments', 'flight_status', 'cabin_crew', 'flight_crew']
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'return_departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'return_arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        new_flight = kwargs.pop('new_flight', False)
        super().__init__(*args, **kwargs)
        # Control to assign users whose profile reads cabin crew and flight crew
        User = get_user_model()
        self.fields['cabin_crew'].queryset = User.objects.filter(department='cabin_crew')
        self.fields['flight_crew'].queryset = User.objects.filter(department='flight_crew')

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['flight_number'].widget.attrs['readonly'] = True

        if new_flight:
            self.fields['flight_status'].widget = forms.HiddenInput()
        if not self.instance.pk:  # Only for new flights
            self.fields['flight_number'].initial = 'EAWF-' + get_random_string(length=4,
                                                                               allowed_chars='1234567890') + \
                                                   get_random_string(
                                                       length=2, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            self.fields['flight_number'].widget.attrs['readonly'] = True

        for field_name in ['return_departure_time', 'return_arrival_time']:
            self.fields[field_name].widget.attrs['class'] = 'return-field'
            self.fields[field_name].widget.attrs['style'] = 'display:none;'

        self.fields['trip_type'].widget.attrs['onchange'] = "toggleReturnFields()"
        self.fields['flight_dispatch_method'].required = True
        self.fields['flight_dispatch_method'].initial = ''

    def _validate_aircraft_availability(self, cleaned_data):
        aircraft = cleaned_data.get('aircraft')
        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')

        if aircraft and departure_time and arrival_time:
            # Check if this aircraft is already booked in this time slot
            overlapping_flights = Flight.objects.filter(
                aircraft=aircraft,
                departure_time__lt=arrival_time,
                arrival_time__gt=departure_time
            )

            # Exclude the current flight from the queryset
            if self.instance:
                overlapping_flights = overlapping_flights.exclude(pk=self.instance.pk)

            if overlapping_flights.exists():
                self.add_error('aircraft', 'This aircraft is already booked for the selected time slot.')

    def clean(self):
        cleaned_data = super().clean()
        self._validate_time_fields(cleaned_data)
        self._validate_origin_destination(cleaned_data)
        self._validate_same_schedule(cleaned_data)
        self._validate_aircraft_availability(cleaned_data)
        cabin_crew = cleaned_data.get('cabin_crew')
        flight_crew = cleaned_data.get('flight_crew')
        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        aircraft = cleaned_data.get('aircraft')
        origin = cleaned_data.get('origin')
        # 1. Check for Overlapping Assignments
        self.check_overlapping_assignments(cabin_crew, departure_time, arrival_time)
        self.check_overlapping_assignments(flight_crew, departure_time, arrival_time)
        # 2. Sequential Flight Assignments
        self.check_sequential_flight_assignments(cabin_crew, origin, departure_time)
        self.check_sequential_flight_assignments(flight_crew, origin, departure_time)
        # 3. Limit Total Flight Hours
        self.check_total_flight_hours(cabin_crew, departure_time, arrival_time)
        self.check_total_flight_hours(flight_crew, departure_time, arrival_time)
        # 4. Check for Approved Leave
        self.check_for_approved_leave(cabin_crew, departure_time, arrival_time)
        self.check_for_approved_leave(flight_crew, departure_time, arrival_time)
        # 5. Respect Aircraft Capacity
        #self.check_aircraft_capacity(cabin_crew, flight_crew, aircraft)
        return cleaned_data
    def _validate_time_fields(self, cleaned_data):
        time_pairs = [
            ('departure_time', 'arrival_time'),
            ('return_departure_time', 'return_arrival_time'),
        ]
        for start_time_key, end_time_key in time_pairs:
            start_time = cleaned_data.get(start_time_key)
            end_time = cleaned_data.get(end_time_key)
            if start_time and end_time:
                self._validate_time(start_time, end_time, start_time_key, end_time_key)

        # validate return_departure_time is at least 2 hours after arrival_time
        arrival_time = cleaned_data.get('arrival_time')
        return_departure_time = cleaned_data.get('return_departure_time')
        if arrival_time and return_departure_time:
            if return_departure_time - arrival_time < timezone.timedelta(hours=2):
                self.add_error('return_departure_time',
                               self.ERROR_TIME_DIFFERENCE.format('Return departure time', 'Arrival time'))

        # validate return_arrival_time is at least 2 hours after return_departure_time
        return_arrival_time = cleaned_data.get('return_arrival_time')
        if return_departure_time and return_arrival_time:
            if return_arrival_time - return_departure_time < timezone.timedelta(hours=2):
                self.add_error('return_arrival_time',
                               self.ERROR_TIME_DIFFERENCE.format('Return arrival time', 'Return departure time'))

    def _validate_time(self, start_time, end_time, start_time_key, end_time_key):
        if start_time < timezone.now():
            self.add_error(start_time_key, self.ERROR_PAST_TIME.format(start_time_key.capitalize().replace('_', ' ')))
        if end_time < timezone.now():
            self.add_error(end_time_key, self.ERROR_PAST_TIME.format(end_time_key.capitalize().replace('_', ' ')))
        if end_time <= start_time:
            self.add_error(end_time_key, self.ERROR_TIME_SEQUENCE.format(end_time_key.capitalize().replace('_', ' '),
                                                                         start_time_key.capitalize().replace('_', ' ')))
        if (end_time - start_time) < timezone.timedelta(minutes=30):
            self.add_error(end_time_key, self.ERROR_TIME_DIFFERENCE.format(end_time_key.capitalize().replace('_', ' '),
                                                                           start_time_key.capitalize().replace('_',
                                                                                                               ' ')))
    def _validate_origin_destination(self, cleaned_data):
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')

        if origin and destination:
            if origin == destination:
                self.add_error('destination', self.ERROR_SAME_ORIGIN_DESTINATION)

    def _validate_same_schedule(self, cleaned_data):
        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        return_departure_time = cleaned_data.get('return_departure_time')
        return_arrival_time = cleaned_data.get('return_arrival_time')

        if (departure_time and arrival_time and return_departure_time and return_arrival_time and
                departure_time == arrival_time == return_departure_time == return_arrival_time):
            self.add_error(None, self.ERROR_SAME_SCHEDULE)
    def _validate_time(self, start_time, end_time, start_time_key, end_time_key):
        if not self.instance.pk:  # This checks if the flight is a new record (does not exist in the DB yet)
            if start_time < timezone.now():
                self.add_error(start_time_key, self.ERROR_PAST_TIME.format(start_time_key.capitalize().replace('_', ' ')))
            if end_time < timezone.now():
                self.add_error(end_time_key, self.ERROR_PAST_TIME.format(end_time_key.capitalize().replace('_', ' ')))

        # This condition should always be checked regardless of new or existing flight
        if end_time <= start_time:
            self.add_error(end_time_key, self.ERROR_TIME_SEQUENCE.format(end_time_key.capitalize().replace('_', ' '),
                                                                         start_time_key.capitalize().replace('_', ' ')))
        if (end_time - start_time) < timezone.timedelta(minutes=30):
            self.add_error(end_time_key, self.ERROR_TIME_DIFFERENCE.format(end_time_key.capitalize().replace('_', ' '),
                                                                           start_time_key.capitalize().replace('_', ' ')))


    def check_overlapping_assignments(self, crew, departure_time, arrival_time):
        # Check if any of the crew members are assigned to another flight at the same time
        overlapping_flights = Flight.objects.filter(
            models.Q(cabin_crew__in=crew) | models.Q(flight_crew__in=crew),
            departure_time__lt=arrival_time,
            arrival_time__gt=departure_time
        ).exclude(pk=self.instance.pk if self.instance else None)

        if overlapping_flights.exists():
            raise forms.ValidationError("Some crew members are assigned to another flight at the same time.")

    def check_sequential_flight_assignments(self, crew, origin, departure_time):
        # Find the last flight for each crew member before the current flight's departure
        last_flights = Flight.objects.filter(
            models.Q(cabin_crew__in=crew) | models.Q(flight_crew__in=crew),
            departure_time__lt=departure_time
        ).order_by('-departure_time').distinct()

        # Check that the destination of the last flight matches the origin of the current flight
        for flight in last_flights:
            if flight.destination != origin:
                raise forms.ValidationError(f"{flight.cabin_crew} or {flight.flight_crew} cannot be assigned: "
                                            f"the next flight must originate from {flight.destination}.")

    def check_total_flight_hours(self, crew, departure_time, arrival_time):
        # Calculate the duration of the current flight
        current_flight_duration = (arrival_time - departure_time).total_seconds() / 3600  # convert to hours

        for member in crew:
            # Calculate total flight hours for each crew member
            total_hours = Flight.objects.filter(
                models.Q(cabin_crew=member) | models.Q(flight_crew=member),
                departure_time__lt=arrival_time
            ).aggregate(total_hours=models.Sum(models.F('arrival_time') - models.F('departure_time')))['total_hours']

            total_hours = total_hours.total_seconds() / 3600 if total_hours else 0  # convert to hours

            # Check if adding the current flight would exceed the limit
            if total_hours + current_flight_duration > 30000:
                raise forms.ValidationError(f"{member} cannot be assigned: exceeds 30 hours of total flight time.")

    def check_for_approved_leave(self, crew, departure_time, arrival_time):
        # Check if any crew member has approved leave during the flight
        on_leave = LeaveRequest.objects.filter(
            user__in=crew,
            start_date__lte=arrival_time.date(),
            end_date__gte=departure_time.date(),
            status=LeaveRequest.APPROVED
        )

        if on_leave.exists():
            raise forms.ValidationError(
                f"{', '.join(str(leave.user) for leave in on_leave)} has approved leave during the flight.")

    def check_aircraft_capacity(self, aircraft, cabin_crew, flight_crew,):
        # Check if the number of assigned crew exceeds the aircraft's capacity
        if len(cabin_crew) > aircraft.cabin_crew_capacity or len(flight_crew) > aircraft.flight_crew_capacity:
            raise forms.ValidationError("The number of assigned cabin/flight crew exceeds the aircraft's capacity.")


class FlightSearchForm(forms.Form):
    TRIP_STATUS = (
        ('', 'All'),
        ('Dispatched', 'Dispatched'),
        ('Scheduled', 'Scheduled'),
        ('Cancelled', 'Cancelled'),
        ('not-taken', 'Not Taken'),
        ('Dispatching', 'Dispatching'),
        ('OnTrip', 'OnTrip'),
        ('Delayed', 'Delayed'),
        ('Arrived', 'Arrived')
    )

    search_term = forms.CharField(label='Search Term', required=False)
    flight_status = forms.ChoiceField(label='Flight Status', choices=TRIP_STATUS, required=False)
    date_from = forms.DateTimeField(required=False, widget=forms.DateInput(attrs={'type': 'datetime-local'}))
    date_to = forms.DateTimeField(required=False, widget=forms.DateInput(attrs={'type': 'datetime-local'}))
    per_page = forms.ChoiceField(label='Rows Per Page', choices=[(10, 10), (20, 20), (30, 30), (50, 50)], initial=50)

