from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    MotionScore, AccuracyScore, NeutralPenalty, OverallScore,
    IssueDiagnosis, Recommendation, SkillRating, TrainingPlan, VoiceCoachingEvent,
)
from .serializers import (
    MotionScoreSerializer, AccuracyScoreSerializer, NeutralPenaltySerializer,
    OverallScoreSerializer, IssueDiagnosisSerializer, RecommendationSerializer,
    SkillRatingSerializer, TrainingPlanSerializer, VoiceCoachingEventSerializer,
)
from .scoring import AIEngine


class AIResultViewSet(viewsets.GenericViewSet):
    """AI 教练 —— 训练结果聚合查询"""

    @action(detail=False, methods=['get'])
    def session_result(self, request):
        """获取指定 Session 的 AI 分析结果（对应文档 7.1）"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'detail': '请提供 session_id'}, status=400)
        engine = AIEngine()
        result = engine.get_aggregated_result(session_id)
        if result is None:
            return Response({'detail': '未找到相关训练数据'}, status=404)
        return Response(result)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """获取历史数据 + AI 趋势（对应文档 7.2）"""
        # 用户的历史训练成绩列表
        from apps.training.models import TrainingSession
        sessions = TrainingSession.objects.filter(
            user=request.user, status='completed'
        ).prefetch_related('result', 'motion_score', 'accuracy_score',
                           'overall_score', 'diagnosis', 'recommendation')[:100]

        data = []
        for session in sessions:
            item = {
                'session_id': str(session.id),
                'created_at': session.created_at,
                'total_shots': session.total_shots,
            }
            if hasattr(session, 'result'):
                item['avg_ring'] = session.result.avg_ring
            if hasattr(session, 'motion_score'):
                item['motion_score'] = session.motion_score.total_score
            if hasattr(session, 'accuracy_score'):
                item['accuracy_score'] = session.accuracy_score.total_score
            if hasattr(session, 'overall_score'):
                item['overall_score'] = session.overall_score.total_score
            data.append(item)

        skill_rating = SkillRating.objects.filter(user=request.user).first()
        return Response({
            'sessions': data,
            'skill_level': skill_rating.current_level if skill_rating else None,
            'trend_data': skill_rating.trend_data if skill_rating else [],
        })

    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """手动触发 AI 分析（通常由训练结束时自动触发）"""
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'detail': '请提供 session_id'}, status=400)
        engine = AIEngine()
        result = engine.run_full_pipeline(session_id)
        return Response({'session_id': session_id, 'status': result})


class SkillRatingViewSet(viewsets.ReadOnlyModelViewSet):
    """F4: 水平评估 —— 只读"""
    serializer_class = SkillRatingSerializer

    def get_queryset(self):
        return SkillRating.objects.filter(user=self.request.user)


class TrainingPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """F5: 训练计划 —— 只读"""
    serializer_class = TrainingPlanSerializer

    def get_queryset(self):
        return TrainingPlan.objects.filter(user=self.request.user)
