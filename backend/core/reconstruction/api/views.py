from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import (
    CalculateInitialMaskSerializer, InitialMaskFileSerializer,
    CalculateHoughSerializer, HoughPreviewFileSerializer,
    CalculateMeshSerializer, ReconstructionSerializer,
    SaveReconstructionSerializer,
    RoomsUpdateSerializer
)
from reconstruction.models import InitialMaskFile, HoughPreviewFile, Reconstruction
from upload_files.models import UploadedFile
from django.conf import settings
from django.utils import timezone
import uuid
import os
from core import config
from reconstruction.utils.plan2reconstruction import get_initial_mask_and_image, process_and_get_hough_preview, lines_to_3d, save_mesh, reconstruct_3d_from_plan
from PIL import Image
import numpy as np
import cv2
from rest_framework.parsers import JSONParser
from rest_framework import generics, mixins
from reconstruction.tasks import create_reconstruction_task

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
        if upload_file.file_type != UploadedFile.FileType.PHOTO or upload_file.source_type != UploadedFile.SourceType.PLAN_2D:
            return Response({'detail': 'Файл должен быть фото 2D-плана'}, status=status.HTTP_400_BAD_REQUEST)
        src_path = os.path.join(settings.MEDIA_ROOT, upload_file.file_path)
        mask, orig_img = get_initial_mask_and_image(src_path)
        mask_uuid = uuid.uuid4()
        mask_rel_path = f'initial-mask/{mask_uuid}.png'
        mask_abs_path = os.path.join(settings.MEDIA_ROOT, mask_rel_path)
        os.makedirs(os.path.dirname(mask_abs_path), exist_ok=True)
        if isinstance(mask, np.ndarray):
            mask = Image.fromarray(mask)
        mask.save(mask_abs_path)
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
        preview_img, lines = process_and_get_hough_preview(plan_path, user_mask_path)
        hough_uuid = uuid.uuid4()
        hough_rel_path = f'hough/{hough_uuid}.png'
        hough_abs_path = os.path.join(settings.MEDIA_ROOT, hough_rel_path)
        os.makedirs(os.path.dirname(hough_abs_path), exist_ok=True)
        if isinstance(preview_img, np.ndarray):
            preview_img = Image.fromarray(preview_img)
        preview_img.save(hough_abs_path)
        hough_obj = HoughPreviewFile.objects.create(
            id=hough_uuid,
            plan_upload_file_id=plan_file.id,
            user_mask_upload_file_id=user_mask_file.id,
            created_at=timezone.now(),
            created_by=request.user,
            file_path=hough_rel_path
        )
        return Response(HoughPreviewFileSerializer(hough_obj).data, status=status.HTTP_201_CREATED)

class ReconstructionListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReconstructionSerializer

    def get_queryset(self):
        queryset = Reconstruction.objects.all()
        is_saved = self.request.query_params.get('is_saved')
        if is_saved is not None:
            if is_saved.lower() in ['1', 'true', 'yes']:
                queryset = queryset.filter(saved_at__isnull=False)
            elif is_saved.lower() in ['0', 'false', 'no']:
                queryset = queryset.filter(saved_at__isnull=True)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = CalculateMeshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_file_id = serializer.validated_data['plan_file_id']
        user_mask_file_id = serializer.validated_data['user_mask_file_id']

        # Проверяем существование файлов перед созданием объекта
        try:
            plan_file = UploadedFile.objects.get(id=plan_file_id, file_type=UploadedFile.FileType.PHOTO, source_type=UploadedFile.SourceType.PLAN_2D)
        except UploadedFile.DoesNotExist:
            return Response({'detail': 'Файл плана не найден или имеет неверный тип.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            user_mask_file = UploadedFile.objects.get(id=user_mask_file_id, file_type=UploadedFile.FileType.PHOTO, source_type=UploadedFile.SourceType.USER_MASK)
        except UploadedFile.DoesNotExist:
            return Response({'detail': 'Файл маски не найден или имеет неверный тип.'}, status=status.HTTP_404_NOT_FOUND)

        # Создаем объект реконструкции
        mesh_obj = Reconstruction.objects.create(
            created_by=request.user,
            status=Reconstruction.Status.QUEUED
        )

        # Запускаем асинхронную задачу
        create_reconstruction_task.delay(
            reconstruction_id=mesh_obj.id,
            plan_file_id=plan_file.id,
            user_mask_file_id=user_mask_file.id
        )

        # Возвращаем ответ
        response_serializer = self.get_serializer(mesh_obj)
        headers = self.get_success_headers(response_serializer.data)
        response = Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        response['X-Tab-Title'] = mesh_obj.get_name()
        return response

class SaveReconstructionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, id, *args, **kwargs):
        serializer = SaveReconstructionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data['name']
        try:
            reconstruction = Reconstruction.objects.get(id=id)
        except Reconstruction.DoesNotExist:
            return Response({'detail': 'Реконструкция не найдена'}, status=status.HTTP_404_NOT_FOUND)
        if reconstruction.created_by != request.user:
            return Response({'detail': 'Доступ запрещён: только создатель может сохранить реконструкцию'}, status=status.HTTP_403_FORBIDDEN)
        if reconstruction.saved_at is not None:
            return Response({'detail': 'Реконструкция уже сохранена'}, status=status.HTTP_400_BAD_REQUEST)
        reconstruction.name = name
        reconstruction.saved_at = timezone.now()
        reconstruction.save(update_fields=['name', 'saved_at'])
        return Response(ReconstructionSerializer(reconstruction).data, status=status.HTTP_200_OK)

class ReconstructionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReconstructionSerializer
    queryset = Reconstruction.objects.all()
    lookup_field = 'id'

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def get_queryset(self):
        # Теперь любой аутентифицированный пользователь может получить реконструкцию по id
        return Reconstruction.objects.all()

    def check_object_permissions(self, request, obj):
        user = request.user
        if request.method in ['PATCH', 'DELETE']:
            if not (obj.created_by == user or user.is_staff or user.is_superuser):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Можно изменять или удалять только свои реконструкции или если вы staff/superuser.')
        super().check_object_permissions(request, obj)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        name = request.data.get('name')
        if name is not None:
            instance.name = name
            instance.save(update_fields=['name'])
            return Response(self.get_serializer(instance).data)
        return Response({'detail': 'Only "name" can be updated.'}, status=400)

# Новый view для обновления комнат
class UpdateRoomsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, id, *args, **kwargs):
        serializer = RoomsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rooms = serializer.validated_data['rooms']
        try:
            reconstruction = Reconstruction.objects.get(id=id)
        except Reconstruction.DoesNotExist:
            return Response({'detail': 'Реконструкция не найдена'}, status=status.HTTP_404_NOT_FOUND)
        if reconstruction.created_by != request.user:
            return Response({'detail': 'Доступ запрещён: только создатель может обновлять комнаты'}, status=status.HTTP_403_FORBIDDEN)
        reconstruction.rooms = rooms
        reconstruction.save(update_fields=['rooms'])
        return Response({'rooms': reconstruction.rooms}, status=status.HTTP_200_OK) 