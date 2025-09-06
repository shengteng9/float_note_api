from rest_framework_mongoengine.serializers import DocumentSerializer
from ..models import Tag

class TagSerializer(DocumentSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

