from django.contrib import admin
from django.urls import path, include, re_path
from .swagger import schema_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('djoser.urls')),  # Пользовательские эндпоинты
    path('api/v1/', include('djoser.urls.jwt')),  # JWT эндпоинты
    path('api/v1/mobile/', include('mobile.urls')),  # Мобильные эндпоинты
    
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
