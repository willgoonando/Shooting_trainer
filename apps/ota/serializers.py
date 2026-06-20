from rest_framework import serializers
from .models import Firmware, FirmwareUpdateLog


class FirmwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firmware
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class FirmwareUpdateLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmwareUpdateLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
