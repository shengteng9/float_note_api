from django.urls import path, include  # 添加 include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
# from .views.upload_view import UploadViewSet
# from common.views.upload_file_view import TempFileUploadView, TempFileDeleteView, FileInfoView

router = DefaultRouter()
router.register(r'user', UserViewSet, basename='user')
# router.register(r'upload', UploadViewSet, basename='upload')

urlpatterns = [
    path('', include(router.urls)),  
    # path('upload/', TempFileUploadView.as_view(), name='file-upload'),
    # path('files/<str:file_id>/', FileInfoView.as_view(), name='file-info'),
    # path('files/<str:file_id>/delete/', TempFileDeleteView.as_view(), name='file-delete'),
]