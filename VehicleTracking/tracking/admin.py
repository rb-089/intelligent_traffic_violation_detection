from django.contrib import admin
from .models import IncidentReport, Owner, Vehicle, OverspeedIncident

# Register your models here
admin.site.register(IncidentReport)
admin.site.register(Owner)
admin.site.register(Vehicle)
admin.site.register(OverspeedIncident)