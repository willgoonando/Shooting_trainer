from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DrillTemplate, TrainingSession, Shot, TrainingResult
from .serializers import (
    DrillTemplateSerializer,
    TrainingSessionSerializer, SessionCreateSerializer,
    ShotSerializer, ShotBatchSerializer,
    TrainingResultSerializer,
)


class DrillTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """Drill 模板 —— 只读"""
    queryset = DrillTemplate.objects.filter(is_active=True)
    serializer_class = DrillTemplateSerializer


class TrainingSessionViewSet(viewsets.ModelViewSet):
    """训练 Session —— 核心模块"""
    serializer_class = TrainingSessionSerializer

    def get_queryset(self):
        return TrainingSession.objects.filter(
            user=self.request.user
        ).select_related('user', 'drill_template', 'target', 'result').prefetch_related('shots')

    def get_serializer_class(self):
        if self.action == 'create':
            return SessionCreateSerializer
        return TrainingSessionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save(user=request.user)
        return Response(TrainingSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """开始训练"""
        session = self.get_object()
        if session.status != 'created':
            return Response({'detail': '当前状态不允许开始'}, status=status.HTTP_400_BAD_REQUEST)
        session.status = 'in_progress'
        session.started_at = timezone.now()
        session.save(update_fields=['status', 'started_at'])
        return Response(TrainingSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        session = self.get_object()
        session.status = 'paused'
        session.save(update_fields=['status'])
        return Response(TrainingSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        session = self.get_object()
        session.status = 'in_progress'
        session.save(update_fields=['status'])
        return Response(TrainingSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """结束训练 —— 触发 AI 分析"""
        session = self.get_object()
        if session.status not in ['in_progress', 'paused']:
            return Response({'detail': '当前状态不允许结束'}, status=status.HTTP_400_BAD_REQUEST)
        session.status = 'completed'
        session.ended_at = timezone.now()
        if session.started_at:
            session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
        session.total_shots = session.shots.count()
        session.save()
        # 触发 AI 评分流程
        from apps.ai_coach.scoring import AIEngine
        engine = AIEngine()
        engine.run_full_pipeline(str(session.id))
        return Response(TrainingSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def abort(self, request, pk=None):
        session = self.get_object()
        session.status = 'aborted'
        session.ended_at = timezone.now()
        session.save(update_fields=['status', 'ended_at'])
        return Response(TrainingSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def upload_shots(self, request, pk=None):
        """批量上传 Shot 数据"""
        session = self.get_object()
        serializer = ShotBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shots_data = serializer.validated_data['shots']
        shots = [Shot(session=session, **s) for s in shots_data]
        Shot.objects.bulk_create(shots)
        session.total_shots = session.shots.count()
        session.save(update_fields=['total_shots'])
        return Response({'count': len(shots)}, status=status.HTTP_201_CREATED)
