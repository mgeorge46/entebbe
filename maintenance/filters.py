import django_filters
from .models import Aircraft
from django.db.models import Q


class AircraftFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Search')
    aircraft_status = django_filters.ChoiceFilter(choices=Aircraft.CRAFT_STATUS)

    class Meta:
        model = Aircraft
        fields = ['search', 'aircraft_status']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(abbreviation__icontains=value) |
            Q(registration_number__icontains=value) |
            Q(aircraft_model__icontains=value) |
            Q(aircraft_serial__icontains=value) |
            Q(year__icontains=value)
        )


class AircraftFilter2(django_filters.FilterSet):
    abbreviation = django_filters.CharFilter(lookup_expr='icontains')
    registration_number = django_filters.CharFilter(lookup_expr='icontains')
    aircraft_model = django_filters.CharFilter(lookup_expr='icontains')
    seating_capacity = django_filters.NumberFilter(lookup_expr='gte')
    aircraft_status = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Aircraft
        fields = ['abbreviation', 'registration_number', 'aircraft_model', 'seating_capacity', 'aircraft_status']
