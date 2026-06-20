from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrainingResultPageViewSet, HistoryPageViewSet, HomePageViewSet

router = DefaultRouter()
router.register('training-result', TrainingResultPageViewSet, basename='page-training-result')
router.register('history', HistoryPageViewSet, basename='page-history')
router.register('home', HomePageViewSet, basename='page-home')

urlpatterns = [
    path('', include(router.urls)),
]
