from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TargetTemplateViewSet, TargetViewSet

router = DefaultRouter()
router.register('templates', TargetTemplateViewSet, basename='target-template')
router.register('', TargetViewSet, basename='target')

urlpatterns = [
    path('', include(router.urls)),
]
