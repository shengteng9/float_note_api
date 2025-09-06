from unicodedata import category
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import  OpenApiTypes
from ..models import Category
from accounts.models.user_model import User




class SchemaViewSet(APIView):
    """提供完整schema信息的API端点"""
    serializer_class = serializers.FileField()
    @extend_schema(
        tags=['记录的schema'],
        summary='获取schema信息',
        description='根据分类名称获取分类的schema信息',
        parameters=[
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="分类名称，可选参数。指定时返回该分类的schema，不指定时返回所有激活分类的schema",
            )
        ],
        responses={
            200: OpenApiResponse(
                description="成功获取schema信息",
                examples={
                    "application/json": {
                        "category": {
                            "id": "65a1b2c3d4e5f6a7b8c9d0e1",
                            "name": "示例分类",
                            "description": "这是一个示例分类"
                        },
                        "fields": {
                            "field1": {
                                "type": "string",
                                "required": True,
                                "default": None,
                                "description": "字段描述",
                                "ref_model": None
                            }
                        },
                        "required_fields": ["field1"],
                        "example": {
                            "title": "示例记录",
                            "category_name": "示例分类",
                            "standardized_data": {
                                "field1": "示例值"
                            }
                        }
                    }
                }
            ),
            404: OpenApiResponse(
                description="指定的分类不存在或未激活",
                examples={
                    "application/json": {
                        "error": "分类不存在或未激活"
                    }
                }
            )
        },
    )
    def get(self, request):
        category_name = request.query_params.get('category')
        
        if category_name:
            try:
                category = Category.objects.get(name=category_name, is_active=True)
                schema = self._generate_cate_schema(category)
                return Response(schema)
            except Category.DoesNotExist:
                return Response({'error': '分类不存在或未激活'}, status=404)
        else:
            # 返回所有分类的schema
            schemas = {}
            for category in Category.objects.filter(is_active=True):
                schemas[category.name] = self._generate_cate_schema(category)
            return Response(schemas)
    
    def _generate_cate_schema(self, category):
        """生成单个分类的完整schema信息"""
        fields_info = {}
        required_fields = []
        
        for spec in category.field_specs:
            field_info = {
                'type': spec.field_type,
                'required': spec.required,
                'default': spec.default,
                'description': spec.description,
                'ref_model': spec.ref_model
            }
            
            fields_info[spec.name] = field_info
            
            if spec.required:
                required_fields.append(spec.name)
        
        return {
            'category': {
                'id': str(category.id),
                'name': category.name,
                'description': category.description
            },
            'fields': fields_info,
            'required_fields': required_fields,
            'example': self._generate_example(category)
        }
    
    def _generate_example(self, category):
        """生成示例数据"""
        example = {
            'title': f'示例{category.name}记录',
            'cate_name': category.name,
            'standardized_data': {}
        }
        
        for spec in category.field_specs:
            example_value = self._get_example_value(spec)
            example['standardized_data'][spec.name] = example_value
        
        return example
    
    def _get_example_value(self, spec):
        """根据字段规范生成示例值"""
        examples = {
            'string': '示例文本',
            'number': 123.45,
            'boolean': True,
            'date': '2024-01-25T10:30:00Z',
            'array': ['项目1', '项目2'],
            'reference': '65a1b2c3d4e5f6a7b8c9d0e1'
        }
        return examples.get(spec.field_type, '示例值')