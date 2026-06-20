from django.contrib import admin
from .models import Firmware, FirmwareUpdateLog


@admin.register(Firmware)
class FirmwareAdmin(admin.ModelAdmin):
    list_display = ['device_model', 'version', 'status', 'is_force_update', 'created_at']
    list_filter = ['status', 'is_force_update']


@admin.register(FirmwareUpdateLog)
class FirmwareUpdateLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'firmware', 'from_version', 'to_version', 'status', 'created_at']
    list_filter = ['status']
