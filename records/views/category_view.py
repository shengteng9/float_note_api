from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from ..models import Category
from accounts.models.user_model import User
from ..serializers import CategorySerializer
from rest_framework.decorators import action
from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiExample,
    OpenApiRequest,
    inline_serializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """
        动态返回当前用户的过滤 queryset
        """
        user = self.request.user
        queryset = self.queryset

        # 确保每次返回的是独立的 QuerySet（避免污染）
        if hasattr(queryset, 'all'):
            queryset = queryset.all()  # Django ORM
        # 如果是 MongoEngine Document，则不需要 .all()，直接使用

        # 用户过滤
        queryset = queryset.filter(user=user)

        id = self.request.query_params.get("id")
        if id:
            queryset = queryset.filter(id=id)

        # is_active 过滤
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)

        # 名称模糊查询
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    @extend_schema(
        tags=["分类"],
        summary="分类列表查询",
        description="""
        功能：查询用户分类列表  
        限制：
        - 权限：需登录（JWT认证）  
        """,
        parameters=[
            OpenApiParameter(
                name="id",
                description="分类ID",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="is_active",
                description="是否激活",
                required=False,
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="is_active",
                description="是否激活",
                required=False,
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="name",
                description="分类名称",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
  

    @extend_schema(
        tags=["分类"],
        summary="分类详情查询",
        description="""
        功能：查询用户分类详情 
        限制：
        - 权限：需登录（JWT认证）  
    """,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["分类"],
        summary="创建分类",
        description="""
        功能：创建分类  
        限制：
        - 权限：需登录（JWT认证） 
        """,

    )
    def create(self, request, *args, **kwargs):
        """
        创建分类时，自动设置用户字段
        """
        try:
            user = self.request.user
            request.data["user"] = user.id
            
            # 调用父类方法创建分类
            response = super().create(request, *args, **kwargs)
            
            # 自定义成功响应
            if response.status_code == status.HTTP_201_CREATED:
                return Response({
                    "code": 200,
                    "message": "分类创建成功",
                    "data": response.data
                }, status=status.HTTP_201_CREATED)
            
            return response
        except Exception as e:
            # 异常处理
            return Response(
                {
                    "code": 400,
                    "message": f"分类创建失败: {str(e)}",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        tags=["分类"],
        summary="删除分类",
        description="""
        功能：删除分类  
        限制：
        - 权限：需登录（JWT认证）  
        """
    )
    def destroy(self, request, *args, **kwargs):
        """
        分类删除时，不考虑is_active字段，直接删除
        """
        id = kwargs["pk"]
        try:
            instance = Category.objects.get(id=id)
            instance.delete()
        except Category.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


    @extend_schema(
        tags=["分类"],
        summary="部分更新分类",
        description="""
        功能：部分更新分类  
        限制：
        - 权限：需登录（JWT认证）  
        """
    )
    def partial_update(self, request, *args, **kwargs):
        """
        部分更新分类
        """
        try:
            instance = self.get_object()  # 自动根据 pk 获取

            # 检查分类是否存在
            if instance.is_default:
                return Response({
                    "code": 200,
                    "message": "系统分类不能被修改",
                    "data": None
                })
            # 使用序列化器进行更新（DRF 标准流程）
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save()

            return Response({
                "code": 200,
                "message": "分类更新成功",
                "data": serializer.data  # 返回序列化后的数据
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": f"分类更新失败: {str(e)}",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
