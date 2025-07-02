import os
import zipfile
import hashlib
import tempfile
import shutil

from django.conf import settings
from .models import FilePart, ActionLog

class FileStorageService:

    @staticmethod
    def log_action(user_id, action_type, file_id=None, details=""):
        ActionLog.objects.create(
            user_id=user_id,
            action_type=action_type,
            file_id=file_id,
            details=details
        )

    @staticmethod
    def calculate_checksum(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _get_parts_dir(file_storage):
        return os.path.join(settings.MEDIA_ROOT, 'file_parts', str(file_storage.id))

    @staticmethod
    def _archive_part(part_index, part_data, parts_dir):
        archive_name = f'part_{part_index:02d}.zip'
        archive_path = os.path.join(parts_dir, archive_name)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.part') as temp_file:
            temp_file.write(part_data)
            temp_path = temp_file.name

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_path, f'part_{part_index:02d}.data')

        os.unlink(temp_path)
        return archive_path

    @staticmethod
    def split_and_archive_file(file_obj, file_storage):
        file_obj.seek(0)
        file_data = file_obj.read()
        total_size = len(file_data)

        part_size = total_size // 16
        parts_dir = FileStorageService._get_parts_dir(file_storage)
        os.makedirs(parts_dir, exist_ok=True)

        try:
            for i in range(16):
                start = i * part_size
                end = total_size if i == 15 else (start + part_size)
                part_data = file_data[start:end]

                archive_path = FileStorageService._archive_part(i, part_data, parts_dir)

                FilePart.objects.create(
                    file_storage=file_storage,
                    part_number=i,
                    archive_path=archive_path,
                    part_size=len(part_data),
                    checksum=FileStorageService.calculate_checksum(part_data)
                )

            file_storage.is_complete = True
            file_storage.save()
            return True

        except Exception as e:
            shutil.rmtree(parts_dir, ignore_errors=True)
            raise e

    @staticmethod
    def _extract_part(part: FilePart) -> bytes:
        if not os.path.exists(part.archive_path):
            raise FileNotFoundError(f"Архив части {part.part_number} не найден")

        with zipfile.ZipFile(part.archive_path, 'r') as zipf:
            part_name = f'part_{part.part_number:02d}.data'
            data = zipf.read(part_name)

        if FileStorageService.calculate_checksum(data) != part.checksum:
            raise ValueError(f"Контрольная сумма части {part.part_number} не совпадает")

        return data

    @staticmethod
    def reassemble_file(file_storage):
        parts = file_storage.parts.order_by('part_number')

        if parts.count() != 16:
            raise ValueError("Ожидается 16 частей файла")

        return b''.join(FileStorageService._extract_part(part) for part in parts)
