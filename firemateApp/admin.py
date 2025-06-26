from django.contrib import admin
from .models import User, Ambucycle, FireIncident, IncidentMedia, IncidentResponse

# Register your models here.
admin.site.register(User)
admin.site.register(Ambucycle)
admin.site.register(FireIncident)
admin.site.register(IncidentMedia)
admin.site.register(IncidentResponse)