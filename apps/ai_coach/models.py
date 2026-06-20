import uuid
from django.db import models


class MotionScore(models.Model):
    """F1: 动作评分 —— 基于 Trigger/Stability/Follow-through/Consistency"""
    session = models.OneToOneField('training.TrainingSession', on_delete=models.CASCADE, related_name='motion_score', verbose_name='所属 Session')
    trigger_control = models.FloatField(verbose_name='扳机控制分')
    stability = models.FloatField(verbose_name='稳定性分')
    follow_through = models.FloatField(verbose_name='Follow-through 分')
    consistency = models.FloatField(verbose_name='一致性分')
    total_score = models.FloatField(verbose_name='动作总分(Motion Score)')
    details = models.JSONField(default=dict, verbose_name='分项明细')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'motion_scores'
        verbose_name = '动作评分'
        verbose_name_plural = verbose_name


class AccuracyScore(models.Model):
    """F1: 准度评分 —— 0.45*Ring + 0.35*Group + 0.20*Offset"""
    session = models.OneToOneField('training.TrainingSession', on_delete=models.CASCADE, related_name='accuracy_score', verbose_name='所属 Session')
    mean_ring = models.FloatField(verbose_name='平均环数')
    group_radius = models.FloatField(verbose_name='散布半径')
    center_offset = models.FloatField(verbose_name='中心偏移')
    ring_score = models.FloatField(verbose_name='环数得分')
    group_score = models.FloatField(verbose_name='散布得分')
    offset_score = models.FloatField(verbose_name='偏移得分')
    total_score = models.FloatField(verbose_name='准度总分(Accuracy Score)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accuracy_scores'
        verbose_name = '准度评分'
        verbose_name_plural = verbose_name


class NeutralPenalty(models.Model):
    """F1: Neutral Penalty —— HoldTooLong/Timeout/Abort/Safety/ModeRule"""
    session = models.OneToOneField('training.TrainingSession', on_delete=models.CASCADE, related_name='neutral_penalty', verbose_name='所属 Session')
    hold_too_long_count = models.PositiveIntegerField(default=0)
    timeout_no_shot_count = models.PositiveIntegerField(default=0)
    abort_count = models.PositiveIntegerField(default=0)
    safety_violation_count = models.PositiveIntegerField(default=0)
    mode_rule_violation_count = models.PositiveIntegerField(default=0)
    total_penalty = models.FloatField(default=0, verbose_name='总罚分')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'neutral_penalties'
        verbose_name = '中性罚分'
        verbose_name_plural = verbose_name


class OverallScore(models.Model):
    """F1: 综合评分 = MotionWeight*MotionScore + AccuracyWeight*AccuracyScore - NeutralPenalty"""
    session = models.OneToOneField('training.TrainingSession', on_delete=models.CASCADE, related_name='overall_score', verbose_name='所属 Session')
    motion_weight = models.FloatField(default=0.5, verbose_name='动作权重')
    accuracy_weight = models.FloatField(default=0.5, verbose_name='准度权重')
    total_score = models.FloatField(verbose_name='综合总分(Overall Score)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'overall_scores'
        verbose_name = '综合评分'
        verbose_name_plural = verbose_name


class IssueDiagnosis(models.Model):
    """F2: 动作问题诊断 —— 输出 Top 1-3 问题标签"""
    session = models.OneToOneField('training.TrainingSession', on_delete=models.CASCADE, related_name='diagnosis', verbose_name='所属 Session')
    issues = models.JSONField(default=list, verbose_name='问题列表', help_text='每个问题包含 label/severity/description')
    accuracy_limitations = models.JSONField(default=list, verbose_name='准度限制因素')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'issue_diagnoses'
        verbose_name = '问题诊断'
        verbose_name_plural = verbose_name


class Recommendation(models.Model):
    """F3: 训练建议 —— 1-3条，每条对应具体 Drill"""
    session = models.OneToOneField('training.TrainingSession', on_delete=models.CASCADE, related_name='recommendation', verbose_name='所属 Session')
    items = models.JSONField(default=list, verbose_name='建议列表', help_text='每条包含 issue/drill/success_criteria')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recommendations'
        verbose_name = '训练建议'
        verbose_name_plural = verbose_name


class SkillRating(models.Model):
    """F4: 水平评估 —— Beginner→Advanced, 基于 EMA 滑动窗口, 最少 5 次 Session"""
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='skill_rating', verbose_name='用户')
    current_level = models.CharField(
        max_length=20, default='L1',
        choices=[('L1', 'Beginner'), ('L2', 'Novice'), ('L3', 'Intermediate'), ('L4', 'Advanced'), ('L5', 'Expert')],
        verbose_name='当前等级'
    )
    ema_motion_score = models.FloatField(default=0, verbose_name='EMA 动作分')
    ema_accuracy_score = models.FloatField(default=0, verbose_name='EMA 准度分')
    total_sessions_analyzed = models.PositiveIntegerField(default=0, verbose_name='已分析训练次数')
    trend_data = models.JSONField(default=list, verbose_name='趋势数据')
    # L4-L5 专属
    accuracy_mastery_level = models.CharField(max_length=20, blank=True, default='', verbose_name='准度精通等级')
    accuracy_profile = models.JSONField(default=dict, verbose_name='准度画像')
    next_accuracy_focus = models.CharField(max_length=128, blank=True, default='', verbose_name='下一步准度重点')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skill_ratings'
        verbose_name = '水平评估'
        verbose_name_plural = verbose_name


class TrainingPlan(models.Model):
    """F5: 训练计划 —— 7/14/30天"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='training_plans', verbose_name='用户')
    plan_type = models.CharField(max_length=10, choices=[('7d', '7天'), ('14d', '14天'), ('30d', '30天')], verbose_name='计划类型')
    daily_plans = models.JSONField(default=list, verbose_name='每日训练清单')
    completion_rate = models.FloatField(default=0, verbose_name='完成度')
    is_active = models.BooleanField(default=True, verbose_name='是否当前计划')
    started_at = models.DateField(null=True, blank=True, verbose_name='开始日期')
    ended_at = models.DateField(null=True, blank=True, verbose_name='结束日期')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_plans'
        ordering = ['-created_at']
        verbose_name = '训练计划'
        verbose_name_plural = verbose_name


class VoiceCoachingEvent(models.Model):
    """F6: 语音指导事件记录"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('training.TrainingSession', on_delete=models.CASCADE, related_name='voice_events', verbose_name='所属 Session')
    event_type = models.CharField(
        max_length=40,
        choices=[
            ('pre_trigger_jerk_risk', 'Pre-trigger jerk risk'),
            ('hold_too_long', 'Hold too long'),
            ('follow_through_too_short', 'Follow-through too short'),
            ('tempo_too_fast', 'Tempo too fast'),
            ('good_shot', 'Good shot reinforcement'),
        ],
        verbose_name='事件类型'
    )
    priority = models.CharField(
        max_length=20,
        choices=[('safety', 'Safety'), ('process', 'Process'), ('correction', 'Correction'), ('encouragement', 'Encouragement')],
        verbose_name='优先级'
    )
    message = models.TextField(verbose_name='语音消息文本')
    is_played = models.BooleanField(default=False, verbose_name='是否已播放')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'voice_coaching_events'
        ordering = ['created_at']
        verbose_name = '语音指导事件'
        verbose_name_plural = verbose_name
