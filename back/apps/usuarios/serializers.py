from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Permission, Role, RolPermiso, Usuario

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
        correo = attrs.get('correo')
        documento = attrs.get('documento')

        if User.objects.filter(email__iexact=correo).exists():
            raise serializers.ValidationError({'correo': 'Este correo ya está registrado.'})
        if Usuario.objects.filter(documento=documento).exists():
            raise serializers.ValidationError({'documento': 'Este documento ya está registrado.'})

        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        rol_id = validated_data.pop('rol_id', None)

        username = validated_data['correo'].split('@')[0] or validated_data['documento']
        username = username[:30]
        username_base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{username_base}{counter}'
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=validated_data['correo'],
            password=password,
            first_name=validated_data['nombres'],
            last_name=validated_data['apellidos'],
        )

        rol = None
        if rol_id:
            rol = Role.objects.filter(id=rol_id).first()
        if rol is None:
            rol, _ = Role.objects.get_or_create(nombre='Votante', defaults={'descripcion': 'Usuario común'} )

        perfil = Usuario.objects.create(
            user=user,
            documento=validated_data['documento'],
            nombres=validated_data['nombres'],
            apellidos=validated_data['apellidos'],
            correo=validated_data['correo'],
            rol=rol,
        )

        return {'user': user, 'perfil': perfil}


class LoginSerializer(serializers.Serializer):
    correo = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        correo = attrs.get('correo')
        password = attrs.get('password')

        if not correo or not password:
            raise serializers.ValidationError('Correo y contraseña son obligatorios.')

        user = User.objects.filter(email__iexact=correo).first()
        if user is None or not user.check_password(password):
            raise serializers.ValidationError('Credenciales inválidas.')

        if not user.is_active:
            raise serializers.ValidationError('Usuario inactivo.')

        attrs['user'] = user
        return attrs
