from django.urls import path
from .views import IdentificationCreateView, IdentificationRetrieveView

urlpatterns = [
    path('identifications', IdentificationCreateView.as_view(), name='identification-create'),
    path('identifications/<int:id>', IdentificationRetrieveView.as_view(), name='identification-detail'),
] 