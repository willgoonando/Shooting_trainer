from django.contrib import admin
from .models import Device, DeviceStatusLog


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_sn', 'device_name', 'owner', 'firmware_version', 'battery_level', 'is_bound', 'is_active']
    list_filter = ['is_bound', 'is_active']
    search_fields = ['device_sn', 'device_name', 'owner__email']


@admin.register(DeviceStatusLog)
class DeviceStatusLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'battery_level', 'firmware_version', 'created_at']
