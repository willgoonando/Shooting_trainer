import uuid
from django.db import models


class Course(models.Model):
    """课程/教程"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256, verbose_name='课程标题')
    description = models.TextField(blank=True, default='', verbose_name='课程描述')
    cover_image = models.URLField(blank=True, default='', verbose_name='封面图')
    difficulty = models.CharField(
        max_length=20, blank=True, default='',
        choices=[('beginner', '入门'), ('intermediate', '中级'), ('advanced', '高级')],
        verbose_name='难度'
    )
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['sort_order']
        verbose_name = '课程'
        verbose_name_plural = verbose_name


class CourseSection(models.Model):
    """课程章节"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections', verbose_name='所属课程')
    title = models.CharField(max_length=256, verbose_name='章节标题')
    content = models.TextField(blank=True, default='', verbose_name='章节内容')
    video_url = models.URLField(blank=True, default='', verbose_name='视频链接')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_sections'
        ordering = ['sort_order']
        verbose_name = '课程章节'
        verbose_name_plural = verbose_name
