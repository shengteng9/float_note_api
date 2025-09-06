# urls.py
from django.urls import path
from .views.upload_view import FileUploadView, FileListView, FileDownloadView, FileDeleteView

urlpatterns = [
    # 永久文件上传相关路由
    path('files/upload/', FileUploadView.as_view(), name='file-upload'),
    path('files/', FileListView.as_view(), name='file-list'),
    path('files/<str:file_id>/download/', FileDownloadView.as_view(), name='file-download'),
    path('files/<str:file_id>/delete/', FileDeleteView.as_view(), name='file-delete'),
]