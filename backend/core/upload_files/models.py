import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def upload_to(instance, filename):
    ext = filename.split('.')[-1].lower()
    if instance.source_type == instance.SourceType.PLAN_2D:
        folder = 'uploads/plan-photos/'
    else:
        folder = 'uploads/user-environment-photos/'
    return f'{folder}{instance.id}.{ext}'

class UploadedFile(models.Model):
    class FileType(models.IntegerChoices):
        PHOTO = 1, 'Фото'

    class SourceType(models.IntegerChoices):
        PLAN_2D = 1, '2D-план'
        USER_ENV = 2, 'Окружение пользователя'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_type = models.PositiveSmallIntegerField(choices=FileType.choices)
    file_path = models.CharField(max_length=255)
    source_type = models.PositiveSmallIntegerField(choices=SourceType.choices)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.id} - {self.get_file_type_display()} - {self.get_source_type_display()}'
