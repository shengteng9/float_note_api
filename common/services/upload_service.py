
from typing import Dict, Any
import datetime
from typing import Dict, List
from ..models import UploadedFile
from mongoengine.queryset.visitor import Q 
from pydantic import Field, BaseModel

class UploadFileService:
    """文件上传服务类"""
    
    
    def upload_file(self, file_list: list, user, ) -> List[UploadedFile]:
        """上传文件"""
        uploaded_files = []
        for file in file_list:
            uploaded_file = UploadedFile(
                user_id=user.id,
                file_path=''  # 临时值，会在save_file中设置
            )
            uploaded_file.save_file(file)
            uploaded_file.save()
            uploaded_files.append(uploaded_file)
        return uploaded_files
    
    def get_file_list(self, user, category: str) -> List[UploadedFile]:
        """获取文件列表"""
        uploaded_files = UploadedFile.objects(user_id=user.id, category=category)
        return uploaded_files