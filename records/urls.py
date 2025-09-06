from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecordViewSet, CategoryViewSet, SchemaViewSet, TagViewSet

router = DefaultRouter()
router.register(r'records', RecordViewSet, basename='record')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
    path('schema-info/', SchemaViewSet.as_view(), name='schema-info'),
]
