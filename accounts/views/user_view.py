
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from ..models import User
from ..serializers import UserSerializer
from common.utils.exception_handler import CustomException, ErrorCode
from common.utils.response_utils import success_response, error_response


class UserViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for managing users.
    create接口无需token验证，其他接口均需token验证
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request):
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, pk=None):
        try:
            user = User.objects.get(id=pk)
            serializer = UserSerializer(user)
            return success_response(data=serializer.data)
        except User.DoesNotExist:
            raise CustomException(
                error_code=ErrorCode.USER_NOT_FOUND,
                error_message=f"User with id {pk} does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )

    # create接口无需token验证
    def create(self, request):
        # 临时修改权限类为允许任何用户
        self.permission_classes = [permissions.AllowAny]
        # 检查权限
        self.check_permissions(request)
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(
                data=serializer.data,
                message='User created successfully',
                status_code=status.HTTP_201_CREATED
            )
        # 让序列化器的验证错误由全局异常处理器自动捕获和格式化
        # 或者如果需要自定义用户名重复错误的处理
        username = request.data.get('username')
        if username and 'username' in serializer.errors:
            raise CustomException(
                error_code=ErrorCode.USERNAME_ALREADY_EXISTS,
                error_message=f"Username '{username}' already exists",
                status_code=status.HTTP_409_CONFLICT
            )
        # 对于其他验证错误，使用统一错误响应格式
        return error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            error_message='Validation error',
            status_code=status.HTTP_400_BAD_REQUEST,
            data={'errors': serializer.errors}
        )

    def update(self, request, pk=None):
        try:
            # 尝试使用id查找用户
            user = User.objects.get(id=pk)
            
            serializer = UserSerializer(user, data=request.data)
            
            if serializer.is_valid():
                serializer.save()
                return success_response(
                    data=serializer.data,
                    message='User updated successfully'
                )
            else:
                print('Serializer errors:', serializer.errors)
            # 这里不需要手动抛出异常，使用统一错误响应格式
            return error_response(
                error_code=ErrorCode.VALIDATION_ERROR,
                error_message='Validation error',
                status_code=status.HTTP_400_BAD_REQUEST,
                data={'errors': serializer.errors}
            )
        except User.DoesNotExist:
            raise CustomException(
                error_code=ErrorCode.USER_NOT_FOUND,
                error_message=f"User with id {pk} does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise CustomException(
                error_code=ErrorCode.UNKNOWN_ERROR,
                error_message=f"Unexpected error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            # 一般异常会被全局异常处理器捕获并格式化

    def partial_update(self, request, pk=None):
        try:
            user = User.objects.get(id=pk)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return success_response(
                    data=serializer.data,
                    message='User updated successfully'
                )
            return error_response(
                error_code=ErrorCode.VALIDATION_ERROR,
                error_message='Validation error',
                status_code=status.HTTP_400_BAD_REQUEST,
                data={'errors': serializer.errors}
            )
        except User.DoesNotExist:
            raise CustomException(
                error_code=ErrorCode.USER_NOT_FOUND,
                error_message=f"User with id {pk} does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        try:
            user = User.objects.get(id=pk)
            user.delete()
            return success_response(
                message='User deleted successfully',
                status_code=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            raise CustomException(
                error_code=ErrorCode.USER_NOT_FOUND,
                error_message=f"User with id {pk} does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )