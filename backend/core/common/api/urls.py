from django.urls import path
from . import views

app_name = 'common_api'

urlpatterns = [
    path('info/', views.InfoView.as_view(), name='info'),
    path('users/<int:pk>/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('users/<int:pk>/change-is-staff/', views.ChangeIsStaffView.as_view(), name='change-is-staff'),
    path('users/<int:pk>/change-is-superuser/', views.ChangeIsSuperUserView.as_view(), name='change-is-superuser'),
    path('users/<int:pk>/change-is-active/', views.ChangeIsActiveView.as_view(), name='change-is-active'),
] 