from rest_framework.response import Response
from rest_framework import status
from common.utils.exception_handler import ErrorCode


def success_response(data=None, message='Success', status_code=status.HTTP_200_OK):
    """
    生成成功响应
    
    Args:
        data: 响应数据，默认为None
        message: 成功消息，默认为'Success'
        status_code: HTTP状态码，默认为200
        
    Returns:
        Response: 包含标准格式的响应对象
    """
    return Response({
        'code': 0,
        'message': message,
        'data': data
    }, status=status_code)


def error_response(error_code, error_message, status_code=status.HTTP_400_BAD_REQUEST, data=None):
    """
    生成错误响应
    
    Args:
        error_code: 错误码
        error_message: 错误消息
        status_code: HTTP状态码，默认为400
        data: 可选的额外数据，默认为None
        
    Returns:
        Response: 包含标准格式的响应对象
    """
    return Response({
        'code': error_code,
        'message': error_message,
        'data': data
    }, status=status_code)