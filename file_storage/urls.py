from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('download/<uuid:file_id>/', views.download_file, name='download_file'),
    path('files/', views.list_files, name='list_files'),
    path('delete/<uuid:file_id>/', views.delete_file, name='delete_file'),
    path('logs/', views.action_logs, name='action_logs'),
]