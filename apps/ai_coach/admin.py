from django.contrib import admin
from .models import (
    MotionScore, AccuracyScore, NeutralPenalty, OverallScore,
    IssueDiagnosis, Recommendation, SkillRating, TrainingPlan, VoiceCoachingEvent,
)


@admin.register(MotionScore)
class MotionScoreAdmin(admin.ModelAdmin):
    list_display = ['session', 'trigger_control', 'stability', 'follow_through', 'consistency', 'total_score']

@admin.register(AccuracyScore)
class AccuracyScoreAdmin(admin.ModelAdmin):
    list_display = ['session', 'mean_ring', 'group_radius', 'center_offset', 'total_score']

@admin.register(NeutralPenalty)
class NeutralPenaltyAdmin(admin.ModelAdmin):
    list_display = ['session', 'hold_too_long_count', 'abort_count', 'total_penalty']

@admin.register(OverallScore)
class OverallScoreAdmin(admin.ModelAdmin):
    list_display = ['session', 'motion_weight', 'accuracy_weight', 'total_score']

@admin.register(IssueDiagnosis)
class IssueDiagnosisAdmin(admin.ModelAdmin):
    list_display = ['session']

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['session']

@admin.register(SkillRating)
class SkillRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_level', 'total_sessions_analyzed', 'ema_motion_score', 'ema_accuracy_score']

@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_type', 'completion_rate', 'is_active', 'started_at']

@admin.register(VoiceCoachingEvent)
class VoiceCoachingEventAdmin(admin.ModelAdmin):
    list_display = ['session', 'event_type', 'priority', 'is_played', 'created_at']
