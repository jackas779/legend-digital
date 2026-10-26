from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Permission, Role, RolPermiso, Usuario
from .serializers import (
    LoginSerializer,
    PermissionSerializer,
    RegisterSerializer,
    RoleSerializer,
    UserProfileSerializer,
)

User = get_user_model()


def health_view(request):
    return JsonResponse({'status': 'ok', 'module': 'usuarios'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Un superusuario creado con createsuperuser no tiene perfil Usuario.
        # En ese caso devolvemos los datos básicos de la cuenta para no romper el login.
        perfil = getattr(request.user, 'perfil_usuario', None)
        if perfil is None:
            return Response({
                'id': request.user.id,
                'documento': '',
                'nombres': request.user.first_name,
                'apellidos': request.user.last_name,
                'correo': request.user.email,
                'rol': None,
                'estado': 'ACTIVO' if request.user.is_active else 'INACTIVO',
            })

        serializer = UserProfileSerializer(perfil)
        return Response(serializer.data)


class RoleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer


class PermissionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Permission.objects.all().order_by('id')
    serializer_class = PermissionSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = serializer.save()
        user = result['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Usuario registrado correctamente.',
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'correo': user.email,
                'nombres': user.first_name,
                'apellidos': user.last_name,
            },
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'correo': user.email,
                'nombres': user.first_name,
                'apellidos': user.last_name,
            },
        }, status=status.HTTP_200_OK)
