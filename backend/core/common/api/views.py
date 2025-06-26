from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import ChangePasswordSerializer, ChangeFlagSerializer
from .permissions import IsSuperUser, CanChangePassword, CanChangeIsActive

User = get_user_model()

class InfoView(APIView):
    """
    Эндпоинт для проверки работоспособности приложения.
    В будущем будет возвращать информацию о приложении.
    """
    permission_classes = []  # Разрешаем доступ без аутентификации

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, CanChangePassword]
    serializer_class = ChangePasswordSerializer
    http_method_names = ['put']

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseChangeFlagView(UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser]
    serializer_class = ChangeFlagSerializer
    http_method_names = ['put']
    flag_name = None

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        setattr(user, self.flag_name, serializer.validated_data['value'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangeIsStaffView(BaseChangeFlagView):
    flag_name = 'is_staff'

class ChangeIsSuperUserView(BaseChangeFlagView):
    flag_name = 'is_superuser'

class ChangeIsActiveView(BaseChangeFlagView):
    """
    Изменяет статус is_active для пользователя.
    """
    permission_classes = [IsAuthenticated, CanChangeIsActive]
    flag_name = 'is_active'
