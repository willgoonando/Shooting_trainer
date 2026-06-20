from rest_framework import viewsets
from .models import Course, CourseSection
from .serializers import CourseSerializer, CourseSectionSerializer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """课程 —— 只读"""
    queryset = Course.objects.filter(is_active=True).prefetch_related('sections')
    serializer_class = CourseSerializer


class CourseSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """课程章节 —— 只读"""
    queryset = CourseSection.objects.all()
    serializer_class = CourseSectionSerializer
