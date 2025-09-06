
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import status

from accounts.models.user_model import User
import logging
from common.utils.exception_handler import ErrorCode

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # 重写validate方法以确保正确处理密码验证
    def validate(self, attrs):
        try:
            # 获取用户输入的密码和用户名
            password = attrs.get('password')
            username = attrs.get('username')
            
            # 直接查找用户
            user = User.objects.get(username=username)
            logger.debug(f"Found user: {username} for token generation")
            
            if user.check_password(password):
                logger.debug(f"Password validation successful for user: {username}")
                # 验证通过后，生成token
                token = self.get_token(user)
                # 构建统一格式的响应数据
                return {
                    'code': 0,
                    'message': 'Authentication successful',
                    'data': {
                        'refresh': str(token),
                        'access': str(token.access_token),
                    }
                }
            else:
                logger.warning(f"Password validation failed for user: {username}")
                # 使用错误码和更明确的消息
                raise AuthenticationFailed({
                    'code': ErrorCode.AUTHENTICATION_ERROR,
                    'message': '密码验证失败',
                    'data': None
                })
        except User.DoesNotExist:
            logger.warning(f"User not found: {username}")
            # 使用错误码和更明确的消息
            raise AuthenticationFailed({
                'code': ErrorCode.USER_NOT_FOUND,
                'message': f'用户 {username} 不存在',
                'data': None
            })
        except Exception as e:
            logger.error(f"Error during token generation: {str(e)}")
            raise AuthenticationFailed({
                'code': ErrorCode.AUTHENTICATION_ERROR,
                'message': '认证失败',
                'data': str(e)
            })
    
    # 重写get_token方法，确保正确处理MongoDB的ObjectId
    @classmethod
    def get_token(cls, user):
        # 关键修复：确保user.id被正确转换为字符串
        token = super().get_token(user)
        # 添加额外信息到token中
        token['username'] = user.username
        # 显式存储用户ID的字符串表示
        token['user_id'] = str(user.id)
        return token
        