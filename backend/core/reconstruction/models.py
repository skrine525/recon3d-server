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
