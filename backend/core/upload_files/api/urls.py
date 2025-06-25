from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadedFileViewSet, PlanPhotoUploadView, UserEnvironmentPhotoUploadView, UserMaskFileUploadView

router = DefaultRouter()
router.register(r'files', UploadedFileViewSet, basename='uploadedfile')

urlpatterns = [
    path('plan-photo/', PlanPhotoUploadView.as_view(), name='plan-photo-upload'),
    path('user-environment-photo/', UserEnvironmentPhotoUploadView.as_view(), name='user-environment-photo-upload'),
    path('user-mask/', UserMaskFileUploadView.as_view(), name='user-mask-upload'),
    path('', include(router.urls)),
] 