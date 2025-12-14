from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from .models import AircraftMainComponent
from django.db import transaction
from .models import Aircraft, AircraftMainComponent, AircraftSubComponent, FlightTechLog, AircraftSub3Component, \
    AircraftSub2Component, AircraftMaintenanceTechLog, Airport
from django.contrib.contenttypes.models import ContentType
from maintenance.models import (AircraftMaintenance, ComponentMaintenance)


class ComponentMaintenanceForm(forms.ModelForm):
    """
    Form for scheduling component maintenance with AJAX-powered search.
    Works with all component types through ContentTypes framework.
    """
    
    aircraft = forms.ModelChoiceField(
        queryset=Aircraft.objects.all(),
        required=True,
        label="Aircraft",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_aircraft'})
    )
    
    component_level = forms.ChoiceField(
        choices=[
            ('', '--- Select Component Level ---'),
            ('aircraftmaincomponent', 'Main Component (Level 0)'),
            ('aircraftsubcomponent', 'Sub Component (Level 1)'),
            ('aircraftsub2component', 'Sub2 Component (Level 2)'),
            ('aircraftsub3component', 'Sub3 Component (Level 3)'),
        ],
        required=True,
        label="Component Level",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_component_level'})
    )
    
    component_search = forms.CharField(
        required=False,
        label="Search Component",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_component_search',
            'placeholder': 'Type component name or serial number...',
            'autocomplete': 'off'
        })
    )
    
    content_type_id = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'id': 'id_content_type_id'}),
        required=True
    )
    
    object_id = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'id': 'id_object_id'}),
        required=True
    )

    class Meta:
        model = ComponentMaintenance
        fields = [
            'main_type_schedule',
            'maintenance_type',
            'maintenance_hours',
            'maintenance_hours_added',
            'start_date',
            'end_date',
            'remarks',
            'maintenance_report'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'main_type_schedule': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'maintenance_hours_added': forms.NumberInput(attrs={'class': 'form-control'}),
            'maintenance_report': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.fields['aircraft'].initial = self._get_aircraft_from_instance()
            self.fields['component_level'].initial = self.instance.content_type.model
            self.fields['component_search'].initial = str(self.instance.component_to_maintain)
            self.fields['content_type_id'].initial = self.instance.content_type_id
            self.fields['object_id'].initial = self.instance.object_id

    def _get_aircraft_from_instance(self):
        component = self.instance.component_to_maintain
        if hasattr(component, 'aircraft_attached'):
            return component.aircraft_attached
        elif hasattr(component, 'parent_component'):
            return component.parent_component.aircraft_attached
        elif hasattr(component, 'parent_sub_component'):
            return component.parent_sub_component.parent_component.aircraft_attached
        elif hasattr(component, 'parent_sub2_component'):
            return component.parent_sub2_component.parent_sub_component.parent_component.aircraft_attached
        return None

    def clean(self):
        cleaned_data = super().clean()
        
        if not cleaned_data.get('content_type_id'):
            raise forms.ValidationError("Please select a component to maintain.")
        
        if not cleaned_data.get('object_id'):
            raise forms.ValidationError("Please select a valid component.")
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.content_type_id = self.cleaned_data['content_type_id']
        instance.object_id = self.cleaned_data['object_id']
        
        if commit:
            instance.save()
        
        return instance

class BulkComponentMaintenanceConfirmForm(forms.Form):
    """Form for bulk confirmation of multiple maintenances"""
    
    maintenance_ids = forms.CharField(widget=forms.HiddenInput(), required=True)
    
    confirmation_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any notes about this confirmation...'
        }),
        required=False,
        label="Confirmation Notes"
    )
    
    def clean_maintenance_ids(self):
        ids = self.cleaned_data['maintenance_ids']
        try:
            return [int(id.strip()) for id in ids.split(',') if id.strip()]
        except ValueError:
            raise forms.ValidationError("Invalid maintenance IDs.")

# ==============================================================================
# END OF ADDITIONS TO forms.py
# ==============================================================================


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

# manual maintenance  forms

# Aircraft Maintenance Schedule Form
class AircraftMaintenanceForm(forms.ModelForm):
    class Meta:
        model = AircraftMaintenance
        exclude = ['updated_by', 'updated_date', 'added_by', 'record_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'next_maintenance_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'



# Search and Filter Forms
class AircraftMaintenanceSearchForm(forms.Form):
    SCHEDULE_TYPE = [
        ('', 'All'),
        ('Operational', 'Manual'),
        ('Maintenance', 'Automated'),
    ]
    
    aircraft = forms.ModelChoiceField(
        queryset=Aircraft.objects.all(),
        required=False,
        empty_label='All Aircraft'
    )
    
    maintenance_type = forms.ChoiceField(
        choices=[('', 'All')] + list(AircraftMaintenance._meta.get_field('maintenance_type').choices),
        required=False
    )
    
    schedule_type = forms.ChoiceField(
        choices=SCHEDULE_TYPE,
        required=False,
        label='Schedule Type'
    )
    
    start_date_from = forms.DateTimeField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='From Date'
    )
    
    start_date_to = forms.DateTimeField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='To Date'
    )
    
    search_term = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search aircraft or remarks...'})
    )


class ComponentMaintenanceSearchForm(forms.Form):
    SCHEDULE_TYPE = [
        ('', 'All'),
        ('Operational', 'Manual'),
        ('Maintenance', 'Automated'),
    ]
    
    COMPONENT_LEVEL = [
        ('', 'All Levels'),
        ('aircraftmaincomponent', 'Main Component'),
        ('aircraftsubcomponent', 'Sub Component Level 1'),
        ('aircraftsub2component', 'Sub Component Level 2'),
        ('aircraftsub3component', 'Sub Component Level 3'),
    ]
    
    aircraft = forms.ModelChoiceField(
        queryset=Aircraft.objects.all(),
        required=False,
        empty_label='All Aircraft'
    )
    
    component_level = forms.ChoiceField(
        choices=COMPONENT_LEVEL,
        required=False,
        label='Component Level'
    )
    
    maintenance_type = forms.ChoiceField(
        choices=[('', 'All')] + list(ComponentMaintenance._meta.get_field('maintenance_type').choices),
        required=False
    )
    
    schedule_type = forms.ChoiceField(
        choices=SCHEDULE_TYPE,
        required=False,
        label='Schedule Type'
    )
    
    start_date_from = forms.DateTimeField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='From Date'
    )
    
    start_date_to = forms.DateTimeField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='To Date'
    )
    
    search_term = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search component name or serial...'})
    )