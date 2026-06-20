from rest_framework import viewsets
from .models import TargetTemplate, Target
from .serializers import TargetTemplateSerializer, TargetSerializer


class TargetTemplateViewSet(viewsets.ModelViewSet):
    """靶纸模板"""
    queryset = TargetTemplate.objects.filter(is_active=True)
    serializer_class = TargetTemplateSerializer

    def perform_create(self, serializer):
        serializer.save()


class TargetViewSet(viewsets.ModelViewSet):
    """具体靶纸配置"""
    queryset = Target.objects.all()
    serializer_class = TargetSerializer

    def perform_create(self, serializer):
        serializer.save()
