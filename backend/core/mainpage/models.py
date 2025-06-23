import os
from django.db import models
from django.utils import timezone

def app_upload_to(instance, filename):
    ext = filename.split('.')[-1].lower()
    return f'application/{instance.os}/recon3d_{instance.version}.{ext}'

class ApplicationFile(models.Model):
    class OS(models.TextChoices):
        ANDROID = 'android', 'Android'
        # В будущем можно добавить iOS и др.

    os = models.CharField('ОС', max_length=20, choices=OS.choices, default=OS.ANDROID)
    version = models.CharField('Версия', max_length=20)
    file = models.FileField('Файл', upload_to=app_upload_to)
    uploaded_at = models.DateTimeField('Загружено', default=timezone.now, db_index=True)
    hidden = models.BooleanField('Скрыто', default=False)

    class Meta:
        verbose_name = 'Файл приложения'
        verbose_name_plural = 'Файлы приложения'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.os} {self.version} ({self.uploaded_at:%Y-%m-%d %H:%M})'
