from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from ..models import Category, FieldSpec



class CategorySerializer(DocumentSerializer):

    class Meta:
        model = Category
        fields = '__all__'

def validate_name(self, value):
    """
    验证name字段：同一用户下不允许重复
    """
    user = self.context['request'].user
    queryset = Category.objects.filter(
        user=user,
        name=value
    )
    if self.instance:
        queryset = queryset.exclude(pk=self.instance.pk)
    
    if queryset.exists():  # ✅ 正确：检查是否存在匹配记录
        raise serializers.ValidationError(f"你已存在名为 '{value}' 的分类，请更换其他名称")

    return value
