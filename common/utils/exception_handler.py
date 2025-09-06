from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

# 获取logger
exception_logger = logging.getLogger('django')

class ErrorCode:
    # 系统级错误码（1000-1999）
    SYSTEM_ERROR = 1000 # 系统错误
    DATABASE_ERROR = 1001 # 数据库错误
    NETWORK_ERROR = 1002 # 网络错误
    AUTHENTICATION_ERROR = 1003 # 认证错误
    PERMISSION_ERROR = 1004 # 权限错误
    RATE_LIMIT_ERROR = 1005 # 限流错误
    INVALID_REQUEST = 1006 # 无效请求
    VALIDATION_ERROR = 1007 # 验证错误
    RESOURCE_NOT_FOUND = 1008 # 资源不存在
    DUPLICATE_RESOURCE = 1009 # 重复资源
    SERVER_BUSY = 1010 # 服务器繁忙
    INTERNAL_SERVER_ERROR = 1011 # 内部服务器错误

    # 用户相关错误码（2000-2999）
    USER_NOT_FOUND = 2001
    USERNAME_ALREADY_EXISTS = 2002
    INVALID_PASSWORD = 2003
    USER_INACTIVE = 2004
    USER_BANNED = 2005

    # 业务相关错误码（3000+）
    # 可以根据具体业务模块添加更多错误码
    CREATE_FAILED = 3001


class CustomException(Exception):
    """
    自定义异常类，用于封装错误码和错误信息
    """
    def __init__(self, error_code, error_message, status_code=status.HTTP_400_BAD_REQUEST):
        self.error_code = error_code
        self.error_message = error_message
        self.status_code = status_code
        super().__init__(error_message)


def custom_exception_handler(exc, context):
    
    """
    自定义异常处理器，统一处理REST Framework的异常
    """
    # 首先调用默认的异常处理机制获取标准的错误响应
    response = exception_handler(exc, context)
    request = context.get('request')
    view = context.get('view')
    
    # 记录异常信息
    error_info = {
        'path': request.path if request else 'unknown',
        'method': request.method if request else 'unknown',
        'view': str(view.__class__.__name__) if view else 'unknown',
        'error_type': exc.__class__.__name__,
        'error_message': str(exc)
    }
    
    # 处理自定义异常
    if isinstance(exc, CustomException):
        exception_logger.warning(f"Custom exception: {error_info}")
        return Response({
            'code': exc.error_code,
            'message': exc.error_message,
            'data': None
        }, status=exc.status_code)
    
    # 处理序列化器验证错误
    elif response is not None and status.is_client_error(response.status_code) and 'detail' not in response.data:
        exception_logger.warning(f"Validation error: {error_info}")
        # 格式化验证错误信息
        error_messages = []
        for field, errors in response.data.items():
            if isinstance(errors, list):
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            else:
                error_messages.append(f"{field}: {errors}")
                
        return Response({
            'code': ErrorCode.VALIDATION_ERROR,
            'message': 'Validation error',
            'data': {
                'errors': response.data
            }
        }, status=response.status_code)
    
    # 处理404错误
    elif response is not None and response.status_code == status.HTTP_404_NOT_FOUND:
        exception_logger.warning(f"Resource not found: {error_info}")
        return Response({
            'code': ErrorCode.RESOURCE_NOT_FOUND,
            'message': 'Resource not found',
            'data': None
        }, status=response.status_code)
    
    # 处理认证错误
    elif response is not None and response.status_code == status.HTTP_401_UNAUTHORIZED:
        exception_logger.warning(f"Authentication error: {error_info}")
        return Response({
            'code': ErrorCode.AUTHENTICATION_ERROR,
            'message': 'Authentication required',
            'data': None
        }, status=response.status_code)
    
    # 处理权限错误
    elif response is not None and response.status_code == status.HTTP_403_FORBIDDEN:
        exception_logger.warning(f"Permission error: {error_info}")
        return Response({
            'code': ErrorCode.PERMISSION_ERROR,
            'message': "You don't have permission to access this resource",
            'data': None
        }, status=response.status_code)
    
    # 处理500错误
    elif response is not None and status.is_server_error(response.status_code):
        exception_logger.error(f"Server error: {error_info}")
        return Response({
            'code': ErrorCode.SYSTEM_ERROR,
            'message': 'Internal server error',
            'data': None
        }, status=response.status_code)
    
    # 对于其他类型的逾期，使用默认的ukai处理机制
    return response
