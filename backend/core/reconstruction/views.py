from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import CalculateInitialMaskSerializer, InitialMaskFileSerializer, CalculateHoughSerializer, HoughPreviewFileSerializer
from .models import InitialMaskFile, HoughPreviewFile
from upload_files.models import UploadedFile
from django.conf import settings
from django.utils import timezone
import uuid
import os
from core import config
from .utils.plan2reconstruction import get_initial_mask_and_image, process_and_get_hough_preview
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

class CalculateHoughView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CalculateHoughSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan_file_id = serializer.validated_data['plan_file_id']
        user_mask_file_id = serializer.validated_data['user_mask_file_id']
        try:
            plan_file = UploadedFile.objects.get(id=plan_file_id)
        except UploadedFile.DoesNotExist:
            return Response({'detail': 'План не найден'}, status=status.HTTP_404_NOT_FOUND)
        if plan_file.file_type != UploadedFile.FileType.PHOTO or plan_file.source_type != UploadedFile.SourceType.PLAN_2D:
            return Response({'detail': 'plan_file_id должен быть фото 2D-плана'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_mask_file = UploadedFile.objects.get(id=user_mask_file_id)
        except UploadedFile.DoesNotExist:
            return Response({'detail': 'Маска не найдена'}, status=status.HTTP_404_NOT_FOUND)
        if user_mask_file.file_type != UploadedFile.FileType.PHOTO or user_mask_file.source_type != UploadedFile.SourceType.USER_MASK:
            return Response({'detail': 'user_mask_file_id должен быть маской пользователя'}, status=status.HTTP_400_BAD_REQUEST)
        plan_path = os.path.join(settings.MEDIA_ROOT, plan_file.file_path)
        user_mask_path = os.path.join(settings.MEDIA_ROOT, user_mask_file.file_path)
        # Вызываем функцию
        preview_img, lines = process_and_get_hough_preview(plan_path, user_mask_path)
        # Сохраняем результат
        hough_uuid = uuid.uuid4()
        hough_rel_path = f'hough/{hough_uuid}.png'
        hough_abs_path = os.path.join(settings.MEDIA_ROOT, hough_rel_path)
        os.makedirs(os.path.dirname(hough_abs_path), exist_ok=True)
        # Преобразуем preview_img в PIL.Image, если это numpy.ndarray
        if isinstance(preview_img, np.ndarray):
            preview_img = Image.fromarray(preview_img)
        preview_img.save(hough_abs_path)
        # Создаем запись
        hough_obj = HoughPreviewFile.objects.create(
            id=hough_uuid,
            plan_upload_file_id=plan_file.id,
            user_mask_upload_file_id=user_mask_file.id,
            created_at=timezone.now(),
            created_by=request.user,
            file_path=hough_rel_path
        )
        return Response(HoughPreviewFileSerializer(hough_obj).data, status=status.HTTP_201_CREATED) 