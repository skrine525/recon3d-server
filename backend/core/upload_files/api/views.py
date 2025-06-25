from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.conf import settings
import os
import uuid
from upload_files.models import UploadedFile
from .serializers import UploadedFileSerializer

class UploadedFileViewSet(mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

class BaseFileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    file_type = UploadedFile.FileType.PHOTO
    source_type = None
    folder = None

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'Файл обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UploadedFileSerializer(data={'file': file}, context={'request': request})
        serializer.is_valid(raise_exception=True)

        file_uuid = uuid.uuid4()
        ext = os.path.splitext(file.name)[1].lower() or '.jpg'

        rel_path = f'{self.folder}{file_uuid}{ext}'
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        instance = UploadedFile.objects.create(
            id=file_uuid,
            file_type=self.file_type,
            source_type=self.source_type,
            file_path=rel_path,
            uploaded_by=request.user,
            uploaded_at=timezone.now()
        )
        response_serializer = UploadedFileSerializer(instance, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class PlanPhotoUploadView(BaseFileUploadView):
    source_type = UploadedFile.SourceType.PLAN_2D
    folder = 'uploads/plan-photos/'

class UserEnvironmentPhotoUploadView(BaseFileUploadView):
    source_type = UploadedFile.SourceType.USER_ENV
    folder = 'uploads/user-environment-photos/'

class UserMaskFileUploadView(BaseFileUploadView):
    source_type = UploadedFile.SourceType.USER_MASK
    folder = 'uploads/user-mask-photos/' 