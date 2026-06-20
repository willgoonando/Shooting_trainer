import uuid
from django.db import models


class Firmware(models.Model):
    """固件版本"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_model = models.CharField(max_length=64, verbose_name='设备型号')
    version = models.CharField(max_length=32, verbose_name='版本号')
    release_notes = models.TextField(blank=True, default='', verbose_name='更新说明')
    file_url = models.URLField(verbose_name='固件文件地址')
    file_size_bytes = models.PositiveBigIntegerField(default=0, verbose_name='文件大小')
    checksum = models.CharField(max_length=128, verbose_name='校验和')
    is_force_update = models.BooleanField(default=False, verbose_name='是否强制升级')
    min_battery_required = models.SmallIntegerField(default=20, verbose_name='最低电量要求')
    status = models.CharField(
        max_length=20, default='draft',
        choices=[('draft', '草稿'), ('published', '已发布'), ('revoked', '已撤销')],
        verbose_name='状态'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'firmwares'
        ordering = ['-created_at']
        verbose_name = '固件'
        verbose_name_plural = verbose_name


class FirmwareUpdateLog(models.Model):
    """固件升级记录"""
    device = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='update_logs', verbose_name='设备')
    firmware = models.ForeignKey(Firmware, on_delete=models.PROTECT, related_name='update_logs', verbose_name='固件')
    from_version = models.CharField(max_length=32, verbose_name='升级前版本')
    to_version = models.CharField(max_length=32, verbose_name='升级后版本')
    status = models.CharField(
        max_length=20, default='pending',
        choices=[('pending', '待升级'), ('downloading', '下载中'), ('upgrading', '升级中'), ('success', '成功'), ('failed', '失败')],
        verbose_name='状态'
    )
    error_message = models.TextField(blank=True, default='', verbose_name='错误信息')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'firmware_update_logs'
        ordering = ['-created_at']
        verbose_name = '固件升级记录'
        verbose_name_plural = verbose_name
