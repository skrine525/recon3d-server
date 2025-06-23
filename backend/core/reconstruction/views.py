from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import CalculateInitialMaskSerializer, InitialMaskFileSerializer
from .models import InitialMaskFile
from upload_files.models import UploadedFile
from django.conf import settings
from django.utils import timezone
import uuid
import os
from core import config
from .utils.plan2reconstruction import get_initial_mask_and_image
from PIL import Image
import numpy as np

class CalculateInitialMaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CalculateInitialMaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_id = serializer.validated_data['file_id']
        try:
            upload_file = UploadedFile.objects.get(id=file_id)
        except UploadedFile.DoesNotExist:
            return Response({'detail': 'Файл не найден'}, status=status.HTTP_404_NOT_FOUND)
        # Проверка типа файла
        if upload_file.file_type != UploadedFile.FileType.PHOTO or upload_file.source_type != UploadedFile.SourceType.PLAN_2D:
            return Response({'detail': 'Файл должен быть фото 2D-плана'}, status=status.HTTP_400_BAD_REQUEST)
        # Получаем абсолютный путь к исходному файлу
        src_path = os.path.join(settings.MEDIA_ROOT, upload_file.file_path)
        # Вызываем функцию из utils
        mask, orig_img = get_initial_mask_and_image(src_path)
        # Сохраняем результат
        mask_uuid = uuid.uuid4()
        mask_rel_path = f'initial-mask/{mask_uuid}.png'
        mask_abs_path = os.path.join(settings.MEDIA_ROOT, mask_rel_path)
        os.makedirs(os.path.dirname(mask_abs_path), exist_ok=True)
        # Преобразуем mask в PIL.Image, если это numpy.ndarray
        if isinstance(mask, np.ndarray):
            mask = Image.fromarray(mask)
        mask.save(mask_abs_path)
        # Создаем запись
        mask_obj = InitialMaskFile.objects.create(
            id=mask_uuid,
            source_upload_file_id=upload_file.id,
            created_at=timezone.now(),
            created_by=request.user,
            file_path=mask_rel_path
        )
        return Response(InitialMaskFileSerializer(mask_obj).data, status=status.HTTP_201_CREATED) 