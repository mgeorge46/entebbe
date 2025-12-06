from django import forms
from .models import FlightBooking
from maintenance.models import Aircraft, Airport


class FlightBookingForm(forms.ModelForm):
    from_airport = forms.ModelChoiceField(queryset=Airport.objects.all(), label="From")
    to_airport = forms.ModelChoiceField(queryset=Airport.objects.all(), label="To")
    aircraft = forms.ModelChoiceField(queryset=Aircraft.objects.all())

    class Meta:
        model = FlightBooking
        fields = ['from_airport', 'to_airport', 'aircraft', 'departure_time', 'arrival_time', 'trip_type',
                  'booking_pax']

    def clean(self):
        cleaned_data = super().clean()
        aircraft = cleaned_data.get("aircraft")
        #booking_pax = cleaned_data.get("booking_pax")

        booking_pax = forms.IntegerField(
            required=True,
            min_value=1,
            error_messages={
                'required': 'Please enter the number of passengers.',
                'invalid': 'Please enter a valid whole number.'
            }
        )

        if booking_pax and aircraft and booking_pax > aircraft.seating_capacity:
            self.add_error('booking_pax', 'Number of people exceeds the seating capacity of the selected aircraft.')

        return cleaned_data
