from rest_framework import serializers
from .models import Device, DeviceStatusLog


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def validate_device_sn(self, value):
        if Device.objects.filter(device_sn=value, is_bound=True).exists():
            raise serializers.ValidationError('该设备已被绑定')
        return value


class DeviceStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStatusLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
