from django.urls import path
from .views import CalculateInitialMaskView, CalculateHoughView, CalculateMeshView

urlpatterns = [
    path('calculate-initial-mask', CalculateInitialMaskView.as_view(), name='calculate-initial-mask'),
    path('calculate-hough', CalculateHoughView.as_view(), name='calculate-hough'),
    path('calculate-mesh', CalculateMeshView.as_view(), name='calculate-mesh'),
] 