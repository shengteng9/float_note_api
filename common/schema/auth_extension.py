# swagger :could not resolve authenticator

from drf_spectacular.extensions import OpenApiAuthenticationExtension

class MongoJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'accounts.authentication.jwt_backend.MongoJWTAuthentication'
    name = 'bearerAuth'  # 或 'MongoJWTAuth'
    match_subclasses = True
    priority = 1

    def get_authenticator(self):
        return {}

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "name": "Authorization",
            "in": "header",
            "description": "Enter 'Bearer <token>'"
        }