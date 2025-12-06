import django_tables2 as tables
from django.utils import timezone
from django_tables2.utils import A  # alias for Accessor
from django_tables2 import RequestConfig

from flight_dispatch.models import Flight
from accounts.models import LeaveRequest, CustomUser, CrewLicense


def has_ongoing_leave(user):
    current_date = timezone.now().date()
    leaves = LeaveRequest.objects.filter(user=user, start_date__lte=current_date, end_date__gte=current_date, status=LeaveRequest.APPROVED)
    return leaves.exists()


class FlightsWithCrewTable(tables.Table):
    edit = tables.LinkColumn('flight_update', args=[A('pk')], orderable=False, text='Edit', verbose_name='Action', accessor=A('pk'))
    view = tables.LinkColumn('flight_details', args=[A('pk')], orderable=False, text='View', verbose_name='', accessor=A('pk'))

    class Meta:
        model = Flight
        template_name = 'django_tables2/bootstrap.html'
        fields = ('flight_number', 'origin', 'destination', 'departure_time', 'arrival_time', 'cabin_crew', 'flight_crew', 'edit', 'view')


class FlightsWithoutCrewTable(tables.Table):
    edit = tables.LinkColumn('flight_update', args=[A('pk')], orderable=False, text='Edit', verbose_name='Action', accessor=A('pk'))
    view = tables.LinkColumn('flight_details', args=[A('pk')], orderable=False, text='View', verbose_name='', accessor=A('pk'))

    class Meta:
        model = Flight
        template_name = 'django_tables2/bootstrap.html'
        fields = ('flight_number', 'origin', 'destination', 'departure_time', 'arrival_time', 'edit', 'view')
'''


class FreeCrewTable(tables.Table):
    current_date = timezone.now()
    all_crew = CustomUser.objects.filter(department__in=['cabin_crew', 'flight_crew'])
    assigned_crew = Flight.objects.filter(arrival_time__gte=current_date).values_list('cabin_crew', 'flight_crew')
    free_crew = all_crew.exclude(pk__in=assigned_crew)

    free_crew_data = [{
        'Names': crew.first_name + ' ' + crew.last_name,
        'Last Flight': None,  # You need to determine this based on your model's relationships
        'Last Destination': None,  # Likewise, determine this based on your model's relationships
        'Office Status': 'Out of Office' if has_ongoing_leave(crew) else 'In Office',
        'Assign': None,  # Link for assigning this crew (if needed)
        'View': None  # Link for viewing this crew member's profile/details
    } for crew in free_crew]

    table_free_crew = FreeCrewTable(free_crew_data)
    RequestConfig(request, paginate={'per_page': 50}).configure(table_free_crew)

    assign = tables.LinkColumn('flight_update', args=[A('pk')], orderable=False, text='Edit', verbose_name='Action', accessor=A('pk'))
    view = tables.LinkColumn('flight_details', args=[A('pk')], orderable=False, text='View', verbose_name='', accessor=A('pk'))

class LinceseTable(tables.Table):
    licenses = CrewLicense.objects.all().select_related('user')

    licenses_data = [{
        'Names': license.user.first_name + ' ' + license.user.last_name,
        'Last Flight': None,  # Determine based on your model's relationships
        'Last Destination': None,  # Likewise
        'Office Status': 'Out of Office' if has_ongoing_leave(license.user) else 'In Office',
        'Update': None,  # Link for updating license info (if needed)
        'View': None  # Link for viewing license info
    } for license in licenses]

    table_licenses = LinceseCrewTable(licenses_data)
    RequestConfig(request, paginate={'per_page': 50}).configure(table_licenses)

'''

