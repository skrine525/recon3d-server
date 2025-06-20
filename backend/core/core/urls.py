from django.contrib import admin
from django.urls import path, include
from .swagger import schema_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('djoser.urls')),  # Пользовательские эндпоинты
    path('api/v1/', include('djoser.urls.authtoken')),  # Эндпоинты для обычных токенов
    path('api/v1/common/', include('common.api.urls')),  # Общие эндпоинты
    
    # Swagger URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
