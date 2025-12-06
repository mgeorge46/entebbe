import django_filters
from .models import Flight

class FlightFilter(django_filters.FilterSet):
    class Meta:
        model = Flight
        fields = '__all__'
