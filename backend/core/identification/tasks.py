from celery import shared_task
from identification.models import Identification
from upload_files.models import UploadedFile
from reconstruction.models import Reconstruction
from django.conf import settings
from identification.utils.room_number_detector import find_room_numbers
import os

@shared_task
def run_identification_task(identification_id, file_id, reconstruction_id):
    try:
        identification = Identification.objects.get(id=identification_id)
        file = UploadedFile.objects.get(id=file_id)
        reconstruction = Reconstruction.objects.get(id=reconstruction_id)
    except (Identification.DoesNotExist, UploadedFile.DoesNotExist, Reconstruction.DoesNotExist):
        return
    identification.status = Identification.Status.IN_PROGRESS
    identification.save(update_fields=['status'])
    try:
        abs_file_path = os.path.join(settings.MEDIA_ROOT, file.file_path)
        room_numbers = find_room_numbers(abs_file_path)
        room_numbers = [n.lower() for n in room_numbers]
        found = False
        if reconstruction.rooms:
            for room in reconstruction.rooms:
                number = str(room.get('number', '')).lower()
                if number in room_numbers:
                    identification.x_value = int(room.get('x', 0))
                    identification.y_value = int(room.get('y', 0))
                    identification.status = Identification.Status.DONE
                    found = True
                    break
        if not found:
            identification.status = Identification.Status.NOT_FOUND  # Не найдено
        identification.save(update_fields=['x_value', 'y_value', 'status'])
    except Exception:
        identification.status = Identification.Status.FAILED
        identification.save(update_fields=['status']) 