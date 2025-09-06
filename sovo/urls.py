from django.urls import include, path


# drf-spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# jwt
from rest_framework_simplejwt.views import (
    TokenRefreshView,     # 刷新 Token
)
from accounts.views.jwt_views import CustomTokenObtainPairView
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    # drf-spectacular API 文档
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
      # 子应用路由
    path('api/', include('accounts.urls')),  # accounts 的路由
    path('api/record/', include('records.urls')),  # records 的路由
     # 
    path('api/common/', include('common.urls')),  # common 的路由
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #static() 仅适用于开发环境，生产环境必须通过 Nginx/Apache 等服务器处理静态文件。此配置仅适用于开发环境（DEBUG=True）。