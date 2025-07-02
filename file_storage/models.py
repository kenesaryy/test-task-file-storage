from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class FileStorage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    parts_count = models.IntegerField(default=16)
    created_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.original_filename} ({self.user.username})"

class FilePart(models.Model):
    file_storage = models.ForeignKey(FileStorage, on_delete=models.CASCADE, related_name='parts')
    part_number = models.IntegerField()
    archive_path = models.CharField(max_length=500)
    part_size = models.BigIntegerField()
    checksum = models.CharField(max_length=64)  # SHA256

    class Meta:
        unique_together = ['file_storage', 'part_number']

class ActionLog(models.Model):
    ACTION_TYPES = [
        ('UPLOAD_START', 'Upload Started'),
        ('UPLOAD_SUCCESS', 'Upload Successful'),
        ('UPLOAD_FAIL', 'Upload Failed'),
        ('DOWNLOAD_START', 'Download Started'),
        ('DOWNLOAD_SUCCESS', 'Download Successful'),
        ('DOWNLOAD_FAIL', 'Download Failed'),
        ('DELETE', 'File Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    timestamp = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    file_id = models.UUIDField(null=True, blank=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']