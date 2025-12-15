# views.py
from decimal import Decimal
from django.apps import apps
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, UpdateView, TemplateView, ListView, CreateView
from django_tables2 import RequestConfig
from django_tables2 import SingleTableView
from flight_dispatch.models import Flight
from .filters import AircraftFilter
from .forms import AircraftMainComponentForm, AircraftSubComponentForm, FlightTechLogForm, AircraftFormUpdate, \
    AircraftFormAdd, AircraftMaintenanceTechLogForm, CloneComponentForm, ComponentMaintenanceForm, \
    BulkComponentMaintenanceConfirmForm

from .models import Aircraft, AircraftMainComponent, AircraftSubComponent, AircraftMaintenanceTechLog, FlightTechLog, \
    AircraftSub3Component, AircraftSub2Component, ComponentMaintenance, AircraftMaintenance

from .tables import AircraftTable, SubComponentTable, MainComponentTable, AircraftMaintenanceTechLogTable, \
    FlightTechLogTable, FlightTablePendingTechlog

from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
import uuid
from django import forms


def generate_batch_id():
    """Generate a unique, user-friendly batch ID"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f'MAINT-{timestamp}-{random_suffix}'


class AircraftListView(LoginRequiredMixin, SingleTableView):
    model = Aircraft
    table_class = AircraftTable
    template_name = 'maintenance/aircraft/aircraft_list.html'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        self.filter = AircraftFilter(self.request.GET, queryset=qs)
        return self.filter.qs


class AircraftDetailView(LoginRequiredMixin, DetailView):
    model = Aircraft
    template_name = 'maintenance/aircraft/aircraft_detail.html'
    context_object_name = 'aircraft'
    slug_field = 'registration_number'
    slug_url_kwarg = 'registration_number'

    def get_object(self, queryset=None):
        # This method ensures that self.object is set
        if not hasattr(self, 'object') or self.object is None:
            self.object = super().get_object(queryset)
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aircraft = self.get_object()
        main_components = aircraft.aircraftmaincomponent_set.all().filter(maintenance_status='Attached')
        sub_components = AircraftSubComponent.objects.filter(parent_component__in=main_components,
                                                             maintenance_status='Attached')
        sub2_components = AircraftSub2Component.objects.filter(
            parent_sub_component__parent_component__in=main_components, maintenance_status='Attached')
        sub3_components = AircraftSub3Component.objects.filter(
            parent_sub2_component__parent_sub_component__parent_component__in=main_components,
            maintenance_status='Attached')

        completed_flights = Flight.objects.filter(aircraft=aircraft, flight_status='Completed').count()
        total_main_components = main_components.count()
        total_sub_components = sub_components.count()
        total_sub_2_components = sub2_components.count()
        total_sub_3_components = sub3_components.count()
        main_components_less_than_10 = main_components.filter(maintenance_hours__lt=10).count()
        sub_components_less_than_10 = sub_components.filter(maintenance_hours__lt=10).count()
        sub2_components_less_than_10 = sub2_components.filter(maintenance_hours__lt=10).count()
        sub3_components_less_than_10 = sub3_components.filter(maintenance_hours__lt=10).count()
        main_components_greater_than_or_equal_to_10 = main_components.filter(maintenance_hours__gte=10).count()
        sub_components_greater_than_or_equal_to_10 = sub_components.filter(maintenance_hours__gte=10).count()
        sub2_components_greater_than_or_equal_to_10 = sub2_components.filter(maintenance_hours__gte=10).count()
        sub3_components_greater_than_or_equal_to_10 = sub3_components.filter(maintenance_hours__gte=10).count()
        # Pagination
        page = self.request.GET.get('page')
        paginator = Paginator(main_components, 20)
        try:
            main_components = paginator.page(page)
        except PageNotAnInteger:
            main_components = paginator.page(1)
        except EmptyPage:
            main_components = paginator.page(paginator.num_pages)

        context['main_components'] = main_components
        context['sub_components'] = sub_components
        context['completed_flights'] = completed_flights
        context['total_main_components'] = total_main_components
        context['total_sub_components'] = total_sub_components
        context['total_sub_2_components'] = total_sub_2_components
        context['total_sub_3_components'] = total_sub_3_components
        context['main_components_less_than_10'] = main_components_less_than_10
        context['sub_components_less_than_10'] = sub_components_less_than_10
        context['sub2_components_less_than_10'] = sub2_components_less_than_10
        context['sub3_components_less_than_10'] = sub3_components_less_than_10
        context['main_components_greater_than_or_equal_to_10'] = main_components_greater_than_or_equal_to_10
        context['sub_components_greater_than_or_equal_to_10'] = sub_components_greater_than_or_equal_to_10
        context['sub2_components_greater_than_or_equal_to_10'] = sub2_components_greater_than_or_equal_to_10
        context['sub3_components_greater_than_or_equal_to_10'] = sub3_components_greater_than_or_equal_to_10
        return context


class AircraftUpdateView(LoginRequiredMixin, UpdateView):
    model = Aircraft
    template_name = 'maintenance/aircraft/aircraft_edit.html'
    context_object_name = 'aircraft'
    exclude = ['updated_by', 'updated_date', 'added_by', 'record_date']
    form_class = AircraftFormUpdate

    def form_valid(self, form):
        if form.is_valid():
            form.save()
            messages.success(self.request, 'Aircraft edited successfully.')
            return redirect('list_aircraft')


@login_required
def create_aircraft(request):
    if request.method == 'POST':
        form = AircraftFormAdd(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aircraft Added Successfully')
            return redirect('add_aircraft')
    else:
        form = AircraftFormAdd()
    return render(request, 'maintenance/aircraft/aircraft_add.html', {'form': form})


@login_required
def add_aircraft_main_component(request, aircraft_id):
    aircraft = get_object_or_404(Aircraft, pk=aircraft_id)
    if request.method == 'POST':
        form = AircraftMainComponentForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('multiple_entries'):
                # Assuming serial_numbers is already a list based on the error
                serial_numbers = form.cleaned_data['serial_numbers']
                num_created = 0
                with transaction.atomic():
                    for serial_number in serial_numbers:
                        component = AircraftMainComponent()
                        # Apply other form data to the component
                        for field in form.cleaned_data:
                            if field not in ['multiple_entries', 'serial_numbers']:
                                setattr(component, field, form.cleaned_data[field])
                        component.aircraft_attached = aircraft
                        component.added_by = request.user
                        component.serial_number = serial_number.strip()  # Assuming serial_number is a string here
                        component.save()
                        num_created += 1
                messages.success(request, f'{num_created} Multiple Main Components Added Successfully')
                return redirect('aircraft_main_components_list', pk=aircraft.id)
            else:
                component = form.save(commit=False)
                component.aircraft_attached = aircraft
                component.added_by = request.user
                component.save()
                messages.success(request, 'Main Component Added Successfully')
                return redirect('aircraft_main_components_list', pk=aircraft.id)
    else:
        form = AircraftMainComponentForm()

    return render(request, 'maintenance/main_component/main_component_add.html', {'form': form, 'aircraft': aircraft})


class MainComponentListView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/main_component/main_component_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_term = self.request.GET.get('search', '')
        min_hours = self.request.GET.get('min_hours', '')
        max_hours = self.request.GET.get('max_hours', '')
        aircraft = get_object_or_404(Aircraft, pk=self.kwargs['pk'])

        main_components = AircraftMainComponent.objects.filter(
            Q(component_name__icontains=search_term) |
            Q(aircraft_attached__abbreviation__icontains=search_term),
            aircraft_attached=aircraft
        )
        if min_hours:
            main_components = main_components.filter(maintenance_hours__gte=min_hours)
        if max_hours:
            main_components = main_components.filter(maintenance_hours__lte=max_hours)

        paginator = Paginator(main_components, 50)  # Show 50 main components per page.
        page = self.request.GET.get('page')
        try:
            main_components = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            main_components = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            main_components = paginator.page(paginator.num_pages)

        main_components1 = aircraft.aircraftmaincomponent_set.all()
        total_main_components = main_components1.count()

        table = MainComponentTable(main_components)
        RequestConfig(self.request).configure(table)

        context['table'] = table
        context['aircraft'] = aircraft
        context['total_main_components'] = total_main_components

        return context


class MainComponentUpdateView(LoginRequiredMixin, UpdateView):
    model = AircraftMainComponent
    template_name = 'maintenance/main_component/main_component_edit.html'
    context_object_name = 'main_component'
    form_class = AircraftMainComponentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = True  # Indicate that this is an update operation
        return kwargs

    def form_valid(self, form):
        if form.is_valid():
            main_component = form.save()  # Save and get the instance
            aircraft_pk = main_component.aircraft_attached.pk  # Get the Aircraft's PK
            messages.success(self.request, 'Main Component edited successfully.')
            return redirect('aircraft_main_components_list', pk=aircraft_pk)


@login_required
def add_aircraft_sub_component(request, main_component_id):
    main_component = get_object_or_404(AircraftMainComponent, pk=main_component_id)
    aircraft = main_component.aircraft_attached

    if request.method == 'POST':
        form = AircraftSubComponentForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('multiple_entries'):
                serial_numbers = form.cleaned_data['serial_numbers']  # Assuming this is already a list
                num_created = 0
                with transaction.atomic():
                    for serial_number in serial_numbers:
                        sub_component = AircraftSubComponent()
                        for field in form.cleaned_data:
                            if field not in ['multiple_entries', 'serial_numbers']:
                                setattr(sub_component, field, form.cleaned_data[field])
                        sub_component.parent_component = main_component
                        sub_component.added_by = request.user
                        sub_component.serial_number = serial_number.strip()  # Clean serial number
                        sub_component.save()
                        num_created += 1
                messages.success(request, f'{num_created} Sub Components Added Successfully')
            else:
                sub_component = form.save(commit=False)
                sub_component.parent_component = main_component
                sub_component.added_by = request.user
                sub_component.save()
                messages.success(request, 'Sub Component Added Successfully')
            return redirect('aircraft_sub_components_list', pk=main_component.id)
    else:
        form = AircraftSubComponentForm()

    return render(request, 'maintenance/sub_component/sub_component_add.html',
                  {'form': form, 'main_component': main_component, 'aircraft': aircraft})


class SubComponentListView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/sub_component/sub_component_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_term = self.request.GET.get('search', '')
        min_hours = int(self.request.GET.get('min_hours', '0')) if self.request.GET.get('min_hours') else None
        max_hours = int(self.request.GET.get('max_hours', '0')) if self.request.GET.get('max_hours') else None
        main_component_id = self.kwargs['pk']
        main_component = get_object_or_404(AircraftMainComponent, pk=main_component_id)

        # Only get subcomponents of the given main component
        sub_components = AircraftSubComponent.objects.filter(parent_component=main_component)
        total_sub_components = sub_components.count()

        search_fields = [
            'component_name',
            'parent_component__component_name',
            'parent_component__aircraft_attached__abbreviation'
        ]

        query = Q()
        for field in search_fields:
            query |= Q(**{f'{field}__icontains': search_term})

        sub_components = sub_components.filter(
            query
        )

        if min_hours is not None:
            sub_components = sub_components.filter(maintenance_hours__gte=min_hours)
        if max_hours is not None:
            sub_components = sub_components.filter(maintenance_hours__lte=max_hours)

        paginator = Paginator(sub_components, 50)  # Show 50 subcomponents per page.
        page = self.request.GET.get('page')
        try:
            sub_components = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            sub_components = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            sub_components = paginator.page(paginator.num_pages)

        table = SubComponentTable(sub_components)
        RequestConfig(self.request).configure(table)
        model_name = 'AircraftMainComponent'
        context['model_name'] = model_name
        context['table'] = table
        context['component'] = main_component
        context['total_components'] = total_sub_components
        return context


class SubComponentUpdateView(LoginRequiredMixin, UpdateView):
    model = AircraftSubComponent
    template_name = 'maintenance/sub_component/sub_component_edit.html'
    context_object_name = 'sub_component'
    form_class = AircraftSubComponentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = True  # Indicate that this is an update operation
        return kwargs

    def form_valid(self, form):
        if form.is_valid():
            sub_component = form.save()
            parent_component_pk = sub_component.parent_component.pk
            messages.success(self.request, 'Sub Component Edited successfully.')
            return redirect('aircraft_sub_components_list', pk=parent_component_pk)


class FlightTechLogCreateView(LoginRequiredMixin, View):
    template_name = 'maintenance/techlogs/flight_techlog_add.html'

    def get(self, request, registration_number):
        aircraft = Aircraft.objects.get(registration_number=registration_number)
        flights_on_trip = Flight.objects.filter(aircraft=aircraft, flight_status='OnTrip')
        form = FlightTechLogForm(flights_on_trip=flights_on_trip)  # Pass the queryset to the form
        return render(request, self.template_name, {'form': form, 'aircraft_name': aircraft.abbreviation})

    def post(self, request, registration_number):
        form = FlightTechLogForm(request.POST, flights_on_trip=Flight.objects.filter(
            aircraft__registration_number=registration_number, flight_status='OnTrip'))
        if form.is_valid():
            flight_tech_log = form.save(commit=False)
            flight = form.cleaned_data['flight_leg']
            total_flight_time = flight_tech_log.landing - flight_tech_log.takeoff
            # Convert timedelta to hours
            total_flight_time_hours = Decimal(total_flight_time.total_seconds()) / Decimal(3600)
            flight_tech_log.flight_time = total_flight_time

            # Update maintenance hours for associated components
            main_components = flight.aircraft.aircraftmaincomponent_set.filter(maintenance_status='Attached')
            sub_components = AircraftSubComponent.objects.filter(
                parent_component__in=main_components, maintenance_status='Attached')
            sub2_components = AircraftSub2Component.objects.filter(
                parent_sub_component__parent_component__in=main_components, maintenance_status='Attached')
            sub3_components = AircraftSub3Component.objects.filter(
                parent_sub2_component__parent_sub_component__parent_component__in=main_components,
                maintenance_status='Attached')

            for component in main_components:
                component.maintenance_hours -= total_flight_time_hours
                if component.item_cycle is not None:
                    cycle_count = int(component.item_cycle)
                    cycle_count += 1
                    component.item_cycle = cycle_count
                else:
                    component.item_cycle = 1  # Set to 1 if it's somehow None
                component.save()

            for component in sub_components:
                component.maintenance_hours -= total_flight_time_hours
                if component.item_cycle is not None:
                    cycle_count = int(component.item_cycle)
                    cycle_count += 1
                    component.item_cycle = cycle_count
                else:
                    component.item_cycle = 1
                component.save()
            for component in sub2_components:
                component.maintenance_hours -= total_flight_time_hours
                if component.item_cycle is not None:
                    cycle_count = int(component.item_cycle)
                    cycle_count += 1
                    component.item_cycle = cycle_count
                else:
                    component.item_cycle = 1
                component.save()
            for component in sub3_components:
                component.maintenance_hours -= total_flight_time_hours
                if component.item_cycle is not None:
                    cycle_count = int(component.item_cycle)
                    cycle_count += 1
                    component.item_cycle = cycle_count
                else:
                    component.item_cycle = 1
                component.save()

            # Update attached flight status
            flight.flight_status = 'Completed'
            flight.tech_log = 'Completed'
            flight.updated_date = timezone.now()
            flight.updated_by = request.user.username
            flight_tech_log.added_by = request.user
            flight_tech_log.aircraft = flight_tech_log.flight_leg.aircraft
            flight_tech_log.save()
            flight.save()
            messages.success(request, 'Flight tech log Completed successfully.')
            return redirect('aircraft_detail', registration_number=registration_number)

        return render(request, self.template_name, {'form': form})


# tech log list
class AircraftMaintenanceTechLogListView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/techlogs/maintenance_techlog_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Retrieve filter parameters from the request
        aircraft_id = self.request.GET.get('aircraft', '')
        arrival_date_from = self.request.GET.get('arrival_date_from', '')
        arrival_date_to = self.request.GET.get('arrival_date_to', '')

        # Build the queryset based on filters
        maintenance_tech_logs = AircraftMaintenanceTechLog.objects.all()
        if aircraft_id:
            maintenance_tech_logs = maintenance_tech_logs.filter(aircraft__id=aircraft_id)
        if arrival_date_from:
            maintenance_tech_logs = maintenance_tech_logs.filter(arrival_date__gte=arrival_date_from)
        if arrival_date_to:
            maintenance_tech_logs = maintenance_tech_logs.filter(arrival_date__lte=arrival_date_to)

        # Pagination and table configuration
        paginator = Paginator(maintenance_tech_logs, 50)  # Adjust the number per page as needed
        page = self.request.GET.get('page')
        try:
            maintenance_tech_logs = paginator.page(page)
        except PageNotAnInteger:
            maintenance_tech_logs = paginator.page(1)
        except EmptyPage:
            maintenance_tech_logs = paginator.page(paginator.num_pages)

        table = AircraftMaintenanceTechLogTable(maintenance_tech_logs)
        RequestConfig(self.request).configure(table)

        context['table'] = table
        return context


class FlightTechLogListView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/techlogs/flight_techlog_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flight_list = Flight.objects.filter(tech_log='Pending')

        # Retrieve filter parameters from the request
        flight_leg = self.request.GET.get('flight_leg', '')
        aircraft_id = self.request.GET.get('aircraft', '')
        departure_airport = self.request.GET.get('departure_airport', '')
        departure_from = self.request.GET.get('departure_from', '')
        departure_to = self.request.GET.get('departure_to', '')

        # Build the queryset based on filters
        flight_tech_logs = FlightTechLog.objects.all()
        if flight_leg:
            flight_tech_logs = flight_tech_logs.filter(flight_leg__id=flight_leg)
        if aircraft_id:
            flight_tech_logs = flight_tech_logs.filter(aircraft__id=aircraft_id)
        if departure_airport:
            flight_tech_logs = flight_tech_logs.filter(departure_airport__icontains=departure_airport)
        if departure_from:
            flight_tech_logs = flight_tech_logs.filter(departure_date__gte=departure_from)
        if departure_to:
            flight_tech_logs = flight_tech_logs.filter(departure_date__lte=departure_to)

        # Get distinct aircraft that are in the filtered flight_tech_logs
        aircraft_ids = flight_tech_logs.values_list('aircraft', flat=True).distinct()
        aircrafts = Aircraft.objects.filter(id__in=aircraft_ids)

        # Pagination and table configuration
        paginator = Paginator(flight_tech_logs, 50)
        flight_paginator = Paginator(flight_list, 50)
        flight_page = self.request.GET.get('page')
        page = self.request.GET.get('page')
        try:
            flight_tech_logs_page = paginator.page(page)
        except PageNotAnInteger:
            flight_tech_logs_page = paginator.page(1)
        except EmptyPage:
            flight_tech_logs_page = paginator.page(paginator.num_pages)

        table = FlightTechLogTable(flight_tech_logs_page)
        RequestConfig(self.request).configure(table)

        # Filters for FlightTablePendingTechlog
        flight_number_filter = self.request.GET.get('flight_number', '')
        origin_filter = self.request.GET.get('origin', '')
        flight_booking_reference_filter = self.request.GET.get('flight_booking_reference', '')
        departure_from_filter = self.request.GET.get('departure_from_flight', '')
        departure_to_filter = self.request.GET.get('departure_to_flight', '')

        # Build the queryset for FlightTablePendingTechlog
        pending_flights = Flight.objects.filter(tech_log='Pending')
        if flight_number_filter:
            pending_flights = pending_flights.filter(flight_number__icontains=flight_number_filter)
        if origin_filter:
            pending_flights = pending_flights.filter(origin__icontains=origin_filter)
        if flight_booking_reference_filter:
            pending_flights = pending_flights.filter(
                flight_booking_reference__icontains=flight_booking_reference_filter)
        if departure_from_filter:
            pending_flights = pending_flights.filter(departure_time__gte=departure_from_filter)
        if departure_to_filter:
            pending_flights = pending_flights.filter(departure_time__lte=departure_to_filter)

        # Pagination for FlightTablePendingTechlog
        pending_flight_paginator = Paginator(pending_flights, 50)
        pending_flight_page = self.request.GET.get('pending_flight_page')
        try:
            pending_flights = pending_flight_paginator.page(pending_flight_page)
        except PageNotAnInteger:
            pending_flights = pending_flight_paginator.page(1)
        except EmptyPage:
            pending_flights = pending_flight_paginator.page(pending_flight_paginator.num_pages)

        # Create tables
        table = FlightTechLogTable(flight_tech_logs_page)
        pending_flight_table = FlightTablePendingTechlog(pending_flights)

        # Configure tables
        RequestConfig(self.request).configure(table)
        RequestConfig(self.request).configure(pending_flight_table)

        context.update({
            'flight_leg': flight_leg,
            'aircrafts': aircrafts,
            'table': table,
            'pending_flight_table': pending_flight_table,
            # Add filter parameters for pending flights to context
            'flight_number_filter': flight_number_filter,
            'origin_filter': origin_filter,
            'flight_booking_reference_filter': flight_booking_reference_filter,
            'departure_from_filter': departure_from_filter,
            'departure_to_filter': departure_to_filter,
        })
        return context


def create_aircraft_maintenance_techlog(request):
    if request.method == 'POST':
        form = AircraftMaintenanceTechLogForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aircraft maintenance tech log added successfully.')
            return redirect('aircraft_maintenance_techlog_list')  # Replace with your list view's URL name
    else:
        form = AircraftMaintenanceTechLogForm()
    return render(request, 'maintenance/techlogs/maintenance_techlog_add.html', {'form': form})


class AircraftMaintenanceTechLogUpdateView(LoginRequiredMixin, UpdateView):
    model = AircraftMaintenanceTechLog
    form_class = AircraftMaintenanceTechLogForm
    template_name = 'maintenance/techlogs/maintenance_techlog_edit.html'
    success_url = reverse_lazy('aircraft_maintenance_techlog_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        techlog = form.save(commit=False)
        techlog.updated_by = self.request.user.username  # Assuming username is the field you want
        techlog.updated_date = timezone.now()
        # Get update_comments from request.POST
        techlog.update_comments = self.request.POST.get('update_comments', '')
        techlog.save()
        return HttpResponseRedirect(self.get_success_url())


class AircraftMaintenanceTechLogDetailView(LoginRequiredMixin, DetailView):
    model = AircraftMaintenanceTechLog
    template_name = 'maintenance/maintenance_techlog_details.html'
    context_object_name = 'maintenance_techlog'


@login_required
def clone_component_generic2(request, model_name, instance_id):
    ModelClass = apps.get_model('maintenance', model_name)
    original_component = get_object_or_404(ModelClass, pk=instance_id)

    if request.method == 'POST':
        form = CloneComponentForm(request.POST)
        if form.is_valid():
            serial_numbers = form.cleaned_data['serial_numbers'].replace(',', '\n').split('\n')
            serial_numbers = [sn.strip() for sn in serial_numbers if sn.strip()]  # Clean and filter empty values

            with transaction.atomic():
                for serial_number in serial_numbers:
                    cloned_component = ModelClass.objects.get(pk=original_component.pk)
                    cloned_component.pk = None  # Remove primary key to create a new instance
                    cloned_component.serial_number = serial_number
                    # Handle any foreign key relationships here if necessary
                    cloned_component.save()

            messages.success(request, 'Components cloned successfully.')
            return redirect('list_aircraft')
    else:
        form = CloneComponentForm()

    return render(request, 'maintenance/clone/clone_component.html', {
        'form': form,
        'original_component': original_component
    })


@login_required
def clone_component_generic(request, model_name, instance_id):
    ModelClass = apps.get_model('maintenance', model_name)  # Replace 'your_app_name' with your actual app name
    original_component = get_object_or_404(ModelClass, pk=instance_id)

    if request.method == 'POST':
        form = CloneComponentForm(request.POST)
        if form.is_valid():
            serial_numbers = form.cleaned_data['serial_numbers'].replace(',', '\n').split('\n')
            serial_numbers = [sn.strip() for sn in serial_numbers if sn.strip()]  # Clean and filter empty values

            try:
                with transaction.atomic():
                    for serial_number in serial_numbers:
                        cloned_component = ModelClass.objects.get(pk=original_component.pk)
                        cloned_component.pk = None  # Remove primary key to create a new instance
                        cloned_component.serial_number = serial_number
                        cloned_component.save()
                messages.success(request, 'Components cloned successfully.')
                return_path = request.session.get('return_path', reverse('list_aircraft'))
                request.session.pop('return_path', None)
                return HttpResponseRedirect(return_path)
            except IntegrityError as e:
                messages.error(request,
                               'An error occurred while cloning the component. Please ensure the serial numbers are unique.')
            except Exception as e:
                # Log the error or handle it as appropriate
                messages.error(request, 'An unexpected error occurred. Please try again.')
    else:
        form = CloneComponentForm()

    return render(request, 'maintenance/clone/clone_component.html', {
        'form': form,
        'original_component': original_component
    })


def bluky_import_aircraft_components(request, registration_number):
    slug_field = 'registration_number'
    return render(request, 'maintenance/clone/import_component.html')


def get_component_tree(component, level=0):
    # Base information for any component
    component_info = {
        'level': level,
        'component_name': component.component_name,
        'serial_number': component.serial_number,
        'children': []
    }

    # Depending on the type, fetch the appropriate subcomponents
    if isinstance(component, AircraftMainComponent):
        sub_components = AircraftSubComponent.objects.filter(parent_component=component)
    elif isinstance(component, AircraftSubComponent):
        sub_components = AircraftSub2Component.objects.filter(parent_sub_component=component)
    elif isinstance(component, AircraftSub2Component):
        sub_components = AircraftSub3Component.objects.filter(parent_sub2_component=component)
    else:
        # No further nesting, so return the current component info
        return component_info

    # Recursively fetch and append child components
    for sub_component in sub_components:
        component_info['children'].append(get_component_tree(sub_component, level=level + 1))

    return component_info


def component_tree_view(request):
    main_component = AircraftMainComponent.objects.get(pk=5)  # Adjust the pk accordingly
    tree = get_component_tree(main_component)
    return render(request, 'maintenance/main_component/components_tree.html', {'tree': tree})


# ===================================================================
# COMPLETE MAINTENANCE SCHEDULING VIEWS, Manaul Maintenance View
# =====================================================================
class ComponentMaintenanceListView(LoginRequiredMixin, ListView):
    """
    FIXED: Proper status classification
    - Scheduled: Future maintenances (start_date > now)
    - Expired: Past due but not completed
    - Completed: Actually marked as completed
    """
    model = ComponentMaintenance
    template_name = 'maintenance/schedule/component_maintenance_list.html'
    context_object_name = 'maintenance_schedules'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get filter parameters
        status = self.request.GET.get('status', 'scheduled')
        aircraft_id = self.request.GET.get('aircraft')
        component_level = self.request.GET.get('component_level')
        batch_id = self.request.GET.get('batch_id')
        maintenance_type = self.request.GET.get('maintenance_type')
        schedule_type = self.request.GET.get('schedule_type')
        start_date_from = self.request.GET.get('start_date_from')
        start_date_to = self.request.GET.get('start_date_to')
        search_term = self.request.GET.get('search_term')

        # CRITICAL FIX: Use maintenance_status field explicitly
        now = timezone.now()

        if status == 'scheduled':
            # FIXED: Only future schedules that haven't been completed
            queryset = queryset.filter(
                start_date__gt=now,
                maintenance_status='Scheduled'
            )
        elif status == 'expired':
            # FIXED: Past due but NOT completed
            queryset = queryset.filter(
                end_date__lt=now,
                maintenance_status='Scheduled'
            )
        elif status == 'completed':
            # FIXED: Only records explicitly marked as completed
            queryset = queryset.filter(maintenance_status='Completed')

        # Apply other filters
        if aircraft_id:
            queryset = self._filter_by_aircraft(queryset, aircraft_id)

        if component_level:
            try:
                ct = ContentType.objects.get(model=component_level)
                queryset = queryset.filter(content_type=ct)
            except ContentType.DoesNotExist:
                pass

        if batch_id:
            queryset = queryset.filter(
                Q(update_comments__icontains=f'Batch: {batch_id}') |
                Q(update_comments__icontains=f'Single: {batch_id}') |
                Q(update_comments__icontains=f'Auto: {batch_id}')
            )

        if maintenance_type:
            queryset = queryset.filter(maintenance_type=maintenance_type)

        if schedule_type:
            queryset = queryset.filter(main_type_schedule=schedule_type)

        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)

        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)

        if search_term:
            queryset = queryset.filter(
                Q(remarks__icontains=search_term) |
                Q(completion_remarks__icontains=search_term)
            )

        return queryset.order_by('-start_date')

    def _filter_by_aircraft(self, queryset, aircraft_id):
        """Filter maintenance records by aircraft"""
        filtered_ids = []

        for maintenance in queryset:
            component = maintenance.component_to_maintain
            aircraft = None

            if hasattr(component, 'aircraft_attached'):
                aircraft = component.aircraft_attached
            elif hasattr(component, 'parent_component'):
                aircraft = component.parent_component.aircraft_attached
            elif hasattr(component, 'parent_sub_component'):
                aircraft = component.parent_sub_component.parent_component.aircraft_attached
            elif hasattr(component, 'parent_sub2_component'):
                aircraft = component.parent_sub2_component.parent_sub_component.parent_component.aircraft_attached

            if aircraft and str(aircraft.id) == aircraft_id:
                filtered_ids.append(maintenance.id)

        return queryset.filter(id__in=filtered_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aircrafts'] = Aircraft.objects.all()
        context['status'] = self.request.GET.get('status', 'scheduled')

        # FIXED: Accurate counts
        now = timezone.now()

        context['scheduled_count'] = ComponentMaintenance.objects.filter(
            start_date__gt=now,
            maintenance_status='Scheduled'
        ).count()

        context['expired_count'] = ComponentMaintenance.objects.filter(
            end_date__lt=now,
            maintenance_status='Scheduled'
        ).count()

        context['completed_count'] = ComponentMaintenance.objects.filter(
            maintenance_status='Completed'
        ).count()

        # Get batch IDs for filter
        batch_ids = set()
        for m in ComponentMaintenance.objects.all():
            if m.update_comments:
                for prefix in ['Batch: MAINT-', 'Single: MAINT-', 'Auto: MAINT-']:
                    if prefix in m.update_comments:
                        batch_ids.add(m.update_comments.split(prefix)[1].split()[0])

        context['batch_ids'] = sorted(batch_ids, reverse=True)

        return context


@login_required
def search_components_ajax(request):
    """AJAX endpoint to search components by aircraft, level, and search term"""
    aircraft_id = request.GET.get('aircraft_id')
    component_level = request.GET.get('component_level')
    search_term = request.GET.get('search_term', '').strip()

    if not aircraft_id or not component_level:
        return JsonResponse({'results': []})

    # Map component level to model class
    model_map = {
        'aircraftmaincomponent': AircraftMainComponent,
        'aircraftsubcomponent': AircraftSubComponent,
        'aircraftsub2component': AircraftSub2Component,
        'aircraftsub3component': AircraftSub3Component,
    }

    model_class = model_map.get(component_level)
    if not model_class:
        return JsonResponse({'results': []})

    # Build query based on component level
    if component_level == 'aircraftmaincomponent':
        queryset = model_class.objects.filter(aircraft_attached_id=aircraft_id)
    elif component_level == 'aircraftsubcomponent':
        queryset = model_class.objects.filter(
            parent_component__aircraft_attached_id=aircraft_id
        )
    elif component_level == 'aircraftsub2component':
        queryset = model_class.objects.filter(
            parent_sub_component__parent_component__aircraft_attached_id=aircraft_id
        )
    else:  # aircraftsub3component
        queryset = model_class.objects.filter(
            parent_sub2_component__parent_sub_component__parent_component__aircraft_attached_id=aircraft_id
        )

    # Only show attached components
    queryset = queryset.filter(component_status='Attached')

    # Apply search filter
    if search_term:
        queryset = queryset.filter(
            Q(component_name__icontains=search_term) |
            Q(serial_number__icontains=search_term) |
            Q(part_number__icontains=search_term)
        )

    # Limit results
    queryset = queryset[:20]

    # Format results
    results = []
    content_type = ContentType.objects.get_for_model(model_class)

    for component in queryset:
        results.append({
            'id': component.id,
            'content_type_id': content_type.id,
            'text': f"{component.component_name} - S/N: {component.serial_number} (Hours: {component.maintenance_hours})",
            'component_name': component.component_name,
            'serial_number': component.serial_number,
            'maintenance_hours': str(component.maintenance_hours),
            'part_number': component.part_number
        })

    return JsonResponse({'results': results})


# ===================================================================
# FIX 2 & 3: ComponentMaintenanceCreateView - BATCH SUPPORT + NO COMPLETION FIELDS
# ===================================================================

class ComponentMaintenanceCreateView(LoginRequiredMixin, CreateView):
    """
    FIXED: 
    - Removed completion fields from form
    - Added batch support (multiple component selection)
    """
    model = ComponentMaintenance
    template_name = 'maintenance/schedule/maintenance_form.html'
    success_url = reverse_lazy('component_maintenance_list')

    # FIXED: Only scheduling fields
    fields = ['main_type_schedule', 'maintenance_type', 'start_date', 'end_date']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Add CSS classes and datetime widgets
        for field_name, field in form.fields.items():
            field.widget.attrs['class'] = 'form-control'

        form.fields['start_date'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        )
        form.fields['end_date'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        )

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aircrafts'] = Aircraft.objects.all()
        return context

    def form_valid(self, form):
        """
        FIXED: Handle batch creation from multiple selected components
        """
        # Get selected components (BATCH SUPPORT)
        selected_component_ids = self.request.POST.getlist('selected_components')

        if not selected_component_ids:
            messages.error(self.request, 'Please select at least one component.')
            return self.form_invalid(form)

        # Get component type and aircraft
        component_type = self.request.POST.get('component_type')
        aircraft_id = self.request.POST.get('aircraft')

        if not component_type or not aircraft_id:
            messages.error(self.request, 'Missing aircraft or component type.')
            return self.form_invalid(form)

        # Map to model class
        model_map = {
            'aircraftmaincomponent': AircraftMainComponent,
            'aircraftsubcomponent': AircraftSubComponent,
            'aircraftsub2component': AircraftSub2Component,
            'aircraftsub3component': AircraftSub3Component,
        }

        model_class = model_map.get(component_type)
        if not model_class:
            messages.error(self.request, 'Invalid component type')
            return self.form_invalid(form)

        # Generate batch ID
        batch_id = self.generate_batch_id()
        is_batch = len(selected_component_ids) > 1

        # Get content type
        content_type = ContentType.objects.get_for_model(model_class)

        # Create maintenance records
        created_count = 0

        try:
            with transaction.atomic():
                for component_id in selected_component_ids:
                    component = get_object_or_404(model_class, pk=component_id)

                    ComponentMaintenance.objects.create(
                        content_type=content_type,
                        object_id=component_id,
                        main_type_schedule=form.cleaned_data['main_type_schedule'],
                        maintenance_type=form.cleaned_data['maintenance_type'],
                        maintenance_hours=component.maintenance_hours,
                        maintenance_hours_added=0,  # FIXED: Default to 0
                        start_date=form.cleaned_data['start_date'],
                        end_date=form.cleaned_data['end_date'],
                        remarks='Pending completion sign-off',  # FIXED: Placeholder
                        added_by=self.request.user,
                        maintenance_status='Scheduled',  # FIXED: Explicit status
                        update_comments=f'Batch: {batch_id}' if is_batch else f'Single: {batch_id}'
                    )
                    created_count += 1

            if is_batch:
                messages.success(
                    self.request,
                    f'✓ Batch scheduled for {created_count} components. Batch ID: {batch_id}'
                )
            else:
                messages.success(
                    self.request,
                    f'✓ Maintenance scheduled. ID: {batch_id}'
                )

            return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f'Error: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors.')
        return super().form_invalid(form)

    @staticmethod
    def generate_batch_id():
        """Generate unique batch ID"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f'MAINT-{timestamp}-{random_suffix}'


