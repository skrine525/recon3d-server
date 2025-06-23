from django.urls import path
from .views import CalculateInitialMaskView

urlpatterns = [
    path('calculate-initial-mask', CalculateInitialMaskView.as_view(), name='calculate-initial-mask'),
] 