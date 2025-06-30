from django.urls import path
from .views import IdentificationCreateView

urlpatterns = [
    path('identifications', IdentificationCreateView.as_view(), name='identification-create'),
] 