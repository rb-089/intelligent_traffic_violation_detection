from django.db import models

class Owner(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=20, unique=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)

    def __str__(self):
        return self.vehicle_number

class OverspeedIncident(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    speed = models.FloatField()
    location = models.CharField(max_length=255, default='Unknown')
    number_plate = models.CharField(max_length=20, null=True)  # Optional field for the number plate
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.speed} km/h"
    
from django.db import models

class IncidentReport(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    location = models.CharField(max_length=255)  # Allow storing arbitrary text like GPS coordinates
    description = models.TextField(blank=True, null=True)  # Optional incident description
    photos = models.ImageField(upload_to='incident_photos/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location} ({self.timestamp})"
