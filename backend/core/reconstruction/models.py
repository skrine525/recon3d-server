from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class InitialMaskFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_upload_file_id = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initial_masks')
    file_path = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Файл исходной маски'
        verbose_name_plural = 'Файлы исходных масок'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.id} ({self.created_at:%Y-%m-%d %H:%M})'

class HoughPreviewFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_upload_file_id = models.UUIDField()
    user_mask_upload_file_id = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hough_previews')
    file_path = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Hough preview файл'
        verbose_name_plural = 'Hough preview файлы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.id} ({self.created_at:%Y-%m-%d %H:%M})'

class Reconstruction(models.Model):
    id = models.AutoField(primary_key=True)
    mesh_file_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reconstructions')
    is_saved = models.BooleanField(default=False)
    saved_at = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        verbose_name = '3D реконструкция'
        verbose_name_plural = '3D реконструкции'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.id} ({self.created_at:%Y-%m-%d %H:%M})'
