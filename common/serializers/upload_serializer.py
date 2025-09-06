# serializers.py
from rest_framework import serializers
from ..models import UploadedFile
from django.conf import settings
import os
from rest_framework_mongoengine.serializers import DocumentSerializer

class FileUploadSerializer(serializers.Serializer):
    """文件上传序列化器"""
    # file = serializers.FileField(
    #     max_length=100,
    #     allow_empty_file=False,
    #     use_url=False,
    #     required=True
    # )
    files= serializers.ListField(
        child=serializers.FileField(
            max_length=100,
            allow_empty_file=False,
            use_url=False,
            required=True
        ),
        required=True
    )
    # user_id = serializers.CharField(required=True, max_length=100)
    
    def validate_files(self, value):
        
        """验证文件列表"""
        if not value:
            raise serializers.ValidationError("文件列表不能为空")
        # 检查每个文件的大小
        for file in value:
            if file.size > settings.MAX_UPLOAD_SIZE:
                raise serializers.ValidationError(
                    f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB"
                )
        
        # 检查文件类型
        valid_extensions = []
        for category, exts in settings.ALLOWED_FILE_TYPES.items():
            valid_extensions.extend(exts)

        for file in value:
            ext = os.path.splitext(file.name)[1].lower()[1:]  # 去掉点号
            if ext not in valid_extensions:
                raise serializers.ValidationError("不支持的文件类型")
                
        return value
    
    def validate_user_id(self, value):
        """验证用户ID"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("用户ID不能为空")
        return value.strip()

class UploadedFileSerializer(DocumentSerializer):
    """文件信息序列化器 - 使用 DocumentSerializer 兼容 mongoengine"""
    
    download_url = serializers.SerializerMethodField()
    file_type_display = serializers.SerializerMethodField()
    processing_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedFile
        fields = [
            'id', 'file_name', 'original_filename', 'file_size', 
            'file_type', 'file_type_display', 'mime_type', 
            'uploaded_at', 'user_id', 'download_url',
            'processing_status', 'processing_status_display',
            'expires_at'
        ]
        read_only_fields = fields
    
    def get_download_url(self, obj):
        """获取下载URL"""
        request = self.context.get('request')
        return obj.get_absolute_url(request)
    
    def get_file_type_display(self, obj):
        """获取文件类型显示名称"""
        return dict(UploadedFile.file_type.choices).get(obj.file_type, '未知')
    
    def get_processing_status_display(self, obj):
        """获取处理状态显示名称"""
        return dict(UploadedFile.processing_status.choices).get(obj.processing_status, '未知')