"""
页面级聚合接口 —— 按 APP 展示页面的需求，一次性返回所需全部数据
对应需求文档 9.0 节：/api/page/*
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.training.models import TrainingSession
from apps.ai_coach.models import (
    MotionScore, AccuracyScore, OverallScore,
    IssueDiagnosis, Recommendation, SkillRating,
)


class TrainingResultPageViewSet(viewsets.GenericViewSet):
    """训练结果页 —— 一次请求返回评分/诊断/建议/图表全部数据"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def full(self, request):
        """
        GET /api/page/training-result-full/?session_id=xxx
        返回训练结果页完整数据（对应数据流文档 Step 6）
        """
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'detail': '请提供 session_id'}, status=400)

        session = get_object_or_404(
            TrainingSession.objects.select_related('result'),
            id=session_id, user=request.user,
        )

        data = {
            # —— 训练基本信息 ——
            'session_id': str(session.id),
            'total_shots': session.total_shots,
            'duration_seconds': session.duration_seconds,
            'avg_ring': None,
            'status': session.status,
            'created_at': session.created_at.isoformat() if session.created_at else None,

            # —— F1-F3 默认空 ——
            'motion_score': None,
            'accuracy_score': None,
            'overall_score': None,
            'diagnosis': None,
            'recommendation': None,

            # —— F4 ——
            'skill_level': None,

            # —— 图表数据 ——
            'scatter_data': [],
            'score_curve': [],
            'motion_data': [],
        }

        # 训练结果（图表数据）
        if hasattr(session, 'result') and session.result:
            r = session.result
            data['avg_ring'] = r.avg_ring
            data['scatter_data'] = r.scatter_data or []
            data['score_curve'] = r.score_curve or []
            data['motion_data'] = r.motion_data or []

        # 动作评分
        try:
            ms = MotionScore.objects.get(session=session)
            data['motion_score'] = {
                'trigger_control': ms.trigger_control,
                'stability': ms.stability,
                'follow_through': ms.follow_through,
                'consistency': ms.consistency,
                'total_score': ms.total_score,
            }
            # 将 per_shot_details 放入 motion_data（如果 result 没生成图表）
            per_shot = ms.details.get('per_shot', []) if ms.details else []
            if per_shot and not data['motion_data']:
                data['motion_data'] = [
                    [d['shot_number'], d['trigger_control'],
                     d['stability'], d['follow_through']]
                    for d in per_shot
                ]
        except MotionScore.DoesNotExist:
            pass

        # 准度评分
        try:
            acc = AccuracyScore.objects.get(session=session)
            data['accuracy_score'] = {
                'mean_ring': acc.mean_ring,
                'group_radius': acc.group_radius,
                'center_offset': acc.center_offset,
                'ring_score': acc.ring_score,
                'group_score': acc.group_score,
                'offset_score': acc.offset_score,
                'total_score': acc.total_score,
            }
        except AccuracyScore.DoesNotExist:
            pass

        # 综合评分
        try:
            ov = OverallScore.objects.get(session=session)
            data['overall_score'] = {
                'motion_weight': ov.motion_weight,
                'accuracy_weight': ov.accuracy_weight,
                'total_score': ov.total_score,
            }
        except OverallScore.DoesNotExist:
            pass

        # 诊断
        try:
            diag = IssueDiagnosis.objects.get(session=session)
            data['diagnosis'] = {'issues': diag.issues or []}
        except IssueDiagnosis.DoesNotExist:
            data['diagnosis'] = {'issues': []}

        # 建议
        try:
            rec = Recommendation.objects.get(session=session)
            data['recommendation'] = {'items': rec.items or []}
        except Recommendation.DoesNotExist:
            data['recommendation'] = {'items': []}

        # 等级
        try:
            rating = SkillRating.objects.get(user=request.user)
            data['skill_level'] = rating.current_level
        except SkillRating.DoesNotExist:
            data['skill_level'] = 'L1'

        return Response(data)


class HistoryPageViewSet(viewsets.GenericViewSet):
    """历史记录页 —— 训练历史 + 趋势"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def records(self, request):
        """
        GET /api/page/history/records/?page=1&page_size=20
        返回历史训练列表 + 等级趋势
        """
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        offset = (page - 1) * page_size

        sessions = TrainingSession.objects.filter(
            user=request.user, status='completed',
        ).select_related('result', 'motion_score', 'accuracy_score', 'overall_score')[
            offset:offset + page_size
        ]

        history = []
        for s in sessions:
            item = {
                'session_id': str(s.id),
                'total_shots': s.total_shots,
                'duration_seconds': s.duration_seconds,
                'created_at': s.created_at.isoformat() if s.created_at else None,
                'avg_ring': s.result.avg_ring if hasattr(s, 'result') and s.result else None,
                'motion_score': s.motion_score.total_score if hasattr(s, 'motion_score') else None,
                'accuracy_score': s.accuracy_score.total_score if hasattr(s, 'accuracy_score') else None,
                'overall_score': s.overall_score.total_score if hasattr(s, 'overall_score') else None,
            }
            history.append(item)

        skill_level = None
        ema_data = None
        try:
            rating = SkillRating.objects.get(user=request.user)
            skill_level = rating.current_level
            ema_data = {
                'ema_motion_score': rating.ema_motion_score,
                'ema_accuracy_score': rating.ema_accuracy_score,
                'total_sessions': rating.total_sessions_analyzed,
            }
        except SkillRating.DoesNotExist:
            pass

        return Response({
            'history': history,
            'skill_level': skill_level,
            'ema': ema_data,
            'page': page,
            'page_size': page_size,
            'total': TrainingSession.objects.filter(
                user=request.user, status='completed'
            ).count(),
        })


class HomePageViewSet(viewsets.GenericViewSet):
    """首页 —— 数据聚合"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/page/home/
        返回首页需要的聚合数据（最近训练、等级、推荐 Drill）
        """
        # 最近一次训练
        last_session = TrainingSession.objects.filter(
            user=request.user, status='completed',
        ).select_related('result', 'overall_score').first()

        recent = None
        if last_session:
            recent = {
                'session_id': str(last_session.id),
                'total_shots': last_session.total_shots,
                'created_at': last_session.created_at.isoformat() if last_session.created_at else None,
                'avg_ring': last_session.result.avg_ring if hasattr(last_session, 'result') and last_session.result else None,
                'overall_score': last_session.overall_score.total_score if hasattr(last_session, 'overall_score') else None,
            }

        # 等级
        skill_level = 'L1'
        try:
            rating = SkillRating.objects.get(user=request.user)
            skill_level = rating.current_level
        except SkillRating.DoesNotExist:
            pass

        # 总统计
        total_sessions = TrainingSession.objects.filter(
            user=request.user, status='completed'
        ).count()
        total_shots = sum(
            TrainingSession.objects.filter(
                user=request.user, status='completed'
            ).values_list('total_shots', flat=True)
        )

        # 最近的训练建议（从最近一次有诊断的 session 中取）
        last_diag = IssueDiagnosis.objects.filter(
            session__user=request.user,
        ).select_related('session').order_by('-created_at').first()

        focus_issues = last_diag.issues if last_diag else []

        return Response({
            'recent_session': recent,
            'skill_level': skill_level,
            'total_sessions': total_sessions,
            'total_shots': total_shots,
            'focus_issues': focus_issues,
        })
