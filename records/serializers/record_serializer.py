from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from ..models import Record, RawInput
from ..services.record_service import RecordService


class RecordSerializer(DocumentSerializer):
    
    processing_result = serializers.SerializerMethodField(read_only=True)
    title = serializers.CharField(required=False, allow_blank=True, default='')
    category_id = serializers.CharField(required=False, allow_blank=True, default='')
     
    class Meta:
        model = Record
        fields = '__all__'
        read_only_fields = [
            'id', 
            'user', 
            'type', 
            'content', 
            'category',
            'is_processed', 
            'processed_at', 
            'created_at', 
            'updated_at'
        ]

    
    def get_processing_result(self, obj):
        """返回处理结果"""
        return {
            'type': obj.type,
            'content': obj.content
        }
    
    
    def create(self, validated_data):
        """使用LLM服务创建记录"""
        # list
        raw_inputs_data = validated_data.pop('raw_inputs')

        if len(raw_inputs_data) == 0:
            raise serializers.ValidationError("raw_inputs 不能为空")

        title = validated_data.get('title', '')
        category_id = validated_data.get('category_id', '')
        
        # 获取当前用户
        request = self.context.get('request')
      
        if not request or not request.user:
            raise serializers.ValidationError("用户认证信息缺失")
        
        # 使用服务层创建记录
        record_service = RecordService()
        record = record_service.create_record_with_llm(
            title=title,
            raw_inputs_data=raw_inputs_data,
            user=request.user,
            category_id = category_id
        )
        
        return record