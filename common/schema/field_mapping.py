
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from rest_framework_mongoengine.fields import ObjectIdField

# 扩展 spectacular 的字段识别
from drf_spectacular.contrib.djangorestframework import serializer_field_mapping

# 添加 ObjectIdField 映射
serializer_field_mapping.update({
    ObjectIdField: OpenApiTypes.STR,  # 或者 OpenApiTypes.OBJECT if you want to keep it as object
})