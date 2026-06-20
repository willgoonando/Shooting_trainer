from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    # API 文档（开发环境访问 /api/docs/）
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # 业务模块路由
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/devices/', include('apps.devices.urls')),
    path('api/v1/training/', include('apps.training.urls')),
    path('api/v1/targets/', include('apps.targets.urls')),
    path('api/v1/courses/', include('apps.courses.urls')),
    path('api/v1/ota/', include('apps.ota.urls')),
    path('api/v1/ai/', include('apps.ai_coach.urls')),
]
