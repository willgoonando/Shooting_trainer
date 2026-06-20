from rest_framework import serializers
from .models import DrillTemplate, TrainingSession, Shot, TrainingResult


class DrillTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrillTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ShotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shot
        fields = ['shot_number', 'hit_x', 'hit_y', 'hit_ring', 'imu_data', 'trigger_timestamp']


class ShotBatchSerializer(serializers.Serializer):
    """批量上传 Shot"""
    shots = ShotSerializer(many=True)


class TrainingResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingResult
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class TrainingSessionSerializer(serializers.ModelSerializer):
    shots = ShotSerializer(many=True, read_only=True)
    result = TrainingResultSerializer(read_only=True)

    class Meta:
        model = TrainingSession
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class SessionCreateSerializer(serializers.ModelSerializer):
    """创建 Session 用的简化 Serializer"""
    class Meta:
        model = TrainingSession
        fields = ['drill_template', 'target', 'distance_meters', 'notes']
