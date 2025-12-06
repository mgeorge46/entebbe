# views.py
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
from django.views.generic import DetailView, UpdateView, TemplateView
from django_tables2 import RequestConfig
from django_tables2 import SingleTableView
from flight_dispatch.models import Flight
from .filters import AircraftFilter
from .forms import AircraftMainComponentForm, AircraftSubComponentForm, FlightTechLogForm, AircraftFormUpdate, \
    AircraftFormAdd, AircraftMaintenanceTechLogForm, CloneComponentForm
from .models import Aircraft, AircraftMainComponent, AircraftSubComponent, AircraftMaintenanceTechLog, FlightTechLog, \
    AircraftSub3Component, \
    AircraftSub2Component
from .tables import AircraftTable, SubComponentTable, MainComponentTable, AircraftMaintenanceTechLogTable, \
    FlightTechLogTable, FlightTablePendingTechlog


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
