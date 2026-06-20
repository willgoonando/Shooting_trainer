from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Device, DeviceStatusLog
from .serializers import DeviceSerializer, DeviceStatusLogSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    """设备管理 —— 绑定/解绑/切换/状态上报"""
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return Device.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """切换当前激活设备"""
        device = self.get_object()
        Device.objects.filter(owner=request.user, is_active=True).update(is_active=False)
        device.is_active = True
        device.save(update_fields=['is_active'])
        return Response(DeviceSerializer(device).data)

    @action(detail=True, methods=['post'])
    def unbind(self, request, pk=None):
        """解绑设备"""
        device = self.get_object()
        device.is_bound = False
        device.is_active = False
        device.save(update_fields=['is_bound', 'is_active'])
        return Response({'message': '设备已解绑'})

    @action(detail=True, methods=['post'])
    def report_status(self, request, pk=None):
        """设备状态上报"""
        device = self.get_object()
        serializer = DeviceStatusLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)
        # 同步更新设备状态
        device.battery_level = serializer.validated_data.get('battery_level', device.battery_level)
        device.firmware_version = serializer.validated_data.get('firmware_version', device.firmware_version)
        device.save(update_fields=['battery_level', 'firmware_version', 'updated_at'])
        return Response(serializer.data)
