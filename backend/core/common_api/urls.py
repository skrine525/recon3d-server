from django.urls import path
from . import views

app_name = 'common_api'

urlpatterns = [
    path('meta/', views.MetaView.as_view(), name='meta'),
] 