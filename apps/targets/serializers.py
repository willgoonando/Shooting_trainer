from rest_framework import serializers
from .models import TargetTemplate, Target


class TargetTemplateSerializer(serializers.ModelSerializer):
    image_url_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TargetTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_image_url_display(self, obj):
        """返回实际可用的图片 URL"""
        return obj.get_image_url()


class TargetSerializer(serializers.ModelSerializer):
    template = TargetTemplateSerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Target
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
