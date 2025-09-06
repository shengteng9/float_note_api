from django.core.serializers import serialize
from rest_framework import viewsets, status
from rest_framework.response import Response
import datetime
from ..models import Tag, Category
from ..serializers import TagSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    @extend_schema(
        tags=["标签"],
        summary="获取标签列表",
        description="获取所有标签列表，支持按分类和名称进行过滤",
        parameters=[
            OpenApiParameter(
                name="category_id", description="分类ID", required=False, type=str
            ),
            OpenApiParameter(
                name="name", description="标签名称", required=False, type=str
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        category_id = request.query_params.get("category_id")
        if category_id:
            self.queryset = self.queryset.filter(category=category_id)

        name = request.query_params.get("name")
        if name:
            self.queryset = self.queryset.filter(name=name)

        # 确保只返回当前用户的标签
        user = request.user
        self.queryset = self.queryset.filter(user=user)

        # 执行查询并序列化数据
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'code': status.HTTP_200_OK,
                'message': '获取标签列表成功',
                'data': serializer.data,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': status.HTTP_200_OK,
            'message': '获取标签列表成功',
            'data': serializer.data,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, status=status.HTTP_200_OK)


    @extend_schema(
        tags=['标签'],
        summary='创建标签',
        description='创建一个新的标签',
        request=TagSerializer,
        responses={201: TagSerializer}
    )
    def create(self, request, *args, **kwargs):

        try:
            request_data = request.data
            request_data['user'] = request.user.id
            category_id = request.data['category']
            category = Category.objects.get(id=category_id, user=request.user)
            if not category:
                return Response({
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': '分类不存在',
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(data=request_data)

            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response({
                    'code': status.HTTP_201_CREATED,
                    'message': '标签创建成功',
                    'data': serializer.data,
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                 'code': status.HTTP_400_BAD_REQUEST,
                 'message': '标签创建失败',
                 'error': serializer.errors,
                 'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
             }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '标签创建失败',
                'error': str(e),
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, status=status.HTTP_400_BAD_REQUEST)

    
    @extend_schema(
        tags=['标签'],
        summary='更新标签',
        description='更新一个标签',
        request=TagSerializer,
        responses={200: TagSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        try:
            print('update...')
            instance = self.get_object()
            data = instance.to_mongo().to_dict()
            print(data)
            print('=== update ==== data ', request.data)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'code': status.HTTP_200_OK,
                    'message': '标签更新成功',
                    'data': serializer.data,
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': '标签更新失败',
                    'error': serializer.errors,
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '标签更新失败',
                'error': str(e),
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, status=status.HTTP_400_BAD_REQUEST)

    
    @extend_schema(
        tags=['标签'],
        summary='删除标签',
        description='删除一个标签',
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({
                'code': status.HTTP_204_NO_CONTENT,
                'message': '标签删除成功',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '标签删除失败',
                'error': str(e),
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['标签'],
        summary='获取标签详情',
        description='获取一个标签详情',
        responses={200: TagSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            
            instance = self.get_object()

            serializer = self.get_serializer(instance)
            return Response({
                'code': status.HTTP_200_OK,
                'message': '获取标签详情成功',
                'data': serializer.data,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '标签不存在',
                'error': str(e),
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, status=status.HTTP_400_BAD_REQUEST)
    
        
    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)
        