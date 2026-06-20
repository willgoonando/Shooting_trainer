from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIResultViewSet, SkillRatingViewSet, TrainingPlanViewSet

router = DefaultRouter()
router.register('results', AIResultViewSet, basename='ai-result')
router.register('skill', SkillRatingViewSet, basename='skill-rating')
router.register('plans', TrainingPlanViewSet, basename='training-plan')

urlpatterns = [
    path('', include(router.urls)),
]
