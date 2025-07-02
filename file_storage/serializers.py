from rest_framework import serializers
from .models import FileStorage, ActionLog

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class FileStorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStorage
        fields = ['id', 'original_filename', 'file_size', 'created_at', 'is_complete']
        read_only_fields = ['id', 'file_size', 'created_at', 'is_complete']

class ActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionLog
        fields = ['id', 'user_id', 'timestamp', 'action_type', 'file_id', 'details']
