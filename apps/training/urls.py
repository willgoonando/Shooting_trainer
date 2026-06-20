from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DrillTemplateViewSet, TrainingSessionViewSet

router = DefaultRouter()
router.register('drills', DrillTemplateViewSet, basename='drill')
router.register('sessions', TrainingSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
]
