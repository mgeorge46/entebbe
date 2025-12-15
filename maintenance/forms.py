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
    FIXED: Scheduling form - NO completion fields
    - Removed: maintenance_hours, maintenance_hours_added, remarks, maintenance_report
    - These will be captured during sign-off/completion
    """
    
    class Meta:
        model = ComponentMaintenance
        # FIXED: Only these 4 fields for scheduling
        fields = [
            'main_type_schedule',
            'maintenance_type',
            'start_date',
            'end_date',
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'main_type_schedule': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data



class BatchComponentMaintenanceCompletionForm(forms.Form):
    """Batch sign-off form"""
    
    actual_end_date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        label="Batch Completion Date"
    )
    
    hours_added = forms.DecimalField(
        required=True,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'id': 'hours_input'
        }),
        label="Hours to Add to EACH Component"
    )
    
    completion_remarks = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5
        }),
        label="Batch Completion Remarks"
    )
    
    completion_report = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file'
        }),
        label="Batch Report (optional)"
    )


class ComponentMaintenanceCompletionForm(forms.Form):
    """
    NEW: Completion form used by complete_component_maintenance view
    This is where hours_added, remarks, and report are captured
    """
    
    actual_start_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        label="Actual Start Date (optional)"
    )
    
    actual_end_date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        label="Actual Completion Date",
        help_text="When was the maintenance actually completed?"
    )
    
    actual_hours_added = forms.DecimalField(
        required=True,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label="Hours to Add Back to Component",
        help_text="Maintenance hours to add to this component"
    )
    
    completion_remarks = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe work performed, parts replaced, findings...'
        }),
        label="Completion Remarks",
        help_text="Document what was actually done"
    )
    
    completion_report = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': '.pdf,.doc,.docx,.xlsx,.xls,.jpg,.png'
        }),
        label="Upload Completion Report (optional)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        actual_start = cleaned_data.get('actual_start_date')
        actual_end = cleaned_data.get('actual_end_date')
        
        if actual_start and actual_end and actual_end <= actual_start:
            raise forms.ValidationError("Actual end must be after actual start.")
        
        return cleaned_data


class BulkComponentMaintenanceConfirmForm(forms.Form):
    """Form for bulk confirmation of multiple maintenances"""
    
    maintenance_ids = forms.CharField(widget=forms.HiddenInput(), required=True)
    
    actual_end_date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        label="Batch Completion Date"
    )
    
    hours_added = forms.DecimalField(
        required=True,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label="Hours to Add to Each Component"
    )
    
    completion_remarks = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe work performed across all components...'
        }),
        required=True,
        label="Batch Completion Remarks"
    )
    
    completion_report = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': '.pdf,.doc,.docx,.xlsx,.xls'
        }),
        label="Upload Batch Completion Report"
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