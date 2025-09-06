from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from accounts.models.user_model import User
import logging

logger = logging.getLogger(__name__)

class MongoJWTAuthentication(JWTAuthentication):
    
    def authenticate(self, request):
        # 对于Swagger和Token API路径，跳过认证
        path = request.path
        if path.startswith('/swagger/') or path.startswith('/redoc/') or path.startswith('/api/token/'):
            return None
        
        try:
            # 调用父类的authenticate方法
            return super().authenticate(request)
        except Exception as e:
            logger.error(f"JWT认证失败: {str(e)}")
            # 不抛出异常，让权限类决定是否允许访问
            return None

    def get_user(self, validated_token):
        try:
            user_id = validated_token.get('user_id')
            
            if not user_id:
                raise AuthenticationFailed("JWT中缺少user_id")
            
            user = User.objects.get(id=user_id)
            
            if not user:
                raise AuthenticationFailed("无效的用户")
            
            return user
        except User.DoesNotExist:
            logger.error(f"用户不存在: {user_id}")
            raise AuthenticationFailed("用户不存在")
        except Exception as e:
            logger.error(f"JWT认证过程中出错: {str(e)}")
            # 不抛出异常，允许匿名访问
            return None