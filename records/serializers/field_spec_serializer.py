from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer

class FieldSpecSerializer(serializers.Serializer):
    name = serializers.CharField()
    field_type = serializers.ChoiceField(choices=[
        'string', 
        'number', 
        'boolean', 
        'date', 
        'array', 
        'reference'
    ])
    required = serializers.BooleanField(default=False)
    default = serializers.JSONField(allow_null=True)
    ref_model = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)