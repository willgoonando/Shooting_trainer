import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """用户模型 —— 基于 Django AbstractUser 扩展"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name='邮箱')
    nickname = models.CharField(max_length=64, blank=True, default='', verbose_name='昵称')
    avatar = models.URLField(blank=True, default='', verbose_name='头像')
    gender = models.CharField(
        max_length=10, blank=True, default='',
        choices=[('male', '男'), ('female', '女'), ('other', '其他')],
        verbose_name='性别'
    )
    training_frequency = models.SmallIntegerField(null=True, blank=True, verbose_name='每周训练频次')
    session_duration_minutes = models.SmallIntegerField(null=True, blank=True, verbose_name='单次训练时长(分钟)')
    focus_area = models.CharField(max_length=128, blank=True, default='', verbose_name='重点提升方向')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class EmailVerification(models.Model):
    """邮箱验证码"""
    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=[('register', '注册'), ('reset_password', '重置密码')])
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_verifications'
