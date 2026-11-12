from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UsuarioSerializer(serializers.ModelSerializer):
    """Datos del usuario que el frontend muestra (nombre en el encabezado, etc.)."""

    nombre = serializers.SerializerMethodField()
    es_admin = serializers.BooleanField(source="is_staff", read_only=True)

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "nombre", "email", "es_admin"]
        read_only_fields = fields

    def get_nombre(self, obj):
        return obj.get_full_name() or obj.username


class LoginSerializer(TokenObtainPairSerializer):
    """Igual que el login estándar de JWT, pero además devuelve los datos del usuario,
    así el frontend no necesita una segunda consulta después de iniciar sesión."""

    default_error_messages = {
        "no_active_account": "Usuario o contraseña incorrectos.",
    }

    def validate(self, attrs):
        datos = super().validate(attrs)
        datos["usuario"] = UsuarioSerializer(self.user).data
        return datos
