from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import FileStorage, ActionLog
from .serializers import FileUploadSerializer, FileStorageSerializer, ActionLogSerializer
from .services import FileStorageService

User = get_user_model()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """Загрузка и обработка файла"""
    user = request.user

    # Логируем начало загрузки
    FileStorageService.log_action(
        user_id=user.id,
        action_type='UPLOAD_START',
        details=f"Попытка загрузки файла пользователем {user.username}"
    )

    serializer = FileUploadSerializer(data=request.data)
    if not serializer.is_valid():
        FileStorageService.log_action(
            user_id=user.id,
            action_type='UPLOAD_FAIL',
            details=f"Невалидные данные: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = serializer.validated_data['file']

    # Проверяем размер файла (максимум 16MB)
    if uploaded_file.size > 16 * 1024 * 1024:
        FileStorageService.log_action(
            user_id=user.id,
            action_type='UPLOAD_FAIL',
            details=f"Файл слишком большой: {uploaded_file.size} байт"
        )
        return Response(
            {'error': 'Размер файла превышает 16MB'}, 
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )

    try:
        with transaction.atomic():  # Оборачиваем в транзакцию: создание + обработка файла + лог
            # Создаем запись о файле
            file_storage = FileStorage.objects.create(
                user=user,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size
            )

            # Разбиваем и архивируем файл
            FileStorageService.split_and_archive_file(uploaded_file, file_storage)

            FileStorageService.log_action(
                user_id=user.id,
                action_type='UPLOAD_SUCCESS',
                file_id=file_storage.id,
                details=f"Файл {uploaded_file.name} успешно загружен и обработан"
            )

        return Response({
            'file_id': file_storage.id,
            'message': 'Файл успешно загружен и обработан'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        FileStorageService.log_action(
            user_id=user.id,
            action_type='UPLOAD_FAIL',
            details=f"Ошибка при обработке файла: {str(e)}"
        )
        return Response(
            {'error': f'Ошибка при обработке файла: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_file(request, file_id):
    """Скачивание файла"""
    user = request.user

    FileStorageService.log_action(
        user_id=user.id,
        action_type='DOWNLOAD_START',
        file_id=file_id,
        details=f"Попытка скачивания файла {file_id}"
    )

    try:
        file_storage = FileStorage.objects.get(id=file_id, user=user)

        if not file_storage.is_complete:
            FileStorageService.log_action(
                user_id=user.id,
                action_type='DOWNLOAD_FAIL',
                file_id=file_id,
                details="Файл не готов к скачиванию"
            )
            return Response(
                {'error': 'Файл не готов к скачиванию'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Собираем файл из частей
        file_data = FileStorageService.reassemble_file(file_storage)

        FileStorageService.log_action(
            user_id=user.id,
            action_type='DOWNLOAD_SUCCESS',
            file_id=file_id,
            details=f"Файл {file_storage.original_filename} успешно скачан"
        )

        response = HttpResponse(file_data, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_storage.original_filename}"'
        response['Content-Length'] = len(file_data)

        return response

    except FileStorage.DoesNotExist:
        FileStorageService.log_action(
            user_id=user.id,
            action_type='DOWNLOAD_FAIL',
            file_id=file_id,
            details="Файл не найден"
        )
        return Response(
            {'error': 'Файл не найден'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        FileStorageService.log_action(
            user_id=user.id,
            action_type='DOWNLOAD_FAIL',
            file_id=file_id,
            details=f"Ошибка при скачивании: {str(e)}"
        )
        return Response(
            {'error': f'Ошибка при скачивании файла: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_files(request):
    """Список файлов пользователя"""
    user = request.user
    files = FileStorage.objects.filter(user=user).order_by('-created_at')
    serializer = FileStorageSerializer(files, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request, file_id):
    """Удаление файла"""
    user = request.user

    try:
        file_storage = FileStorage.objects.get(id=file_id, user=user)

        with transaction.atomic():  # Оборачиваем удаление БД и файловую операцию
            # Удаляем физические файлы
            import shutil
            import os
            from django.conf import settings

            parts_dir = os.path.join(settings.MEDIA_ROOT, 'file_parts', str(file_storage.id))
            if os.path.exists(parts_dir):
                shutil.rmtree(parts_dir)

            filename = file_storage.original_filename
            file_storage.delete()

            FileStorageService.log_action(
                user_id=user.id,
                action_type='DELETE',
                file_id=file_id,
                details=f"Файл {filename} удален"
            )

        return Response({'message': 'Файл успешно удален'})

    except FileStorage.DoesNotExist:
        return Response(
            {'error': 'Файл не найден'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def action_logs(request):
    """Просмотр логов действий пользователя"""
    user = request.user
    logs = ActionLog.objects.filter(user_id=user.id)[:100]  # Последние 100 записей
    serializer = ActionLogSerializer(logs, many=True)
    return Response(serializer.data)
