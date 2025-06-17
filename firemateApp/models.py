from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class Citizen(AbstractUser):
    GENDER_CHOICES = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    )
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    postal_code = models.CharField(max_length=15, blank=True)
    region = models.CharField(max_length=30, null=True, blank=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_number = models.CharField(max_length=20, unique=True)
    
class AmbucycleOperator(AbstractUser):
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    id_number = models.CharField(max_length=20, unique=True)

class Admin(AbstractUser):
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    id_number = models.CharField(max_length=20, unique=True)


class Ambucycle(models.Model):
    operator = models.ForeignKey(AmbucycleOperator.id, on_delete=models.SET_NULL, null=True)
    vehicle_number = models.CharField(max_length=20, unique=True)
    is_available = models.BooleanField(default=True)
    current_latitude = models.FloatField(null=True)
    current_longitude = models.FloatField(null=True)
    last_location_update = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

class FireIncident(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('IN_PROGRESS', 'Response In Progress'),
        ('RESOLVED', 'Resolved'),
    )

    reporter = models.ForeignKey(Citizen.id, on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField()
    voice_stress_score = models.FloatField(null=True)  # Overall voice stress score
    voice_analysis_details = models.JSONField(null=True)  # Detailed voice analysis results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    ai_confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True
    )
    assigned_ambucycle = models.ForeignKey(Ambucycle, on_delete=models.SET_NULL, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True)
    resolved_at = models.DateTimeField(null=True)

class IncidentMedia(models.Model):
    MEDIA_TYPES = (
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
    )
    
    incident = models.ForeignKey(FireIncident, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

class IncidentResponse(models.Model):
    incident = models.ForeignKey(FireIncident, on_delete=models.CASCADE, related_name='responses')
    ambucycle = models.ForeignKey(Ambucycle, on_delete=models.CASCADE)
    dispatched_at = models.DateTimeField(auto_now_add=True)
    arrived_at = models.DateTimeField(null=True)
    estimated_arrival_time = models.DateTimeField(null=True)
    route_data = models.JSONField(null=True)  # For storing navigation route information
