from django.contrib.auth import get_user_model
from rest_framework import serializers

from .auth import autenticar
from .models import Permission, Role, RolPermiso, Usuario
from .services import crear_cuenta, validar_cuenta_libre, validar_password

User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'codigo', 'modulo', 'descripcion']


class RoleSerializer(serializers.ModelSerializer):
    permisos = PermissionSerializer(many=True, read_only=True, source='permisos_asignados.permiso')

    class Meta:
        model = Role
        fields = ['id', 'nombre', 'descripcion', 'permisos']


class UserProfileSerializer(serializers.ModelSerializer):
    rol = RoleSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'documento', 'nombres', 'apellidos', 'correo', 'rol', 'estado']


class RegisterSerializer(serializers.Serializer):
    documento = serializers.CharField(max_length=20)
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    correo = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    rol_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        errores = validar_cuenta_libre(attrs.get('documento'), attrs.get('correo'))
        if errores:
            raise serializers.ValidationError(errores)

        mensajes = validar_password(attrs.get('password'))
        if mensajes:
            raise serializers.ValidationError({'password': mensajes})

        return attrs

    def create(self, validated_data):
        rol_id = validated_data.pop('rol_id', None)
        rol = Role.objects.filter(id=rol_id).first() if rol_id else None

        user, perfil = crear_cuenta(
            documento=validated_data['documento'],
            nombres=validated_data['nombres'],
            apellidos=validated_data['apellidos'],
            correo=validated_data['correo'],
            password=validated_data['password'],
            rol=rol,
        )
        return {'user': user, 'perfil': perfil}


class LoginSerializer(serializers.Serializer):
    """Acepta correo, nombre de usuario o documento.

    Toda la lógica (bloqueo, estado de la cuenta, conteo de fallos) vive en
    ``back.apps.usuarios.auth`` para compartirla con el login MVT.
    """

    correo = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user, error = autenticar(attrs.get('correo'), attrs.get('password'))
        if error:
            raise serializers.ValidationError(error)

        attrs['user'] = user
        return attrs
