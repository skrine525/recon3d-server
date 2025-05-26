from django.urls import path
from .views import MetaView

app_name = 'mobile'

urlpatterns = [
    path('meta/', MetaView.as_view(), name='meta'),
] 