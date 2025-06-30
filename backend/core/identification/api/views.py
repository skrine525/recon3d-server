from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from upload_files.models import UploadedFile
from reconstruction.models import Reconstruction
from identification.utils.improc import process_image
from reconstruction.utils.planproc import get_user_pos
from .serializers import IdentificationInputSerializer
import json
import os

class IdentificationCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = IdentificationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reconstruction_id = serializer.validated_data['reconstruction_id']
        file_id = serializer.validated_data['file_id']
        scale = serializer.validated_data['scale']
        try:
            reconstruction = Reconstruction.objects.get(id=reconstruction_id)
        except Reconstruction.DoesNotExist:
            return Response({'detail': 'Реконструкция не найдена'}, status=status.HTTP_404_NOT_FOUND)
        try:
            file = UploadedFile.objects.get(id=file_id, source_type=2)
        except UploadedFile.DoesNotExist:
            return Response({'detail': 'Файл не найден или имеет неверный source_type'}, status=status.HTTP_404_NOT_FOUND)
        file_path = file.file_path
        # Абсолютный путь
        from django.conf import settings
        abs_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
        # Получаем признаки с фото
        signs_photo = process_image(abs_file_path)
        # Получаем признаки с плана
        if not reconstruction.plan_signs:
            return Response({'detail': 'На плане реконструкции не были распознаны знаки'}, status=status.HTTP_400_BAD_REQUEST)
        # Вызываем get_user_pos
        user_pos = get_user_pos(reconstruction.plan_signs, signs_photo, scale)
        # user_pos должен быть dict с ключами x, y, angle
        x = user_pos.get('x')
        y = user_pos.get('y')
        angle = user_pos.get('angle')
        return Response({'x': x, 'y': y, 'angle': angle}, status=status.HTTP_200_OK) 