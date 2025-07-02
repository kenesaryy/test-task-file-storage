from django.contrib import admin
from .models import FileStorage, FilePart, ActionLog

@admin.register(FileStorage)
class FileStorageAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_filename', 'user', 'file_size', 'is_complete', 'created_at']
    list_filter = ['is_complete', 'created_at']
    search_fields = ['original_filename', 'user__username']
    readonly_fields = ['id', 'created_at']

@admin.register(FilePart)
class FilePartAdmin(admin.ModelAdmin):
    list_display = ['file_storage', 'part_number', 'part_size', 'checksum']
    list_filter = ['part_number']
    search_fields = ['file_storage__original_filename']

@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'action_type', 'file_id', 'timestamp']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['user_id', 'file_id', 'details']
    readonly_fields = ['id', 'timestamp']