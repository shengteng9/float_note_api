from mongoengine import Document, fields
import os
import mimetypes
from datetime import datetime, timedelta
from django.conf import settings
from .storage import file_storage

def get_upload_path(instance, filename):
    """生成按类型和时间分类的存储路径"""
    ext = os.path.splitext(filename)[1].lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_id = str(fields.ObjectId())
    safe_name = f"{timestamp}_{file_id}{ext}"
    
    # 确定文件类型目录
    file_type = 'other'
    for category, exts in settings.ALLOWED_FILE_TYPES.items():
        if ext[1:] in exts:  # 去掉点号
            file_type = category
            break
            
    return f"{file_type}/{safe_name}"

class UploadedFile(Document):
    """文件上传模型 - 使用文件系统存储"""
    
    meta = {
        'collection': 'uploaded_files',
        'indexes': [
            {'fields': ['file_type'], 'name': 'file_type_idx'},
            {'fields': ['user_id'], 'name': 'user_id_idx'},
            {
                'fields': ['uploaded_at'], 
                'name': 'uploaded_at_ttl',
                'expireAfterSeconds': 604800  # 7天，与你的 expires_at 保持一致
            },
            {
                'fields': ['expires_at'], 
                'name': 'expires_at_ttl',
                'expireAfterSeconds': 0  # 使用 expires_at 字段的值作为过期时间
            },
            # 复合索引示例
            {
                'fields': ['user_id', 'uploaded_at'],
                'name': 'user_upload_time_idx'
            }
        ],
        'ordering': ['-uploaded_at']
    }
    
    # 文件信息
    file_path = fields.StringField(required=True)
    file_name = fields.StringField(required=True)
    original_filename = fields.StringField(required=True)
    file_size = fields.IntField(min_value=0)
    file_type = fields.StringField(choices=[
        ('image', '图片'),
        ('audio', '音频'), 
        ('video', '视频'),
        ('document', '文档'),
        ('other', '其他')
    ], required=True)
    mime_type = fields.StringField()
    
    # 元数据
    uploaded_at = fields.DateTimeField(default=datetime.now)
    user_id = fields.ObjectIdField(required=True)
    expires_at = fields.DateTimeField(default=lambda: datetime.now() + timedelta(days=7))
    processing_status = fields.StringField(choices=[
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败')
    ], default='pending')
    
    def save_file(self, file_obj):
        """保存文件到文件系统并填充元数据"""
        # 生成存储路径
        filename = get_upload_path(self, file_obj.name)
        self.file_path = file_storage.save(filename, file_obj)
        
        # 提取并保存新生成的文件名（不含路径）
        self.file_name = os.path.basename(self.file_path)
        
        # 填充元数据
        self.original_filename = file_obj.name
        self.file_size = file_obj.size
        
        # 检测MIME类型
        self.mime_type = mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'
        
        # 确定文件类型
        ext = os.path.splitext(file_obj.name)[1].lower()[1:]  # 去掉点号
        file_type = 'other'
        for category, exts in settings.ALLOWED_FILE_TYPES.items():
            if ext in exts:
                file_type = category
                break
        self.file_type = file_type
        
        return self.file_path
    
    def get_file_content(self):
        """读取文件内容"""
        try:
            if file_storage.exists(self.file_path):
                with file_storage.open(self.file_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
        return None
    
    def delete_file(self):
        """删除物理文件"""
        if self.file_path:
            return file_storage.delete(self.file_path)
        return False
    
    def get_absolute_url(self, request=None):
        """获取文件访问URL"""
        if self.file_path:
            if request:
                return request.build_absolute_uri(settings.MEDIA_URL + self.file_path)
            return settings.MEDIA_URL + self.file_path
        return None
    
    def clean(self):
        """验证数据"""
        if not self.file_path:
            raise ValueError("文件路径不能为空")
    
    def delete(self, *args, **kwargs):
        """重写删除方法，同时删除物理文件"""
        self.delete_file()
        super().delete(*args, **kwargs)