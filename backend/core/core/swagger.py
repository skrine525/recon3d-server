from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .config import APPLICATION_URL


schema_view = get_schema_view(
    openapi.Info(
        title="3D Diplom",
        default_version='v1',
        description="3D Diplom description",
    ),
    url=APPLICATION_URL,
    public=True,
    permission_classes=(permissions.AllowAny,),
) 