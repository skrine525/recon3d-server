from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from upload_files.models import UploadedFile
from reconstruction.models import Reconstruction
from identification.utils.improc import process_image
from reconstruction.utils.planproc import get_user_pos
from .serializers import IdentificationInputSerializer, IdentificationSerializer
from identification.models import Identification
import json
import os
from identification.tasks import run_identification_task

class IdentificationCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = IdentificationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reconstruction_id = serializer.validated_data['reconstruction_id']
        file_id = serializer.validated_data['file_id']
        # Проверяем, что файл существует и source_type=2
        try:
            file = UploadedFile.objects.get(id=file_id, source_type=2)
        except UploadedFile.DoesNotExist:
            return Response({'detail': 'Файл не найден или имеет неверный source_type'}, status=status.HTTP_404_NOT_FOUND)
        # Создаём объект Identification
        identification = Identification.objects.create(
            created_by=request.user,
            status=Identification.Status.QUEUED
        )
        # Запускаем асинхронную задачу
        run_identification_task.delay(identification.id, file_id, reconstruction_id)
        return Response(IdentificationSerializer(identification).data, status=status.HTTP_201_CREATED)

class IdentificationRetrieveView(generics.RetrieveAPIView):
    queryset = Identification.objects.all()
    serializer_class = IdentificationSerializer
    lookup_field = 'id'

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        # Только свои или если staff/superuser
        if user.is_staff or user.is_superuser:
            return Identification.objects.all()
        return Identification.objects.filter(created_by=user) 