from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers.jwt_serializer import CustomTokenObtainPairSerializer
from rest_framework.response import Response

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
    
        response = super().post(request, *args, **kwargs)
        
        if response.data and 'refresh' in response.data and 'access' in response.data:
 
            token_data = response.data

            return Response({
                'code': 0,
                'message': 'Authentication successful',
                'data': token_data
            }, status=response.status_code)
        
        # 如果已经是统一格式，直接返回
        return response