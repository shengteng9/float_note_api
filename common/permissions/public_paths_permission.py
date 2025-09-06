from rest_framework.permissions import IsAuthenticated, AllowAny

class PublicPathsPermission(IsAuthenticated):
    """
    自定义权限类，允许特定路径的匿名访问
    其他路径保持需要认证的状态
    """
    # 定义允许匿名访问的路径前缀列表
    PUBLIC_PATHS = [
        '/swagger/',
        '/redoc/',
        '/api/token/',
        '/api/schema/',
    ]
    
    def has_permission(self, request, view):
        # 检查请求路径是否以允许的公共路径前缀开头
        path = request.path
        for public_path in self.PUBLIC_PATHS:
            if path.startswith(public_path):
                # 对于公共路径，始终返回True（允许访问）
                return True
        
        # 对于非公共路径，使用默认的IsAuthenticated权限检查
        return super().has_permission(request, view)

class PublicPathsAllowAny(AllowAny):
    """
    简单的允许任何访问的权限类，用作安全的备选方案
    """
    pass