from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import  OpenApiTypes

from ..models import Record
from ..serializers import RecordSerializer
from ..services.record_service import RecordService
from common.models.upload_model import UploadedFile
from common.services.upload_service import UploadFileService

import json

class RecordViewSet(viewsets.ModelViewSet):
    serializer_class = RecordSerializer
    queryset = Record.objects.all()
    # parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Record.objects.filter(user=self.request.user)
    
    @extend_schema(
        tags=['记录'],
        summary='创建新记录',
        description='创建记录并支持每个原始输入项上传文件',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'title': {
                        'type': 'string',
                        'description': '记录标题',
                        'nullable': True
                    },
                    'files': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'format': 'binary'
                        },
                        'description': '上传的文件数组',
                    },
                    'raw_inputs': {
                        'type': 'string',           # ← 明确写 string，不是 array
                        'description': '原始输入数组（JSON 字符串格式）',
                        'example': '[{"type": "text", "content": "1111"}]'
                    },
                    'category_id': {
                        'type': 'string',
                        'description': '分类ID',
                        'nullable': True
                    }
                }
            }
        },
        responses={
            201: RecordSerializer,
            400: OpenApiResponse(description="无效输入"),
        }
    )
    def create(self, request, *args, **kwargs):
        parser_classes = [MultiPartParser, FormParser]
        try:
            request_data = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)
            # form-data 特别处理json字符串
            raw_inputs_str = request_data.get('raw_inputs', '')
            raw_inputs = []
            try:
                if isinstance(raw_inputs_str, str) and raw_inputs_str.strip():
                    raw_inputs = json.loads(raw_inputs_str)

            except json.JSONDecodeError:
                print('JSON解析失败，使用空列表')

            # 4. 确保raw_inputs是列表类型
            if not isinstance(raw_inputs, list):
                raw_inputs = [raw_inputs] if raw_inputs else []
            
            files_list = request.FILES.getlist('files')

            if files_list:
                upload_file_service = UploadFileService()
                uploaded_files = upload_file_service.upload_file(files_list, request.user)
                if len(uploaded_files) > 0:
                    for uploaded_file in uploaded_files:
                        raw_inputs.append({
                            'type': uploaded_file.file_type,
                            'content': '文件描述信息',
                            'file_path': uploaded_file.file_path,
                        })
                del request_data['files']

            request_data['raw_inputs'] = raw_inputs
            serializer = RecordSerializer(data=request_data, context={'request': request})
            
            if serializer.is_valid():
                # 保存记录
                record = serializer.save(user=request.user)
                
                # 构造响应
                response_serializer = RecordSerializer(record)
                return Response({
                    'success': True,
                    'message': '记录创建成功',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                print('序列化器验证失败')
                print('错误详情:', serializer.errors)
                # 特别检查raw_inputs字段的错误
                if 'raw_inputs' in serializer.errors:
                    print('raw_inputs验证错误:', serializer.errors['raw_inputs'])
                    print('提交的raw_inputs值:', request_data['raw_inputs'])
                
                return Response({
                    'success': False,
                    'error': serializer.errors,
                    'message': '创建记录失败，输入验证错误'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            
            return Response({
                'success': False,
                'error': str(e),
                'message': '创建记录时发生异常'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['记录'],
        summary='查询记录列表',
        description='查询用户记录列表',
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['记录'],
        summary='查询记录详情',
        description='查询用户记录详情',
    )
    def retrieve(self, request, *args, **kwargs):
        # instance = self.get_object()
        # serializer = self.serializer_class(instance)
        # return Response(serializer.data)

        try:
            record_id = kwargs.get('pk')
            record = RecordService().get_record_by_id(record_id)
            serializer = self.serializer_class(record)
            return Response({
                'success': True,
                'message': '查询记录成功',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': '查询记录失败'
            }, status=status.HTTP_400_BAD_REQUEST)      

    @extend_schema(
        tags=['记录'],
        summary='更新记录',
        description='更新用户记录',
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['记录'],
        summary='重新处理记录',
        description='重新处理用户记录',
    )
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """重新处理记录"""
        record = self.get_object()
        record_service = RecordService()
        updated_record = record_service.reprocess_record(record)
        
        return Response({
            'message': '记录已重新处理',
            'new_type': updated_record.type,
            # 'confidence': updated_record.confidence,
            'content': updated_record.content
        })

    @extend_schema(
        tags=['记录'],
        summary='删除记录',
        description='删除用户记录',
    )
    def destroy(self, request, *args, **kwargs):
        """删除记录"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        tags=['记录'],
        summary='测试处理功能',
        description='测试处理功能',
    )
    @action(detail=False, methods=['post'])
    def test_processing(self, request):
        """测试处理功能"""
        raw_inputs_data = request.data.get('raw_inputs', [])
        title = request.data.get('title', '测试记录')
        
        record_service = RecordService()
        try:
            # 直接处理而不保存到数据库
            from ..models import RawInput
            raw_inputs = [RawInput(**data) for data in raw_inputs_data]
            
            result = record_service.llm_processor.process_inputs(raw_inputs)
            
            return Response({
                'success': True,
                'result': result
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


