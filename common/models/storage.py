# storage.py
import os
import shutil
from django.conf import settings
from datetime import datetime

class FileSystemStorage:
    """自定义文件系统存储"""
    
    def __init__(self, location=None):
        self.location = location or settings.MEDIA_ROOT
        os.makedirs(self.location, exist_ok=True)
    
    def save(self, name, content):
        """保存文件到文件系统"""
        full_path = self.path(name)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 保存文件
        with open(full_path, 'wb+') as destination:
            for chunk in content.chunks():
                destination.write(chunk)
        
        return name
    
    def path(self, name):
        """获取文件的完整路径"""
        return os.path.join(self.location, name)
    
    def delete(self, name):
        """删除文件"""
        try:
            full_path = self.path(name)
            if os.path.isfile(full_path):
                os.remove(full_path)
                return True
        except (OSError, Exception) as e:
            print(f"删除文件失败: {e}")
        return False
    
    def exists(self, name):
        """检查文件是否存在"""
        return os.path.exists(self.path(name))
    
    def open(self, name, mode='rb'):
        """打开文件"""
        return open(self.path(name), mode)
    
    def size(self, name):
        """获取文件大小"""
        try:
            return os.path.getsize(self.path(name))
        except OSError:
            return 0

# 创建存储实例
file_storage = FileSystemStorage()