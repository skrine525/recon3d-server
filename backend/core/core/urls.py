from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from .swagger import schema_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('djoser.urls')),  # Пользовательские эндпоинты
    path('api/v1/', include('djoser.urls.jwt')),  # JWT эндпоинты
    path('api/v1/common/', include('common_api.urls')),  # Мобильные эндпоинты
    
    # Swagger URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
