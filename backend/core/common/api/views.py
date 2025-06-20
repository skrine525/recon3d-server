from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class MetaView(APIView):
    """
    Эндпоинт для проверки работоспособности приложения.
    В будущем будет возвращать метаданные приложения.
    """
    permission_classes = []  # Разрешаем доступ без аутентификации

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)