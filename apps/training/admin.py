from django.contrib import admin
from .models import DrillTemplate, TrainingSession, Shot, TrainingResult


@admin.register(DrillTemplate)
class DrillTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'cartridge_type', 'difficulty', 'is_active']
    list_filter = ['difficulty', 'is_active']


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'device', 'status', 'total_shots', 'distance_meters', 'started_at', 'ended_at']
    list_filter = ['status']
    search_fields = ['user__email']


@admin.register(Shot)
class ShotAdmin(admin.ModelAdmin):
    list_display = ['session', 'shot_number', 'hit_ring', 'trigger_timestamp', 'created_at']


@admin.register(TrainingResult)
class TrainingResultAdmin(admin.ModelAdmin):
    list_display = ['session', 'avg_ring', 'group_radius_mm', 'center_offset_mm', 'total_score']
