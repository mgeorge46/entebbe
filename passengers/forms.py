from django import forms
from flight_dispatch.models import Flight
from .models import Passenger, PassengerBooking, PassengerGroup
from django.db.models import Q
from django.utils import timezone

TRIP_CHOICES = (('', ''), ('one-way', 'One Way'), ('round-trip', 'Round Trip'),)


class BaseCreationForm(forms.ModelForm):
    active_flights = Flight.objects.filter(
        Q(flight_status='Scheduled') | Q(flight_status='In Progress'),
        departure_time__gt=timezone.now()
    )
    flight_number = forms.ModelChoiceField(
        queryset=active_flights,
        empty_label=None,
        required=False,
    )
    seat_number = forms.CharField(required=True)

    trip_type = forms.ChoiceField(choices=TRIP_CHOICES, required=True, )

    def clean_seat_number(self):
        seat_number = self.cleaned_data['seat_number']
        flight_number = self.cleaned_data['flight_number']

        # Check if a booking with the same flight number and seat number already exists
        if PassengerBooking.objects.filter(flight_number=flight_number, seat_number=seat_number).exists():
            raise forms.ValidationError('This seat number is already taken for the selected flight.')

        return seat_number

    class Meta:
        abstract = True


class PassengerCreationForm(BaseCreationForm):
    group_name = forms.ModelChoiceField(
        queryset=PassengerGroup.objects.all(),
        empty_label=None,
        required=False,
    )

    booking_reference = forms.ModelChoiceField(
        queryset=PassengerBooking.objects.values_list('booking_reference', flat=True),
        required=False
    )

    # Add return_flight field

    return_flight = forms.ModelChoiceField(
        queryset=BaseCreationForm.active_flights,
        empty_label=None,
        required=False,
    )

    class Meta(BaseCreationForm.Meta):
        model = Passenger
        exclude = ['updated_by', 'updated_date', 'added_by', 'record_date', 'passenger_comments_update']
        include = ['group_name']

        widgets = {
            'date_of_birth': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'passport_expiration_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(PassengerCreationForm, self).__init__(*args, **kwargs)
        self.fields['group_name'].empty_label = ''
        self.fields['group_name'].initial = None
        self.fields['group_name'].required = False


class BookingCreationForm(BaseCreationForm):
    class Meta(BaseCreationForm.Meta):
        model = PassengerBooking
        exclude = ['updated_by', 'updated_date', 'added_by', 'record_date']

    def clean(self):
        cleaned_data = super().clean()
        passenger_id = cleaned_data.get('passenger_id')
        flight_number = cleaned_data.get('flight_number')
        return_flight = cleaned_data.get('return_flight')
        trip_type = cleaned_data.get('trip_type')

        # Check if a passenger is already booked on the same flight
        if PassengerBooking.objects.filter(passenger_id=passenger_id, flight_number=flight_number).exists():
            raise forms.ValidationError("This passenger has already been booked on this flight.")

        # Check if a passenger is booked on another flight that has the same departure date
        if PassengerBooking.objects.filter(passenger_id=passenger_id,
                                  flight_number__departure_time__date=flight_number.departure_time.date()).exists():
            raise forms.ValidationError(
                "This passenger has been booked on another flight with the same departure date.")
        if PassengerBooking.objects.filter(passenger_id=passenger_id,
                                  flight_number__arrival_time__date=flight_number.arrival_time.date()).exists():
            raise forms.ValidationError(
                "This passenger has been booked on another flight with the same arrival date.")

        # Check if the trip type is round-trip
        if trip_type == 'round-trip':
            # Check if a return flight is selected
            if return_flight is None:
                raise forms.ValidationError("Please select a return flight for a round-trip booking.")

            if return_flight.departure_time <= timezone.now():
                raise forms.ValidationError("The return flight must have a future departure date.")

            if return_flight.departure_time < flight_number.departure_time:
                raise forms.ValidationError("The return flight must depart after the outgoing flight.")

            if return_flight.destination == flight_number.destination:
                raise forms.ValidationError(
                    "The return flight and the outgoing flight must have different destinations.")

            if return_flight.destination != flight_number.origin:
                raise forms.ValidationError(
                    "The return flight's destination must be equivalent to the outgoing flight's origin.")

            if return_flight.origin != flight_number.destination:
                raise forms.ValidationError(
                    "The return flight's origin must be equivalent to the outgoing flight's destination.")

        return cleaned_data


class PassengerGroupCreationForm(forms.ModelForm):
    class Meta:
        model = PassengerGroup
        fields = ['group_name', 'passengers_ids']
