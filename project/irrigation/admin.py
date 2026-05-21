from django.contrib import admin
from .models import Farmer, SensorReading


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'device_id', 'crop', 'farming_type')
    search_fields = ('name', 'device_id', 'crop')


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('id', 'farmer', 'timestamp', 'water_level', 'ph', 'light_intensity', 'humidity', 'temperature')
    list_filter = ('farmer',)
    readonly_fields = ('timestamp',)