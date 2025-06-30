from celery import shared_task
from .models import Reconstruction
from upload_files.models import UploadedFile
from django.conf import settings
import os
import uuid
from .utils.plan2reconstruction import reconstruct_3d_from_plan, save_mesh
import logging

logger = logging.getLogger(__name__)

@shared_task
def create_reconstruction_task(reconstruction_id, plan_file_id, user_mask_file_id):
    """
    Асинхронная задача для создания 3D-реконструкции.
    """
    try:
        reconstruction = Reconstruction.objects.get(id=reconstruction_id)
        plan_file = UploadedFile.objects.get(id=plan_file_id)
        user_mask_file = UploadedFile.objects.get(id=user_mask_file_id)
    except Reconstruction.DoesNotExist:
        logger.error(f"Реконструкция с id={reconstruction_id} не найдена.")
        return
    except UploadedFile.DoesNotExist:
        logger.error(f"Файл плана ({plan_file_id}) или маски ({user_mask_file_id}) не найден.")
        reconstruction.status = Reconstruction.Status.FAILED
        reconstruction.save(update_fields=['status'])
        return

    # 1. Обновляем статус на "В обработке"
    reconstruction.status = Reconstruction.Status.IN_PROGRESS
    reconstruction.save(update_fields=['status'])

    plan_path = os.path.join(settings.MEDIA_ROOT, plan_file.file_path)
    user_mask_path = os.path.join(settings.MEDIA_ROOT, user_mask_file.file_path)

    try:
        # 2. Основная логика реконструкции
        mesh = reconstruct_3d_from_plan(plan_path, user_mask_path)
        if mesh is None:
            raise ValueError("Не удалось построить 3D-модель (нет линий)")

        # 3. Сохранение меша
        mesh_rel_path = f'mesh/{uuid.uuid4()}.obj'
        mesh_abs_path = os.path.join(settings.MEDIA_ROOT, mesh_rel_path)
        os.makedirs(os.path.dirname(mesh_abs_path), exist_ok=True)
        save_mesh(mesh, mesh_abs_path)

        # 4. Обновление объекта Reconstruction
        reconstruction.mesh_file_path = mesh_rel_path
        reconstruction.status = Reconstruction.Status.DONE
        reconstruction.save(update_fields=['mesh_file_path', 'status'])
        logger.info(f"Реконструкция {reconstruction_id} успешно завершена.")

    except Exception as e:
        logger.error(f"Ошибка при создании реконструкции {reconstruction_id}: {e}", exc_info=True)
        reconstruction.status = Reconstruction.Status.FAILED
        reconstruction.save(update_fields=['status']) 