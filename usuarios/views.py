from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView

from .serializers import LoginSerializer, UsuarioSerializer


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Cuerpo: {"username": "...", "password": "..."}
    Respuesta: {"access": "...", "refresh": "...", "usuario": {...}}
    El "access" se envía en cada consulta con el encabezado: Authorization: Bearer <access>
    """

    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class RefreshView(TokenRefreshView):
    """
    POST /api/auth/refresh/
    Cuerpo: {"refresh": "..."}
    Respuesta: {"access": "...", "refresh": "..."} (el refresh anterior deja de servir)
    """


class LogoutView(TokenBlacklistView):
    """
    POST /api/auth/logout/
    Cuerpo: {"refresh": "..."}
    Invalida el refresh para que no se pueda volver a usar. El frontend además
    debe borrar ambos tokens de su almacenamiento.
    """


class PerfilView(APIView):
    """
    GET /api/auth/perfil/
    Devuelve los datos del usuario que inició sesión.
    """

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)
