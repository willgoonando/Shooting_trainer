from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Firmware, FirmwareUpdateLog
from .serializers import FirmwareSerializer, FirmwareUpdateLogSerializer


class FirmwareViewSet(viewsets.ReadOnlyModelViewSet):
    """固件 —— 只读"""
    queryset = Firmware.objects.filter(status='published')
    serializer_class = FirmwareSerializer

    @action(detail=False, methods=['get'])
    def check(self, request):
        """检查固件更新"""
        device_model = request.query_params.get('model')
        current_version = request.query_params.get('version')
        if not device_model or not current_version:
            return Response({'detail': '请提供 model 和 version 参数'}, status=400)
        # 查找是否有更新版本的固件
        latest = Firmware.objects.filter(
            device_model=device_model, status='published'
        ).first()
        if not latest:
            return Response({'has_update': False})
        has_update = latest.version != current_version
        return Response({
            'has_update': has_update,
            'latest': FirmwareSerializer(latest).data if has_update else None,
            'is_force_update': latest.is_force_update if has_update else False,
        })


class FirmwareUpdateLogViewSet(viewsets.ReadOnlyModelViewSet):
    """固件升级记录 —— 只读"""
    serializer_class = FirmwareUpdateLogSerializer

    def get_queryset(self):
        return FirmwareUpdateLog.objects.filter(
            device__owner=self.request.user
        ).select_related('device', 'firmware')
