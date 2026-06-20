import uuid
from django.db import models


class Device(models.Model):
    """设备模型 —— 对应物理射击训练器"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='devices', verbose_name='拥有者')
    device_sn = models.CharField(max_length=64, unique=True, verbose_name='设备序列号')
    device_name = models.CharField(max_length=128, blank=True, default='', verbose_name='设备名称')
    firmware_version = models.CharField(max_length=32, blank=True, default='', verbose_name='固件版本')
    battery_level = models.SmallIntegerField(null=True, blank=True, verbose_name='电量百分比')
    is_bound = models.BooleanField(default=True, verbose_name='是否绑定')
    is_active = models.BooleanField(default=False, verbose_name='当前是否激活')
    mac_address = models.CharField(max_length=32, blank=True, default='', verbose_name='MAC地址')
    last_online_at = models.DateTimeField(null=True, blank=True, verbose_name='最后在线时间')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devices'
        verbose_name = '设备'
        verbose_name_plural = verbose_name


class DeviceStatusLog(models.Model):
    """设备状态上报日志"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='status_logs', verbose_name='设备')
    battery_level = models.SmallIntegerField(null=True, blank=True)
    firmware_version = models.CharField(max_length=32, blank=True, default='')
    signal_strength = models.SmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_status_logs'
        ordering = ['-created_at']
