from django.conf import settings
from django.db import models


class Role(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre


class Permission(models.Model):
    codigo = models.CharField(max_length=100, unique=True)
    modulo = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'permisos'

    def __str__(self):
        return self.codigo


class RolPermiso(models.Model):
    rol = models.ForeignKey('Role', on_delete=models.CASCADE, related_name='permisos_asignados')
    permiso = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='roles_asignados')

    class Meta:
        db_table = 'rol_permisos'
        constraints = [
            models.UniqueConstraint(fields=['rol', 'permiso'], name='uq_rol_permiso')
        ]

    def __str__(self):
        return f'{self.rol} -> {self.permiso}'


class Usuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_usuario'
    )
    documento = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    rol = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='usuarios')
    estado = models.CharField(max_length=20, default='ACTIVO')
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'


class SessionToken(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='sesiones')
    token_hash = models.CharField(max_length=256, unique=True)
    ip_origen = models.CharField(max_length=45)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    revocado = models.BooleanField(default=False)

    class Meta:
        db_table = 'sesiones_tokens'

    def __str__(self):
        return f'Sesión de {self.usuario}'
