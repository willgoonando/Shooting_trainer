from django.contrib import admin
from .models import TargetTemplate, Target


@admin.register(TargetTemplate)
class TargetTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'ring_count', 'is_active']


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ['id', 'template', 'distance_meters']