# ============================================================================
# COMPONENT MAINTENANCE VIEWS
# ============================================================================

class ComponentMaintenanceCreateView(LoginRequiredMixin, CreateView):
    """Create view for scheduling component maintenance"""
    model = ComponentMaintenance
    form_class = ComponentMaintenanceForm
    template_name = 'maintenance/schedule/maintenance_form.html'
    success_url = reverse_lazy('component_maintenance_list')

    def form_valid(self, form):
        form.instance.added_by = self.request.user
        messages.success(self.request, 'Component maintenance scheduled successfully.')
        return super().form_valid(form)


class ComponentMaintenanceUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update scheduled maintenances
    """
    model = ComponentMaintenance
    template_name = 'maintenance/schedule/component_maintenance_update.html'
    fields = ['main_type_schedule', 'maintenance_type', 'start_date', 'end_date']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, field in form.fields.items():
            field.widget.attrs['class'] = 'form-control'

        form.fields['start_date'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        )
        form.fields['end_date'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        )

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        maintenance = self.object
        component = maintenance.component_to_maintain

        context['component'] = component

        # Get aircraft
        if hasattr(component, 'aircraft_attached'):
            context['aircraft'] = component.aircraft_attached
        elif hasattr(component, 'parent_component'):
            context['aircraft'] = component.parent_component.aircraft_attached
        elif hasattr(component, 'parent_sub_component'):
            context['aircraft'] = component.parent_sub_component.parent_component.aircraft_attached
        elif hasattr(component, 'parent_sub2_component'):
            context[
                'aircraft'] = component.parent_sub2_component.parent_sub_component.parent_component.aircraft_attached

        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user.username
        form.instance.updated_date = timezone.now()

        messages.success(self.request, 'Schedule updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('component_maintenance_detail', kwargs={'pk': self.object.pk})


# ===================================================================
# ComponentMaintenanceDetailView - NO CHANGES NEEDED
# ===================================================================

class ComponentMaintenanceDetailView(LoginRequiredMixin, DetailView):
    """Detail view for component maintenance"""
    model = ComponentMaintenance
    template_name = 'maintenance/schedule/component_maintenance_detail.html'
    context_object_name = 'maintenance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        maintenance = self.object

        component = maintenance.component_to_maintain
        context['component'] = component
        context['component_details'] = maintenance.get_component_details()
        context['now'] = timezone.now()

        # Check if part of batch
        if maintenance.update_comments:
            if 'Batch: MAINT-' in maintenance.update_comments:
                batch_id = maintenance.update_comments.split('Batch: ')[1].split()[0]
                context['is_batch'] = True
                context['batch_id'] = batch_id
                context['batch_records'] = ComponentMaintenance.objects.filter(
                    update_comments__icontains=f'Batch: {batch_id}'
                ).exclude(pk=maintenance.pk)
            else:
                context['is_batch'] = False

        # Get aircraft
        if hasattr(component, 'aircraft_attached'):
            context['aircraft'] = component.aircraft_attached
        elif hasattr(component, 'parent_component'):
            context['aircraft'] = component.parent_component.aircraft_attached
        elif hasattr(component, 'parent_sub_component'):
            context['aircraft'] = component.parent_sub_component.parent_component.aircraft_attached
        elif hasattr(component, 'parent_sub2_component'):
            context[
                'aircraft'] = component.parent_sub2_component.parent_sub_component.parent_component.aircraft_attached

        return context


class ComponentMaintenanceDetailView(LoginRequiredMixin, DetailView):
    """Detail view for component maintenance"""
    model = ComponentMaintenance
    template_name = 'maintenance/schedule/maintenance_detail.html'
    context_object_name = 'maintenance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        maintenance = self.object

        # Get component details
        component = maintenance.component_to_maintain
        context['component'] = component
        context['component_details'] = maintenance.get_component_details()
        context['now'] = timezone.now()

        # Get aircraft
        if hasattr(component, 'aircraft_attached'):
            context['aircraft'] = component.aircraft_attached
        elif hasattr(component, 'parent_component'):
            context['aircraft'] = component.parent_component.aircraft_attached
        elif hasattr(component, 'parent_sub_component'):
            context['aircraft'] = component.parent_sub_component.parent_component.aircraft_attached
        elif hasattr(component, 'parent_sub2_component'):
            context[
                'aircraft'] = component.parent_sub2_component.parent_sub_component.parent_component.aircraft_attached

        return context


# ============================================================================
# CONFIRMATION ACTIONS
# ============================================================================

@login_required
def confirm_component_maintenance(request, pk):
    """
    Confirm a scheduled maintenance and update component hours.
    This is called when a single maintenance is confirmed.
    """
    maintenance = get_object_or_404(ComponentMaintenance, pk=pk)
    component = maintenance.component_to_maintain

    if request.method == 'POST':
        # Update component maintenance hours
        component.maintenance_hours += maintenance.maintenance_hours_added
        component.updated_by = request.user.username
        component.updated_date = timezone.now()

        # If component was in maintenance status, return to operational
        if component.component_status == 'Maintenance':
            component.component_status = 'Attached'
        if component.maintenance_status == 'Maintenance':
            component.maintenance_status = 'Operational'

        component.save()

        # Update maintenance status
        maintenance.main_type_schedule = 'Operational'
        maintenance.updated_by = request.user.username
        maintenance.updated_date = timezone.now()

        # Add confirmation notes if provided
        confirmation_notes = request.POST.get('confirmation_notes', '')
        if confirmation_notes:
            maintenance.remarks += f"\n\nConfirmation Notes ({timezone.now().strftime('%Y-%m-%d %H:%M')} by {request.user.username}): {confirmation_notes}"

        maintenance.save()

        messages.success(
            request,
            f'Maintenance confirmed! {component.component_name} hours updated: {component.maintenance_hours - maintenance.maintenance_hours_added} → {component.maintenance_hours} (+{maintenance.maintenance_hours_added} hours)'
        )
        return redirect('component_maintenance_list')

    return render(request, 'maintenance/schedule/maintenance_confirm.html', {
        'maintenance': maintenance,
        'component': component
    })


@login_required
def bulk_confirm_maintenances(request):
    """
    Bulk confirm multiple scheduled maintenances.
    Updates all selected components and moves maintenances to historical.
    """
    if request.method == 'POST':
        form = BulkComponentMaintenanceConfirmForm(request.POST)
        if form.is_valid():
            maintenance_ids = form.cleaned_data['maintenance_ids']
            confirmation_notes = form.cleaned_data.get('confirmation_notes', '')

            confirmed_count = 0
            failed_count = 0

            for maintenance_id in maintenance_ids:
                try:
                    maintenance = ComponentMaintenance.objects.get(pk=maintenance_id)
                    component = maintenance.component_to_maintain

                    # Update component hours
                    component.maintenance_hours += maintenance.maintenance_hours_added
                    component.updated_by = request.user.username
                    component.updated_date = timezone.now()

                    # Update component status if in maintenance
                    if component.component_status == 'Maintenance':
                        component.component_status = 'Attached'
                    if component.maintenance_status == 'Maintenance':
                        component.maintenance_status = 'Operational'

                    component.save()

                    # Update maintenance status
                    maintenance.main_type_schedule = 'Operational'
                    maintenance.updated_by = request.user.username
                    maintenance.updated_date = timezone.now()

                    if confirmation_notes:
                        maintenance.remarks += f"\n\nBulk Confirmation ({timezone.now().strftime('%Y-%m-%d %H:%M')} by {request.user.username}): {confirmation_notes}"

                    maintenance.save()
                    confirmed_count += 1

                except ComponentMaintenance.DoesNotExist:
                    failed_count += 1
                    continue
                except Exception as e:
                    failed_count += 1
                    messages.warning(request, f'Failed to confirm maintenance ID {maintenance_id}: {str(e)}')
                    continue

            if confirmed_count > 0:
                messages.success(request, f'Successfully confirmed {confirmed_count} maintenance schedule(s).')

            if failed_count > 0:
                messages.warning(request, f'{failed_count} maintenance(s) could not be confirmed.')

            return redirect('component_maintenance_list')

    return redirect('component_maintenance_list')


# ===================================================================
# AIRCRAFT MAINTENANCE VIEWS
# ===================================================================

class AircraftMaintenanceListView(LoginRequiredMixin, ListView):
    model = AircraftMaintenance
    template_name = 'maintenance/schedule/aircraft_maintenance_list.html'
    context_object_name = 'maintenance_schedules'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        aircraft_id = self.request.GET.get('aircraft')
        maintenance_type = self.request.GET.get('maintenance_type')
        schedule_type = self.request.GET.get('schedule_type')
        start_date_from = self.request.GET.get('start_date_from')
        start_date_to = self.request.GET.get('start_date_to')
        search_term = self.request.GET.get('search_term')

        if aircraft_id:
            queryset = queryset.filter(aircraft_to_maintain_id=aircraft_id)
        if maintenance_type:
            queryset = queryset.filter(maintenance_type=maintenance_type)
        if schedule_type:
            queryset = queryset.filter(main_type_schedule=schedule_type)
        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)
        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)
        if search_term:
            queryset = queryset.filter(
                Q(aircraft_to_maintain__abbreviation__icontains=search_term) |
                Q(aircraft_to_maintain__registration_number__icontains=search_term) |
                Q(remarks__icontains=search_term)
            )

        return queryset.order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aircrafts'] = Aircraft.objects.all()
        return context


class AircraftMaintenanceCreateView(LoginRequiredMixin, CreateView):
    model = AircraftMaintenance
    template_name = 'maintenance/schedule/aircraft_maintenance_form.html'
    success_url = reverse_lazy('aircraft_maintenance_list')
    fields = ['aircraft_to_maintain', 'main_type_schedule', 'maintenance_type',
              'maintenance_hours', 'maintenance_hours_added', 'start_date',
              'end_date', 'next_maintenance_date', 'remarks', 'maintenance_report']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, field in form.fields.items():
            field.widget.attrs['class'] = 'form-control'
        form.fields['start_date'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'})
        form.fields['end_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        if 'next_maintenance_date' in form.fields:
            form.fields['next_maintenance_date'].widget = forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'})
        form.fields['maintenance_report'].required = False
        return form

    def form_valid(self, form):
        form.instance.added_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Aircraft maintenance schedule created successfully.')
        return response


class AircraftMaintenanceUpdateView(LoginRequiredMixin, UpdateView):
    model = AircraftMaintenance
    template_name = 'maintenance/schedule/aircraft_maintenance_form.html'
    success_url = reverse_lazy('aircraft_maintenance_list')
    fields = ['aircraft_to_maintain', 'main_type_schedule', 'maintenance_type',
              'maintenance_hours', 'maintenance_hours_added', 'start_date',
              'end_date', 'next_maintenance_date', 'remarks', 'maintenance_report', 'update_comments']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, field in form.fields.items():
            field.widget.attrs['class'] = 'form-control'
        form.fields['start_date'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'})
        form.fields['end_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        if 'next_maintenance_date' in form.fields:
            form.fields['next_maintenance_date'].widget = forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'})
        form.fields['update_comments'].required = True
        return form

    def form_valid(self, form):
        form.instance.updated_by = self.request.user.username
        form.instance.updated_date = timezone.now()
        response = super().form_valid(form)
        messages.success(self.request, 'Aircraft maintenance schedule updated successfully.')
        return response


class AircraftMaintenanceDetailView(LoginRequiredMixin, DetailView):
    model = AircraftMaintenance
    template_name = 'maintenance/schedule/aircraft_maintenance_detail.html'
    context_object_name = 'maintenance'


# ===================================================================
# COMPONENT MAINTENANCE VIEWS
# ===================================================================

# ===================================================================
# COMPLETION/SIGN-OFF VIEWS
# ===================================================================

@login_required
def complete_component_maintenance(request, pk):
    """Sign off / Complete a component maintenance"""
    maintenance = get_object_or_404(ComponentMaintenance, pk=pk)
    component = maintenance.component_to_maintain

    if request.method == 'POST':
        actual_start_date = request.POST.get('actual_start_date')
        actual_end_date = request.POST.get('actual_end_date')
        actual_hours_added = request.POST.get('actual_hours_added', 0)
        completion_remarks = request.POST.get('completion_remarks')
        completion_report = request.FILES.get('completion_report')

        if not actual_end_date or not completion_remarks:
            messages.error(request, 'Please provide completion date and remarks.')
            return redirect('complete_component_maintenance', pk=pk)

        try:
            with transaction.atomic():
                # Update maintenance record (handle both old and new model)
                if hasattr(maintenance, 'maintenance_status'):
                    maintenance.maintenance_status = 'Completed'
                    maintenance.actual_start_date = actual_start_date
                    maintenance.actual_end_date = actual_end_date
                    maintenance.actual_hours_added = actual_hours_added or 0
                    maintenance.completion_date = timezone.now()
                    maintenance.completed_by = request.user
                    maintenance.completion_remarks = completion_remarks
                    if completion_report:
                        maintenance.completion_report = completion_report
                else:
                    # Old model - use update_comments
                    maintenance.maintenance_hours_added = actual_hours_added or 0
                    if not maintenance.update_comments:
                        maintenance.update_comments = ''
                    maintenance.update_comments += f'\nCompleted: {timezone.now().strftime("%Y-%m-%d %H:%M")} by {request.user.username}\n{completion_remarks}'

                maintenance.updated_by = request.user.username
                maintenance.updated_date = timezone.now()
                maintenance.save()

                # Add hours back to component
                if float(actual_hours_added) > 0:
                    component.maintenance_hours += Decimal(actual_hours_added)
                    component.updated_by = request.user.username
                    component.updated_date = timezone.now()
                    component.save()

                messages.success(request,
                                 f'✅ Maintenance completed for {component.component_name}. Added {actual_hours_added} hours.')
                return redirect('component_maintenance_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('complete_component_maintenance', pk=pk)

    context = {'maintenance': maintenance, 'component': component}
    return render(request, 'maintenance/schedule/component_maintenance_complete.html', context)


@login_required
def batch_complete_maintenance(request, batch_id):
    """Complete all maintenance in a batch"""
    maintenance_records = ComponentMaintenance.objects.filter(
        Q(update_comments__icontains=f'Batch: {batch_id}') |
        Q(update_comments__icontains=f'Single: {batch_id}')
    )

    if not maintenance_records.exists():
        messages.error(request, f'No records found for batch {batch_id}')
        return redirect('component_maintenance_list')

    if request.method == 'POST':
        actual_end_date = request.POST.get('actual_end_date')
        hours_added = request.POST.get('hours_added', 0)
        completion_remarks = request.POST.get('completion_remarks')
        completion_report = request.FILES.get('completion_report')

        if not actual_end_date or not completion_remarks:
            messages.error(request, 'Please provide completion date and remarks.')
            return redirect('batch_complete_maintenance', batch_id=batch_id)

        try:
            with transaction.atomic():
                completed_count = 0
                for maintenance in maintenance_records:
                    component = maintenance.component_to_maintain

                    if hasattr(maintenance, 'maintenance_status'):
                        maintenance.maintenance_status = 'Completed'
                        maintenance.actual_end_date = actual_end_date
                        maintenance.actual_hours_added = hours_added
                        maintenance.completion_date = timezone.now()
                        maintenance.completed_by = request.user
                        maintenance.completion_remarks = completion_remarks
                        if completed_count == 0 and completion_report:
                            maintenance.completion_report = completion_report
                    else:
                        maintenance.maintenance_hours_added = hours_added
                        if not maintenance.update_comments:
                            maintenance.update_comments = ''
                        maintenance.update_comments += f'\nBatch Completed: {timezone.now().strftime("%Y-%m-%d")} by {request.user.username}'

                    maintenance.save()

                    if float(hours_added) > 0:
                        component.maintenance_hours += Decimal(hours_added)
                        component.updated_by = request.user.username
                        component.updated_date = timezone.now()
                        component.save()

                    completed_count += 1

                messages.success(request,
                                 f'✅ Batch completed! {completed_count} components updated. Added {hours_added} hours to each.')
                return redirect('batch_maintenance_view', batch_id=batch_id)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('batch_complete_maintenance', batch_id=batch_id)

    context = {
        'batch_id': batch_id,
        'maintenance_records': maintenance_records,
        'total_records': maintenance_records.count(),
        'first_record': maintenance_records.first(),
    }
    return render(request, 'maintenance/schedule/batch_complete_maintenance.html', context)


# ===================================================================
# HELPER VIEWS
# ===================================================================

@login_required
def get_components_by_aircraft_and_type(request):
    """AJAX: Get components by aircraft and type"""
    component_type = request.GET.get('component_type')
    aircraft_id = request.GET.get('aircraft_id')

    if not component_type or not aircraft_id:
        return JsonResponse({'success': False, 'components': []})

    try:
        aircraft = Aircraft.objects.get(pk=aircraft_id)
    except Aircraft.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Aircraft not found'})

    try:
        if component_type == 'aircraftmaincomponent':
            components_qs = AircraftMainComponent.objects.filter(aircraft_attached=aircraft)
        elif component_type == 'aircraftsubcomponent':
            components_qs = AircraftSubComponent.objects.filter(parent_component__aircraft_attached=aircraft)
        elif component_type == 'aircraftsub2component':
            components_qs = AircraftSub2Component.objects.filter(
                parent_sub_component__parent_component__aircraft_attached=aircraft)
        elif component_type == 'aircraftsub3component':
            components_qs = AircraftSub3Component.objects.filter(
                parent_sub2_component__parent_sub_component__parent_component__aircraft_attached=aircraft)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid type'})

        components_data = []
        for comp in components_qs:
            needs_maintenance = comp.min_maintenance_hours and comp.maintenance_hours <= comp.min_maintenance_hours
            components_data.append({
                'id': comp.id,
                'name': comp.component_name,
                'serial_number': comp.serial_number,
                'part_number': comp.part_number,
                'maintenance_hours': float(comp.maintenance_hours),
                'min_maintenance_hours': float(comp.min_maintenance_hours) if comp.min_maintenance_hours else None,
                'needs_maintenance': needs_maintenance,
                'component_location': comp.component_location or 'N/A',
            })

        return JsonResponse({
            'success': True,
            'components': components_data,
            'count': len(components_data),
            'aircraft': {'id': aircraft.id, 'name': aircraft.abbreviation}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def batch_maintenance_view(request, batch_id):
    """View all maintenance records in a batch"""
    maintenance_records = ComponentMaintenance.objects.filter(
        Q(update_comments__icontains=f'Batch: {batch_id}') |
        Q(update_comments__icontains=f'Single: {batch_id}') |
        Q(update_comments__icontains=f'Auto: {batch_id}')
    ).order_by('content_type__model', 'object_id')

    if not maintenance_records.exists():
        messages.error(request, f'No records found for batch {batch_id}')
        return redirect('component_maintenance_list')

    grouped_records = {}
    for record in maintenance_records:
        type_name = record.component_type_name
        if type_name not in grouped_records:
            grouped_records[type_name] = []
        grouped_records[type_name].append(record)

    context = {
        'batch_id': batch_id,
        'maintenance_records': maintenance_records,
        'grouped_records': grouped_records,
        'total_records': maintenance_records.count(),
        'first_record': maintenance_records.first(),
    }
    return render(request, 'maintenance/schedule/batch_maintenance_detail.html', context)


@login_required
def quick_schedule_component_maintenance(request, model_name, component_id):
    """Quick schedule from component page"""
    model_map = {
        'aircraftmaincomponent': AircraftMainComponent,
        'aircraftsubcomponent': AircraftSubComponent,
        'aircraftsub2component': AircraftSub2Component,
        'aircraftsub3component': AircraftSub3Component,
    }

    model_class = model_map.get(model_name)
    if not model_class:
        messages.error(request, 'Invalid component type')
        return redirect('list_aircraft')

    component = get_object_or_404(model_class, pk=component_id)

    if request.method == 'POST':
        content_type = ContentType.objects.get_for_model(model_class)
        maintenance_id = generate_batch_id()

        try:
            maintenance = ComponentMaintenance.objects.create(
                content_type=content_type,
                object_id=component_id,
                main_type_schedule=request.POST.get('main_type_schedule'),
                maintenance_type=request.POST.get('maintenance_type'),
                maintenance_hours=component.maintenance_hours,
                maintenance_hours_added=0,
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                remarks=request.POST.get('remarks'),
                added_by=request.user,
                update_comments=f'Single: {maintenance_id}'
            )
            messages.success(request, f'✓ Maintenance scheduled. ID: {maintenance_id}')
            return redirect('component_maintenance_detail', pk=maintenance.pk)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('list_aircraft')

    context = {'component': component, 'model_name': model_name}
    return render(request, 'maintenance/schedule/quick_component_schedule.html', context)


@login_required
def auto_schedule_component_maintenance(request, model_name, component_id):
    """Auto-schedule when critical"""
    model_map = {
        'aircraftmaincomponent': AircraftMainComponent,
        'aircraftsubcomponent': AircraftSubComponent,
        'aircraftsub2component': AircraftSub2Component,
        'aircraftsub3component': AircraftSub3Component,
    }

    model_class = model_map.get(model_name)
    if not model_class:
        return JsonResponse({'success': False, 'error': 'Invalid type'})

    component = get_object_or_404(model_class, pk=component_id)

    if component.min_maintenance_hours and component.maintenance_hours <= component.min_maintenance_hours:
        content_type = ContentType.objects.get_for_model(model_class)
        maintenance_id = generate_batch_id()

        maintenance = ComponentMaintenance.objects.create(
            content_type=content_type,
            object_id=component_id,
            main_type_schedule='Maintenance',
            maintenance_type='Class_A',
            maintenance_hours=component.maintenance_hours,
            maintenance_hours_added=0,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=7),
            remarks=f'🤖 Auto-scheduled at {component.maintenance_hours} hours',
            added_by=request.user,
            update_comments=f'Auto: {maintenance_id}'
        )

        return JsonResponse({'success': True, 'message': f'Auto-scheduled', 'maintenance_id': maintenance.id})

    return JsonResponse({'success': False, 'error': 'Component OK'})


@login_required
def maintenance_dashboard(request):
    """Unified dashboard"""
    aircraft_id = request.GET.get('aircraft')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    aircraft_schedules = AircraftMaintenance.objects.all()
    component_schedules = ComponentMaintenance.objects.all()

    if aircraft_id:
        aircraft_schedules = aircraft_schedules.filter(aircraft_to_maintain_id=aircraft_id)
        aircraft = get_object_or_404(Aircraft, pk=aircraft_id)
        main_components = AircraftMainComponent.objects.filter(aircraft_attached=aircraft)
        sub_components = AircraftSubComponent.objects.filter(parent_component__in=main_components)
        sub2_components = AircraftSub2Component.objects.filter(parent_sub_component__in=sub_components)
        sub3_components = AircraftSub3Component.objects.filter(parent_sub2_component__in=sub2_components)

        q_objects = Q()
        for comp in main_components:
            q_objects |= Q(content_type__model='aircraftmaincomponent', object_id=comp.id)
        for comp in sub_components:
            q_objects |= Q(content_type__model='aircraftsubcomponent', object_id=comp.id)
        for comp in sub2_components:
            q_objects |= Q(content_type__model='aircraftsub2component', object_id=comp.id)
        for comp in sub3_components:
            q_objects |= Q(content_type__model='aircraftsub3component', object_id=comp.id)
        component_schedules = component_schedules.filter(q_objects)

    if date_from:
        aircraft_schedules = aircraft_schedules.filter(start_date__gte=date_from)
        component_schedules = component_schedules.filter(start_date__gte=date_from)
    if date_to:
        aircraft_schedules = aircraft_schedules.filter(start_date__lte=date_to)
        component_schedules = component_schedules.filter(start_date__lte=date_to)

    context = {
        'aircraft_schedules': aircraft_schedules.order_by('-start_date')[:10],
        'component_schedules': component_schedules.order_by('-start_date')[:10],
        'total_aircraft_schedules': aircraft_schedules.count(),
        'total_component_schedules': component_schedules.count(),
        'manual_aircraft': aircraft_schedules.filter(main_type_schedule='Operational').count(),
        'automated_aircraft': aircraft_schedules.filter(main_type_schedule='Maintenance').count(),
        'manual_component': component_schedules.filter(main_type_schedule='Operational').count(),
        'automated_component': component_schedules.filter(main_type_schedule='Maintenance').count(),
        'aircrafts': Aircraft.objects.all(),
    }
    return render(request, 'maintenance/schedule/maintenance_dashboard.html', context)
