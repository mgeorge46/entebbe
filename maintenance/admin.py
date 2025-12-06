from django.contrib import admin

# Register your models here.

from .models import Aircraft, FlightTechLog, AircraftMainComponent, AircraftSub2Component, AircraftMaintenanceTechLog, \
    AircraftSubComponent, AircraftMaintenance, AircraftSub3Component, Airport

admin.site.register(Aircraft)
admin.site.register(AircraftMainComponent)
admin.site.register(AircraftMaintenance)
admin.site.register(FlightTechLog)
admin.site.register(AircraftSubComponent)
admin.site.register(AircraftSub2Component)
admin.site.register(AircraftSub3Component)
admin.site.register(AircraftMaintenanceTechLog)
admin.site.register(Airport)
