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
    class Status(models.IntegerChoices):
        QUEUED = 1, 'В очереди'
        IN_PROGRESS = 2, 'В обработке'
        DONE = 3, 'Готово'
        FAILED = 4, 'Ошибка'

    id = models.AutoField(primary_key=True)
    mesh_file_path = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reconstructions')
    saved_at = models.DateTimeField(null=True, blank=True, default=None, db_index=True)
    name = models.CharField(max_length=255, null=True, blank=True, default=None)
    status = models.PositiveSmallIntegerField(
        choices=Status.choices,
        default=Status.QUEUED
    )
    plan_signs = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = '3D реконструкция'
        verbose_name_plural = '3D реконструкции'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.id} ({self.created_at:%Y-%m-%d %H:%M})'

    def get_name(self):
        return self.name if self.name else f'Реконструкция №{self.id}'
