from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FirmwareViewSet, FirmwareUpdateLogViewSet

router = DefaultRouter()
router.register('firmwares', FirmwareViewSet, basename='firmware')
router.register('logs', FirmwareUpdateLogViewSet, basename='update-log')

urlpatterns = [
    path('', include(router.urls)),
]
