# views.py
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.http import FileResponse, Http404

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from ..services.upload_service import UploadFileService

from ..models import UploadedFile
from ..serializers import (
    FileUploadSerializer, 
    UploadedFileSerializer,
)


class FileUploadView(APIView):
    """文件上传视图"""
    
    parser_classes = (MultiPartParser, FormParser)
    @extend_schema(
        # 1. 基础文档信息
        tags=["文件管理"],  # 接口分类标签（Swagger中用于分组）
        summary="文件上传接口",
        description="""
        功能：用户上传文件到服务器，自动关联当前登录用户ID  
        限制：
        - 支持文件格式：jpg/png等...  
        - 最大文件大小：100MB  
        - 权限：需登录（JWT认证）  
        """,
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'files': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'format': 'binary',
                        },
                        'description': '要上传的文件列表'
                    }
                }
            }
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': '数据验证失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            file_obj_list = serializer.validated_data['files']
            # 上传文件
            upload_file_service = UploadFileService()
            uploaded_files = upload_file_service.upload_file(file_obj_list, request.user)

            file_serializer = UploadedFileSerializer(
                uploaded_files,
                many=True,
                context={'request': request}
            )
            
            return Response({
                'success': True,
                'message': '文件上传成功',
                'data': file_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # 如果发生错误，尝试删除可能已创建的文件
            if 'uploaded_file' in locals() and hasattr(uploaded_file, 'file_path'):
                uploaded_file.delete_file()
                
            return Response({
                'success': False,
                'message': f'文件上传失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FileDownloadView(APIView):
    """文件下载视图"""
    serializer_class = UploadedFileSerializer

    @extend_schema(
        tags=["文件管理"],  # 接口分类标签（Swagger中用于分组）
        summary="文件下载接口",
        description="""
        功能：下载用户上传的文件
        权限：需登录（JWT认证）
        """,
        parameters=[
            OpenApiParameter(
                name="file_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="文件ID，用于指定要下载的文件"
            ),
        ],
    )
    def get(self, request, file_id):
        try:
            uploaded_file = UploadedFile.objects.get(id=file_id, user_id=request.user.id)
            
            # 检查文件是否存在
            if not uploaded_file.file_path:
                raise Http404("文件不存在")
            
            # 读取文件内容
            file_content = uploaded_file.get_file_content()
            if file_content is None:
                raise Http404("文件不存在或无法读取")
            
            # 创建文件响应
            response = FileResponse(
                file_content,
                content_type=uploaded_file.mime_type or 'application/octet-stream'
            )
            
            # 设置下载头信息
            response['Content-Disposition'] = (
                f'attachment; filename="{uploaded_file.original_filename}"'
            )
            response['Content-Length'] = uploaded_file.file_size
            
            return response
            
        except UploadedFile.DoesNotExist:
            return Response({
                'success': False,
                'message': '文件不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'文件下载失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FileListView(APIView):
    """文件列表视图"""
    serializer_class = UploadedFileSerializer
    
    @extend_schema(
        tags=["文件管理"],  # 接口分类标签（Swagger中用于分组）
        summary="文件列表查询接口",
        description="""
        功能：查询用户上传的文件列表，支持多条件过滤和分页
        权限：需登录（JWT认证）
        """,
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="用户ID，用于过滤特定用户的文件"
            ),
            OpenApiParameter(
                name="file_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="文件类型，可选值：image(图片)、audio(音频)、video(视频)、document(文档)、other(其他)",
                enum=["image", "audio", "video", "document", "other"]
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="处理状态，可选值：pending(待处理)、processing(处理中)、completed(已完成)、failed(失败)",
                enum=["pending", "processing", "completed", "failed"]
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="页码，默认为1",
                default=1
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="每页数量，默认为20",
                default=20
            ),
        ],
    )
    def get(self, request):
        try:
            queryset = UploadedFile.objects.all()
            
            # 过滤条件
            user_id = request.query_params.get('user_id')
            file_type = request.query_params.get('file_type')
            status_filter = request.query_params.get('status')
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            if file_type:
                queryset = queryset.filter(file_type=file_type)
            if status_filter:
                queryset = queryset.filter(processing_status=status_filter)
            
            # 分页
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            skip = (page - 1) * page_size
            
            total_count = queryset.count()
            files = list(queryset.skip(skip).limit(page_size))
            
            serializer = UploadedFileSerializer(
                files, 
                many=True, 
                context={'request': request}
            )
            
            return Response({
                'success': True,
                'data': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'获取文件列表失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FileDeleteView(APIView):
    """文件删除视图"""
    serializer_class = UploadedFileSerializer
    @extend_schema(
        tags=["文件管理"],  # 接口分类标签（Swagger中用于分组）
        summary="文件删除接口",
        description="""
        功能：删除用户上传的文件
        权限：需登录（JWT认证）
        """,
        parameters=[
            OpenApiParameter(
                name="file_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="文件ID，用于指定要删除的文件"
            ),
        ],
    )
    def delete(self, request, file_id):
        try:
            uploaded_file = UploadedFile.objects.get(id=file_id, user_id=request.user.id)
            uploaded_file.delete()  # 这会同时删除数据库记录和物理文件
            
            return Response({
                'success': True,
                'message': '文件删除成功'
            })
            
        except UploadedFile.DoesNotExist:
            return Response({
                'success': False,
                'message': '文件不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'文件删除失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)