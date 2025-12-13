"""
Optimized Whiteboard Calendar Views with Performance Enhancements
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Prefetch, Q, Count
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from datetime import timedelta
import json

from flight_dispatch.models import Flight
from maintenance.models import (
    Aircraft, AircraftMainComponent, AircraftSubComponent,
    AircraftSub2Component, AircraftSub3Component, ComponentMaintenance
)
from accounts.models import CustomUser


# Color schemes for better organization
FLIGHT_STATUS_COLORS = {
    'Scheduled': '#007bff',
    'Dispatching': '#17a2b8',
    'OnTrip': '#20c997',
    'Completed': '#28a745',
    'Cancelled': '#6c757d',
    'Delayed': '#ffc107',
    'Arrived': '#28a745',
    'Dispatched': '#0056b3',
}

EVENT_TYPE_COLORS = {
    'flight': '#007bff',
    'crew_cabin': '#28a745',
    'crew_flight': '#198754',
    'maintenance_due': '#dc3545',
    'maintenance_recommended': '#fd7e14',
    'maintenance_scheduled': '#6f42c1',
}


@login_required
def whiteboard_calendar_view(request):
    """
    Main whiteboard calendar view - optimized query
    """
    # Optimized queries with select_related to reduce database hits
    aircrafts = Aircraft.objects.only('id', 'abbreviation', 'registration_number').order_by('abbreviation')
    
    context = {
        'aircrafts': aircrafts,
        'total_aircraft': aircrafts.count(),
    }
    
    return render(request, 'airways/whiteboard_calendar.html', context)


@login_required
def whiteboard_calendar_data(request):
    """
    Optimized API endpoint with query optimization and partial caching
    """
    # Parse parameters
    start = request.GET.get('start')
    end = request.GET.get('end')
    show_flights = request.GET.get('show_flights', 'true') == 'true'
    show_crew = request.GET.get('show_crew', 'true') == 'true'
    show_maintenance_due = request.GET.get('show_maintenance_due', 'true') == 'true'
    show_maintenance_recommended = request.GET.get('show_maintenance_recommended', 'true') == 'true'
    show_maintenance_scheduled = request.GET.get('show_maintenance_scheduled', 'true') == 'true'
    aircraft_filter = request.GET.get('aircraft', '')
    status_filter = request.GET.get('status', '')
    
    # Create cache key based on parameters
    cache_key = f'whiteboard_events_{start}_{end}_{show_flights}_{show_crew}_{show_maintenance_due}_{show_maintenance_recommended}_{show_maintenance_scheduled}_{aircraft_filter}_{status_filter}'
    
    # Try to get from cache first
    cached_events = cache.get(cache_key)
    if cached_events:
        return JsonResponse(cached_events, safe=False)
    
    events = []
    
    # Base query filters
    flight_query = Q(departure_time__gte=start, departure_time__lte=end)
    if aircraft_filter:
        flight_query &= Q(aircraft_id=aircraft_filter)
    if status_filter:
        flight_query &= Q(flight_status=status_filter)
    
    # 1. FLIGHTS - Optimized with select_related and prefetch_related
    if show_flights:
        flights = Flight.objects.filter(flight_query).select_related(
            'aircraft', 'origin', 'destination'
        ).prefetch_related(
            'cabin_crew', 'flight_crew'
        ).only(
            'id', 'flight_number', 'departure_time', 'arrival_time',
            'return_departure_time', 'return_arrival_time', 'flight_status',
            'trip_type', 'aircraft__abbreviation', 'origin__name', 
            'destination__name'
        )
        
        for flight in flights:
            # Get crew names efficiently
            cabin_crew = list(flight.cabin_crew.values_list('first_name', 'last_name'))
            flight_crew = list(flight.flight_crew.values_list('first_name', 'last_name'))
            
            cabin_crew_str = ", ".join([f"{fn} {ln}" for fn, ln in cabin_crew])
            flight_crew_str = ", ".join([f"{fn} {ln}" for fn, ln in flight_crew])
            
            # Main flight event
            events.append({
                'id': f'f{flight.id}',
                'title': f'✈️ {flight.flight_number}',
                'start': flight.departure_time.isoformat(),
                'end': flight.arrival_time.isoformat(),
                'color': FLIGHT_STATUS_COLORS.get(flight.flight_status, '#007bff'),
                'extendedProps': {
                    'type': 'flight',
                    'flight_id': flight.id,
                    'flight_number': flight.flight_number,
                    'origin': flight.origin.name,
                    'destination': flight.destination.name,
                    'aircraft': flight.aircraft.abbreviation,
                    'status': flight.flight_status,
                    'cabin_crew': cabin_crew_str,
                    'flight_crew': flight_crew_str,
                }
            })
            
            # Return flight
            if flight.trip_type == 'round-trip' and flight.return_departure_time:
                events.append({
                    'id': f'fr{flight.id}',
                    'title': f'↩️ {flight.flight_number}',
                    'start': flight.return_departure_time.isoformat(),
                    'end': flight.return_arrival_time.isoformat(),
                    'color': FLIGHT_STATUS_COLORS.get(flight.flight_status, '#007bff'),
                    'extendedProps': {
                        'type': 'flight_return',
                        'flight_id': flight.id,
                        'flight_number': flight.flight_number,
                        'origin': flight.destination.name,
                        'destination': flight.origin.name,
                        'aircraft': flight.aircraft.abbreviation,
                        'status': flight.flight_status,
                    }
                })
    
    # 2. CREW SCHEDULES - Optimized
    if show_crew:
        crew_flights = Flight.objects.filter(flight_query).prefetch_related(
            Prefetch('cabin_crew', queryset=CustomUser.objects.only('id', 'first_name', 'last_name', 'employee_id')),
            Prefetch('flight_crew', queryset=CustomUser.objects.only('id', 'first_name', 'last_name', 'employee_id'))
        ).only('id', 'flight_number', 'departure_time', 'arrival_time')
        
        for flight in crew_flights:
            # Cabin crew events
            for crew in flight.cabin_crew.all():
                events.append({
                    'id': f'cc{crew.id}f{flight.id}',
                    'title': f'👤 {crew.first_name} {crew.last_name}',
                    'start': flight.departure_time.isoformat(),
                    'end': flight.arrival_time.isoformat(),
                    'color': EVENT_TYPE_COLORS['crew_cabin'],
                    'extendedProps': {
                        'type': 'crew_schedule',
                        'crew_id': crew.id,
                        'crew_name': f'{crew.first_name} {crew.last_name}',
                        'crew_type': 'Cabin Crew',
                        'flight_number': flight.flight_number,
                        'flight_id': flight.id,
                    }
                })
            
            # Flight crew events
            for crew in flight.flight_crew.all():
                events.append({
                    'id': f'fc{crew.id}f{flight.id}',
                    'title': f'✈️ {crew.first_name} {crew.last_name}',
                    'start': flight.departure_time.isoformat(),
                    'end': flight.arrival_time.isoformat(),
                    'color': EVENT_TYPE_COLORS['crew_flight'],
                    'extendedProps': {
                        'type': 'crew_schedule',
                        'crew_id': crew.id,
                        'crew_name': f'{crew.first_name} {crew.last_name}',
                        'crew_type': 'Flight Crew',
                        'flight_number': flight.flight_number,
                        'flight_id': flight.id,
                    }
                })
    
    # 3. MAINTENANCE DUE - Calendar-based, optimized query
    if show_maintenance_due:
        add_component_maintenance_events(
            events, start, end, 
            field='item_calender',
            event_type='maintenance_due',
            title_prefix='🔴 DUE',
            color=EVENT_TYPE_COLORS['maintenance_due'],
            aircraft_filter=aircraft_filter
        )
    
    # 4. RECOMMENDED MAINTENANCE - Optimized
    if show_maintenance_recommended:
        add_component_maintenance_events(
            events, start, end,
            field='next_maintenance_date',
            event_type='maintenance_recommended',
            title_prefix='🟠 REC',
            color=EVENT_TYPE_COLORS['maintenance_recommended'],
            aircraft_filter=aircraft_filter
        )
    
    # 5. SCHEDULED MAINTENANCE - Optimized with select_related
    if show_maintenance_scheduled:
        maintenance_query = Q(start_date__gte=start, start_date__lte=end)
        
        scheduled = ComponentMaintenance.objects.filter(
            maintenance_query
        ).select_related('content_type').only(
            'id', 'start_date', 'end_date', 'maintenance_type',
            'main_type_schedule', 'remarks', 'object_id', 'content_type'
        )
        
        for maint in scheduled:
            component = maint.component_to_maintain
            if component:
                aircraft = get_component_aircraft(component)
                
                # Filter by aircraft if specified
                if aircraft_filter and str(aircraft.id) != str(aircraft_filter):
                    continue
                
                events.append({
                    'id': f'm{maint.id}',
                    'title': f'🛠️ {maint.maintenance_type}: {component.component_name[:20]}',
                    'start': maint.start_date.isoformat(),
                    'end': maint.end_date.isoformat(),
                    'color': EVENT_TYPE_COLORS['maintenance_scheduled'],
                    'extendedProps': {
                        'type': 'maintenance_scheduled',
                        'maintenance_id': maint.id,
                        'component_name': component.component_name,
                        'aircraft': str(aircraft) if aircraft else 'N/A',
                        'maintenance_type': maint.maintenance_type,
                        'status': maint.main_type_schedule,
                        'remarks': maint.remarks,
                    }
                })
    
    # Cache for 2 minutes
    cache.set(cache_key, events, 120)
    
    return JsonResponse(events, safe=False)


def add_component_maintenance_events(events, start, end, field, event_type, title_prefix, color, aircraft_filter=None):
    """
    Helper function to add component maintenance events efficiently
    Reduces code duplication for calendar and recommended maintenance
    """
    component_models = [
        ('AircraftMainComponent', AircraftMainComponent),
        ('AircraftSubComponent', AircraftSubComponent),
        ('AircraftSub2Component', AircraftSub2Component),
        ('AircraftSub3Component', AircraftSub3Component),
    ]
    
    for model_name, Model in component_models:
        # Build query
        query = Q(**{f'{field}__isnull': False, f'{field}__gte': start, f'{field}__lte': end})
        query &= Q(component_status='Attached')
        
        # Optimize query based on model level
        if model_name == 'AircraftMainComponent':
            components = Model.objects.filter(query).select_related('aircraft_attached').only(
                'id', 'component_name', 'serial_number', field,
                'maintenance_hours', 'aircraft_attached__id', 'aircraft_attached__abbreviation'
            )
        else:
            # For nested components, we need to traverse the relationships
            components = Model.objects.filter(query).only(
                'id', 'component_name', 'serial_number', field, 'maintenance_hours'
            )
        
        for component in components:
            aircraft = get_component_aircraft(component)
            
            # Apply aircraft filter
            if aircraft_filter and aircraft and str(aircraft.id) != str(aircraft_filter):
                continue
            
            date_value = getattr(component, field)
            
            events.append({
                'id': f'{event_type}{model_name[:4]}{component.id}',
                'title': f'{title_prefix}: {component.component_name[:25]}',
                'start': date_value.isoformat(),
                'allDay': True,
                'color': color,
                'extendedProps': {
                    'type': event_type,
                    'component_id': component.id,
                    'component_name': component.component_name,
                    'component_type': model_name,
                    'aircraft': str(aircraft) if aircraft else 'N/A',
                    'aircraft_id': aircraft.id if aircraft else None,
                    'serial_number': component.serial_number,
                    'maintenance_hours': float(component.maintenance_hours),
                    field: date_value.strftime('%Y-%m-%d'),
                }
            })


def get_component_aircraft(component):
    """
    Efficiently get aircraft for any component level using cached relationships
    """
    cache_key = f'component_aircraft_{type(component).__name__}_{component.id}'
    aircraft = cache.get(cache_key)
    
    if aircraft is None:
        if isinstance(component, AircraftMainComponent):
            aircraft = component.aircraft_attached
        elif isinstance(component, AircraftSubComponent):
            if hasattr(component, 'parent_component'):
                aircraft = component.parent_component.aircraft_attached
        elif isinstance(component, AircraftSub2Component):
            if hasattr(component, 'parent_sub_component'):
                parent = component.parent_sub_component
                if hasattr(parent, 'parent_component'):
                    aircraft = parent.parent_component.aircraft_attached
        elif isinstance(component, AircraftSub3Component):
            if hasattr(component, 'parent_sub2_component'):
                parent = component.parent_sub2_component
                if hasattr(parent, 'parent_sub_component'):
                    grandparent = parent.parent_sub_component
                    if hasattr(grandparent, 'parent_component'):
                        aircraft = grandparent.parent_component.aircraft_attached
        
        # Cache for 5 minutes
        if aircraft:
            cache.set(cache_key, aircraft, 300)
    
    return aircraft


@login_required
def get_flight_details(request, flight_id):
    """
    Optimized flight details retrieval
    """
    try:
        # Optimized query
        flight = Flight.objects.select_related(
            'aircraft', 'origin', 'destination'
        ).prefetch_related(
            Prefetch('cabin_crew', queryset=CustomUser.objects.only('id', 'first_name', 'last_name', 'employee_id')),
            Prefetch('flight_crew', queryset=CustomUser.objects.only('id', 'first_name', 'last_name', 'employee_id'))
        ).get(id=flight_id)
        
        # Build response efficiently
        data = {
            'success': True,
            'flight': {
                'id': flight.id,
                'flight_number': flight.flight_number,
                'origin': flight.origin.name,
                'destination': flight.destination.name,
                'departure_time': flight.departure_time.strftime('%Y-%m-%d %H:%M'),
                'arrival_time': flight.arrival_time.strftime('%Y-%m-%d %H:%M'),
                'aircraft': flight.aircraft.abbreviation,
                'status': flight.flight_status,
                'trip_type': flight.trip_type,
                'cabin_crew': [
                    {
                        'id': c.id,
                        'name': f'{c.first_name} {c.last_name}',
                        'employee_id': c.employee_id or 'N/A'
                    } for c in flight.cabin_crew.all()
                ],
                'flight_crew': [
                    {
                        'id': c.id,
                        'name': f'{c.first_name} {c.last_name}',
                        'employee_id': c.employee_id or 'N/A'
                    } for c in flight.flight_crew.all()
                ],
                'comments': flight.flight_comments or '',
            }
        }
        
        return JsonResponse(data)
        
    except Flight.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Flight not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_component_details(request, component_type, component_id):
    """
    Optimized component details with maintenance history
    """
    try:
        model_map = {
            'AircraftMainComponent': AircraftMainComponent,
            'AircraftSubComponent': AircraftSubComponent,
            'AircraftSub2Component': AircraftSub2Component,
            'AircraftSub3Component': AircraftSub3Component,
        }
        
        ComponentModel = model_map.get(component_type)
        if not ComponentModel:
            return JsonResponse({'success': False, 'error': 'Invalid component type'}, status=400)
        
        # Get component with limited fields
        component = ComponentModel.objects.only(
            'id', 'component_name', 'serial_number', 'part_number',
            'maintenance_hours', 'item_calender', 'next_maintenance_date',
            'component_status', 'maintenance_status'
        ).get(id=component_id)
        
        aircraft = get_component_aircraft(component)
        
        # Get recent maintenance history
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(ComponentModel)
        
        maintenance_history = ComponentMaintenance.objects.filter(
            content_type=content_type,
            object_id=component.id
        ).only(
            'id', 'maintenance_type', 'start_date', 'end_date', 'remarks'
        ).order_by('-start_date')[:5]
        
        data = {
            'success': True,
            'component': {
                'id': component.id,
                'name': component.component_name,
                'type': component_type,
                'serial_number': component.serial_number,
                'part_number': component.part_number,
                'aircraft': str(aircraft) if aircraft else 'N/A',
                'aircraft_id': aircraft.id if aircraft else None,
                'maintenance_hours': float(component.maintenance_hours),
                'item_calender': component.item_calender.strftime('%Y-%m-%d') if component.item_calender else None,
                'next_maintenance_date': component.next_maintenance_date.strftime('%Y-%m-%d') if component.next_maintenance_date else None,
                'component_status': component.component_status,
                'maintenance_status': component.maintenance_status,
                'maintenance_history': [
                    {
                        'id': m.id,
                        'type': m.maintenance_type,
                        'start_date': m.start_date.strftime('%Y-%m-%d'),
                        'end_date': m.end_date.strftime('%Y-%m-%d'),
                        'remarks': m.remarks,
                    } for m in maintenance_history
                ],
            }
        }
        
        return JsonResponse(data)
        
    except ComponentModel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Component not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def quick_schedule_maintenance(request):
    """
    Quick maintenance scheduling with validation
    """
    if request.method == 'POST':
        try:
            from django.contrib.contenttypes.models import ContentType
            
            component_type = request.POST.get('component_type')
            component_id = request.POST.get('component_id')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            maintenance_type = request.POST.get('maintenance_type')
            remarks = request.POST.get('remarks', '')
            
            # Validate maintenance type
            valid_types = ['Class_A', 'Class_B', 'Class_C', 'Class_D']
            if maintenance_type not in valid_types:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid maintenance type. Must be one of: {", ".join(valid_types)}'
                }, status=400)
            
            # Get component
            model_map = {
                'AircraftMainComponent': AircraftMainComponent,
                'AircraftSubComponent': AircraftSubComponent,
                'AircraftSub2Component': AircraftSub2Component,
                'AircraftSub3Component': AircraftSub3Component,
            }
            
            ComponentModel = model_map.get(component_type)
            if not ComponentModel:
                return JsonResponse({'success': False, 'error': 'Invalid component type'}, status=400)
            
            component = ComponentModel.objects.get(id=component_id)
            content_type = ContentType.objects.get_for_model(ComponentModel)
            
            # Create maintenance record
            maintenance = ComponentMaintenance.objects.create(
                content_type=content_type,
                object_id=component.id,
                main_type_schedule='Maintenance',
                maintenance_type=maintenance_type,
                start_date=start_date,
                end_date=end_date,
                remarks=remarks,
                added_by=request.user,
                maintenance_hours=component.maintenance_hours,
                maintenance_hours_added=0
            )
            
            # Invalidate cache
            cache.delete_pattern('whiteboard_events_*')
            
            return JsonResponse({
                'success': True,
                'message': 'Maintenance scheduled successfully',
                'maintenance_id': maintenance.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def quick_schedule_flight(request):
    """
    Quick flight scheduling from calendar
    """
    if request.method == 'POST':
        from flight_dispatch.forms import FlightForm
        
        form = FlightForm(request.POST, new_flight=True)
        if form.is_valid():
            flight = form.save(commit=False)
            flight.added_by = request.user
            flight.save()
            form.save_m2m()
            
            # Invalidate cache
            cache.delete_pattern('whiteboard_events_*')
            
            return JsonResponse({
                'success': True,
                'message': 'Flight scheduled successfully',
                'flight_id': flight.id,
                'flight_number': flight.flight_number
            })
        else:
            return JsonResponse({'success': False, 'errors': dict(form.errors)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def whiteboard_stats(request):
    """
    Get statistics for the whiteboard dashboard
    """
    now = timezone.now()
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=7)
    
    stats = {
        'flights_this_week': Flight.objects.filter(
            departure_time__gte=week_start,
            departure_time__lt=week_end
        ).count(),
        'maintenance_due_7_days': sum([
            Model.objects.filter(
                item_calender__gte=now,
                item_calender__lte=now + timedelta(days=7),
                component_status='Attached'
            ).count()
            for Model in [AircraftMainComponent, AircraftSubComponent, 
                         AircraftSub2Component, AircraftSub3Component]
        ]),
        'components_critical': sum([
            Model.objects.filter(
                maintenance_hours__lt=10,
                component_status='Attached'
            ).count()
            for Model in [AircraftMainComponent, AircraftSubComponent,
                         AircraftSub2Component, AircraftSub3Component]
        ]),
        'active_crew': CustomUser.objects.filter(
            Q(department='cabin_crew') | Q(department='flight_crew'),
            staff_status='Active'
        ).count(),
    }
    
    return JsonResponse(stats)