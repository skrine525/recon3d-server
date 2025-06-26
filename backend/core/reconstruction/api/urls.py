from django.urls import path
from .views import CalculateInitialMaskView, CalculateHoughView, CalculateMeshView, SaveReconstructionView

urlpatterns = [
    path('initial-masks', CalculateInitialMaskView.as_view(), name='initial-masks'),
    path('houghs', CalculateHoughView.as_view(), name='houghs'),
    path('reconstructions', CalculateMeshView.as_view(), name='reconstructions'),
    path('reconstructions/<int:id>/save', SaveReconstructionView.as_view(), name='save-reconstruction'),
] 