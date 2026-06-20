from rest_framework import serializers
from .models import TargetTemplate, Target


class TargetTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class TargetSerializer(serializers.ModelSerializer):
    template = TargetTemplateSerializer(read_only=True)

    class Meta:
        model = Target
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
