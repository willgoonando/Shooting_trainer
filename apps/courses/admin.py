from django.contrib import admin
from .models import Course, CourseSection


class CourseSectionInline(admin.TabularInline):
    model = CourseSection
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'is_active', 'sort_order']
    list_filter = ['difficulty', 'is_active']
    inlines = [CourseSectionInline]
