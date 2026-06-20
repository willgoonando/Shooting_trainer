import uuid
from django.db import models


class TargetTemplate(models.Model):
    """靶纸模板"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, verbose_name='靶纸名称')
    image_url = models.URLField(blank=True, default='', verbose_name='靶纸图片')
    ring_count = models.SmallIntegerField(default=10, verbose_name='环数')
    ring_definitions = models.JSONField(default=list, verbose_name='环定义', help_text='每环的半径定义(mm)')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'target_templates'
        verbose_name = '靶纸模板'
        verbose_name_plural = verbose_name


class Target(models.Model):
    """具体靶纸（关联到 Session）"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(TargetTemplate, on_delete=models.PROTECT, related_name='targets', verbose_name='靶纸模板')
    distance_meters = models.FloatField(default=10.0, verbose_name='距离(米)')
    calibration = models.JSONField(default=dict, verbose_name='标定信息')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'targets'
        verbose_name = '靶纸'
        verbose_name_plural = verbose_name
