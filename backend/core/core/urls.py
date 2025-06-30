from django.contrib import admin
from django.urls import path, include
from .swagger import schema_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('mainpage.urls')),
    path('admin/', admin.site.urls),
    path('api/v1/', include('djoser.urls')),  # Пользовательские эндпоинты
    path('api/v1/', include('djoser.urls.authtoken')),  # Эндпоинты для обычных токенов
    path('api/v1/common/', include('common.api.urls')),  # Общие эндпоинты
    path('api/v1/upload/', include('upload_files.api.urls')),  # Загрузка файлов
    path('api/v1/reconstruction/', include('reconstruction.api.urls')),  # Reconstruction API
    path('api/v1/identification/', include('identification.api.urls')),
    path('', include('mesh_render.urls')),
    
    # Swagger URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
