import uuid
from django.db import models


class TargetTemplate(models.Model):
    """靶纸模板 —— 支持图片上传 + 环定义"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, verbose_name='靶纸名称')
    category = models.CharField(
        max_length=20, default='standard',
        choices=[
            ('standard', '标准环靶'),
            ('silhouette', '人形靶'),
            ('ipsc', 'IPSC靶'),
            ('steel', '钢靶'),
            ('custom', '自定义'),
        ],
        verbose_name='靶纸类型'
    )
    image = models.ImageField(upload_to='targets/', blank=True, null=True, verbose_name='靶纸图片')
    image_url = models.URLField(blank=True, default='', verbose_name='外部图片链接（备用）')
    ring_count = models.SmallIntegerField(default=10, verbose_name='环数')
    ring_definitions = models.JSONField(default=list, verbose_name='环定义', help_text='每环的半径定义(mm)，例如 [{"ring":10,"radius_mm":50},...]')
    width_mm = models.FloatField(default=170.0, verbose_name='靶纸宽度(mm)')
    height_mm = models.FloatField(default=170.0, verbose_name='靶纸高度(mm)')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'target_templates'
        verbose_name = '靶纸模板'
        verbose_name_plural = verbose_name

    def get_image_url(self):
        """返回可用的图片URL（优先本地图片，fallback到外部链接）"""
        if self.image:
            return self.image.url
        return self.image_url


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
