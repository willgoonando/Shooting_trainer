from rest_framework import serializers
from .models import Course, CourseSection


class CourseSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSection
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class CourseSerializer(serializers.ModelSerializer):
    sections = CourseSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
