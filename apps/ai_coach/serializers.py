from rest_framework import serializers
from .models import (
    MotionScore, AccuracyScore, NeutralPenalty, OverallScore,
    IssueDiagnosis, Recommendation, SkillRating, TrainingPlan, VoiceCoachingEvent,
)


class MotionScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotionScore
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class AccuracyScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccuracyScore
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class NeutralPenaltySerializer(serializers.ModelSerializer):
    class Meta:
        model = NeutralPenalty
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class OverallScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverallScore
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class IssueDiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueDiagnosis
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class SkillRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillRating
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TrainingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingPlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class VoiceCoachingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceCoachingEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


# 训练结果页聚合
class SessionAIResultSerializer(serializers.Serializer):
    """训练结果页聚合 —— 对应文档 7.1 聚合结果页 API"""
    session_id = serializers.UUIDField()
    # 训练摘要 KPI
    avg_ring = serializers.FloatField(allow_null=True)
    group_radius_mm = serializers.FloatField(allow_null=True)
    center_offset_mm = serializers.FloatField(allow_null=True)
    total_shots = serializers.IntegerField()
    duration_seconds = serializers.IntegerField(allow_null=True)
    # 评分
    motion_score = MotionScoreSerializer(allow_null=True)
    accuracy_score = AccuracyScoreSerializer(allow_null=True)
    overall_score = OverallScoreSerializer(allow_null=True)
    # 诊断
    issues = serializers.ListField(child=serializers.DictField(), default=list)
    accuracy_limitations = serializers.ListField(child=serializers.DictField(), default=list)
    # 建议
    recommendations = serializers.ListField(child=serializers.DictField(), default=list)
    # 水平
    skill_level = serializers.CharField(allow_null=True)
    next_plan_hint = serializers.CharField(allow_null=True, allow_blank=True)
    # 图表数据
    scatter_data = serializers.ListField(default=list)
    direction_data = serializers.ListField(default=list)
    score_curve = serializers.ListField(default=list)
    motion_data = serializers.ListField(default=list)
