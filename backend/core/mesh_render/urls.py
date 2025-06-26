from django.urls import path
from . import views

app_name = 'mesh_render'

urlpatterns = [
    path('mesh/<int:id>/', views.mesh_view, name='mesh_view'),
] 