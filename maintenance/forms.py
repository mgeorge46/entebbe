from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from .models import AircraftMainComponent
from django.db import transaction

from .models import Aircraft, AircraftMainComponent, AircraftSubComponent, FlightTechLog, AircraftSub3Component, \
    AircraftSub2Component, AircraftMaintenanceTechLog, Airport


class BaseComponentForm(forms.ModelForm):
    multiple_entries = forms.BooleanField(required=False, widget=forms.CheckboxInput(
        attrs={'class': 'multiple-entries-checkbox', 'id': 'multipleEntriesCheckbox'}), label='Add Multiple Components')
    serial_numbers = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'serial-numbers-textarea',
                'id': 'serialNumbersTextarea',
                'style': 'display:none;',
                'placeholder': 'Enter serial numbers separated by commas'
            }
        ),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.is_update = kwargs.pop('is_update', False)  # Extract the is_update flag
        super().__init__(*args, **kwargs)

        if self.is_update:
            # Hide the fields for update operations
            self.fields['multiple_entries'].widget = forms.HiddenInput()
            #self.fields['serial_numbers'].widget = forms.HiddenInput()
    class Meta:
        abstract = True

    def clean_serial_numbers(self):
        data = self.cleaned_data['serial_numbers']
        if self.cleaned_data.get('multiple_entries') and not data:
            raise forms.ValidationError("This field is required if adding multiple components.")
        return data.split(',')



class AirportForm(forms.ModelForm):
    class Meta:
        model = Airport
        fields = '__all__'
        exclude = ['added_by', 'record_date', 'updated_date', 'updated_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # Checks if the record is being edited to make the Update_comments required
            self.fields['update_comments'].required = True


class AircraftFormAdd(forms.ModelForm):
    class Meta:
        model = Aircraft
        exclude = ['updated_by', 'updated_date', 'added_by', 'record_date', 'update_comments']


class AircraftFormUpdate(forms.ModelForm):
    class Meta:
        model = Aircraft
        exclude = ['updated_by', 'updated_date', 'added_by', 'record_date', ]


class AircraftMainComponentForm(BaseComponentForm):
    class Meta:
        model = AircraftMainComponent
        exclude = ['update_comments', 'aircraft_attached', 'updated_by', 'updated_date', 'added_by',
                   'record_date', 'maintenance_status', 'component_status', 'date_attached', 'date_re_provisioned',
                   'date_detached', 'item_cycle', 'item_original_hours']
        widgets = {
            'item_calender': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'install_date': forms.DateTimeInput(attrs={'type': 'date'}),
            'delivery_date': forms.DateTimeInput(attrs={'type': 'date'}),
        }


class AircraftSubComponentForm(BaseComponentForm):
    class Meta:
        model = AircraftSubComponent
        exclude = ['update_comments', 'parent_component', 'updated_by', 'updated_date', 'added_by',
                   'record_date', 'maintenance_status', 'component_status', 'date_attached', 'date_re_provisioned',
                   'date_detached', 'item_cycle', 'item_original_hours']
        widgets = {
            'item_calender': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'install_date': forms.DateTimeInput(attrs={'type': 'date'}),
            'delivery_date': forms.DateTimeInput(attrs={'type': 'date'}),
        }


class AircraftSub2ComponentForm(BaseComponentForm):
    class Meta:
        model = AircraftSub2Component
        exclude = ['update_comments', 'parent_sub_component', 'updated_by', 'updated_date',
                   'added_by',
                   'record_date', 'maintenance_status', 'component_status', 'date_attached', 'date_re_provisioned',
                   'date_detached', 'item_cycle', 'item_original_hours']
        widgets = {
            'item_calender': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'install_date': forms.DateTimeInput(attrs={'type': 'date'}),
            'delivery_date': forms.DateTimeInput(attrs={'type': 'date'}),
        }

class CloneComponentForm(forms.Form):
    serial_numbers = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter new serial numbers, separated by commas or new lines'}), label='New Serial Numbers')

class AircraftSub3ComponentForm(BaseComponentForm):
    class Meta:
        model = AircraftSub3Component
        exclude = ['update_comments', 'parent_sub2_component', 'updated_by', 'updated_date',
                   'added_by',
                   'record_date', 'maintenance_status', 'component_status', 'date_attached', 'date_re_provisioned',
                   'date_detached', 'item_cycle', 'item_original_hours']
        widgets = {
            'item_calender': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'install_date': forms.DateTimeInput(attrs={'type': 'date'}),
            'delivery_date': forms.DateTimeInput(attrs={'type': 'date'}),
        }



class FlightTechLogForm(forms.ModelForm):
    class Meta:
        model = FlightTechLog
        exclude = ['update_comments', 'parent_sub_component', 'updated_by', 'updated_date', 'added_by', 'record_date',
                   'aircraft']
        widgets = {
            'takeoff': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'landing': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        flights_on_trip = kwargs.pop('flights_on_trip')
        super(FlightTechLogForm, self).__init__(*args, **kwargs)
        self.fields['flight_leg'].queryset = flights_on_trip

    def clean(self):
        cleaned_data = super().clean()
        takeoff = cleaned_data.get('takeoff')
        landing = cleaned_data.get('landing')

        if takeoff and landing:
            time_difference = landing - takeoff
            if time_difference.total_seconds() < 1800:
                raise ValidationError("Landing time must be greater than takeoff time.")


class AircraftMaintenanceTechLogForm(forms.ModelForm):
    class Meta:
        model = AircraftMaintenanceTechLog
        exclude = ['update_comments', 'parent_sub_component', 'updated_by', 'updated_date', 'added_by', 'record_date']
        widgets = {
            'arrival_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),

        }
