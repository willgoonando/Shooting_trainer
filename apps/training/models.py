import uuid
from django.db import models


class DrillTemplate(models.Model):
    """训练 Drill 模板"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, verbose_name='Drill 名称')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    cartridge_type = models.CharField(max_length=64, blank=True, default='', verbose_name='Cartridge 类型')
    difficulty = models.CharField(
        max_length=20, blank=True, default='',
        choices=[('beginner', '入门'), ('intermediate', '中级'), ('advanced', '高级')],
        verbose_name='难度'
    )
    default_params = models.JSONField(default=dict, verbose_name='默认参数')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'drill_templates'
        verbose_name = 'Drill 模板'
        verbose_name_plural = verbose_name


class TrainingSession(models.Model):
    """一次训练 Session —— 包含 N 枪, N>=10 才输出稳定评分"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sessions', verbose_name='用户')
    device = models.ForeignKey('devices.Device', on_delete=models.SET_NULL, null=True, related_name='sessions', verbose_name='设备')
    drill_template = models.ForeignKey(DrillTemplate, on_delete=models.SET_NULL, null=True, related_name='sessions', verbose_name='Drill 模板')
    target = models.ForeignKey('targets.Target', on_delete=models.SET_NULL, null=True, related_name='sessions', verbose_name='靶纸')
    distance_meters = models.FloatField(null=True, blank=True, verbose_name='距离(米)')
    status = models.CharField(
        max_length=20, default='created',
        choices=[('created', '已创建'), ('in_progress', '训练中'), ('paused', '已暂停'), ('completed', '已完成'), ('aborted', '已中止')],
        verbose_name='状态'
    )
    total_shots = models.PositiveIntegerField(default=0, verbose_name='总枪数')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, verbose_name='持续时长(秒)')
    notes = models.TextField(blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'training_sessions'
        ordering = ['-created_at']
        verbose_name = '训练 Session'
        verbose_name_plural = verbose_name


class Shot(models.Model):
    """单枪数据 —— 包含 IMU 时间窗和可选的命中点"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='shots', verbose_name='所属 Session')
    shot_number = models.PositiveIntegerField(verbose_name='枪序号')
    imu_data = models.JSONField(default=dict, verbose_name='IMU 数据', help_text='加速度计和陀螺仪时间序列，窗口-200ms~+100ms')
    trigger_timestamp = models.DateTimeField(null=True, blank=True, verbose_name='击发时刻')
    hit_x = models.FloatField(null=True, blank=True, verbose_name='命中 X 坐标')
    hit_y = models.FloatField(null=True, blank=True, verbose_name='命中 Y 坐标')
    hit_ring = models.FloatField(null=True, blank=True, verbose_name='命中环数')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shots'
        ordering = ['shot_number']
        unique_together = [['session', 'shot_number']]
        verbose_name = '单枪数据'
        verbose_name_plural = verbose_name


class TrainingResult(models.Model):
    """训练结果聚合 —— 对应文档 5.8 训练结果页"""
    session = models.OneToOneField(TrainingSession, on_delete=models.CASCADE, related_name='result', verbose_name='所属 Session')
    avg_ring = models.FloatField(null=True, blank=True, verbose_name='平均环数')
    group_radius_mm = models.FloatField(null=True, blank=True, verbose_name='散布半径(mm)')
    center_offset_mm = models.FloatField(null=True, blank=True, verbose_name='中心偏移(mm)')
    total_score = models.FloatField(null=True, blank=True, verbose_name='总分')
    scatter_data = models.JSONField(default=list, verbose_name='靶面散点数据')
    direction_data = models.JSONField(default=list, verbose_name='方向图数据')
    score_curve = models.JSONField(default=list, verbose_name='分数曲线')
    motion_data = models.JSONField(default=list, verbose_name='动作图数据')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_results'
        verbose_name = '训练结果'
        verbose_name_plural = verbose_name
