from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.

class Identification(models.Model):
    class Status(models.IntegerChoices):
        QUEUED = 1, 'В очереди'
        IN_PROGRESS = 2, 'В обработке'
        DONE = 3, 'Готово'
        FAILED = 4, 'Ошибка'
        NOT_FOUND = 5, 'Не найдено'

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='identifications')
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.QUEUED)
    x_value = models.IntegerField(null=True, blank=True)
    y_value = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def get_status_display(self):
        return self.Status(self.status).label
