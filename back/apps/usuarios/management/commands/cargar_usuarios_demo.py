"""Crea los usuarios de prueba alineados con las cuentas demo del front."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from back.apps.usuarios.models import Role, Usuario

User = get_user_model()

DESCRIPCION_ROLES = {
    'Administrador': 'Control total del sistema',
    'Organizador': 'Gestiona ediciones, categorías, votaciones y opciones',
    'Votante': 'Usuario común: elige una opción y vota',
    'Auditor': 'Solo lectura de resultados y padrón',
}

# Mismas credenciales que front/src/lib/data.js (CUENTAS_DEMO) para poder
# probar el flujo real sin cambiar de usuario.
CUENTAS = [
    {
        'rol': 'Administrador',
        'documento': '100200300',
        'nombres': 'Laura',
        'apellidos': 'Restrepo',
        'correo': 'laura.restrepo@uni.edu.co',
        'password': 'admin123',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'rol': 'Organizador',
        'documento': '100200301',
        'nombres': 'Andrés',
        'apellidos': 'Catalán',
        'correo': 'andres.catalan@uni.edu.co',
        'password': 'org123',
        'is_staff': True,
        'is_superuser': False,
    },
    {
        'rol': 'Votante',
        'documento': '1015487962',
        'nombres': 'Cardina',
        'apellidos': 'Rentería',
        'correo': 'cardi.renteria@uni.edu.co',
        'password': 'voto123',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'rol': 'Auditor',
        'documento': '100200302',
        'nombres': 'Martha',
        'apellidos': 'Lucumí',
        'correo': 'martha.lucumi@uni.edu.co',
        'password': 'aud123',
        'is_staff': True,
        'is_superuser': False,
    },
    # Votantes adicionales para probar el conteo y los estados.
    {
        'rol': 'Votante',
        'documento': '1015987412',
        'nombres': 'Sofía',
        'apellidos': 'Márquez',
        'correo': 'sofia.marquez@uni.edu.co',
        'password': 'voto123',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'rol': 'Votante',
        'documento': '1023654789',
        'nombres': 'Julián',
        'apellidos': 'Ospina',
        'correo': 'julian.ospina@uni.edu.co',
        'password': 'voto123',
        'is_staff': False,
        'is_superuser': False,
        'estado': 'SUSPENDIDO',
    },
]


def _username_unico(correo, documento):
    base = (correo.split('@')[0] or documento)[:30]
    username = base
    contador = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{contador}'
        contador += 1
    return username


class Command(BaseCommand):
    help = (
        'Crea los roles base y los usuarios de prueba (Administrador, '
        'Organizador, Votante y Auditor) con las credenciales del front demo.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Restablece la contraseña de los usuarios que ya existan.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset = options['reset_passwords']

        roles = {}
        for nombre, descripcion in DESCRIPCION_ROLES.items():
            rol, _ = Role.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion},
            )
            roles[nombre] = rol

        creados = 0
        actualizados = 0

        for cuenta in CUENTAS:
            user = User.objects.filter(email__iexact=cuenta['correo']).first()

            if user is None:
                user = User.objects.create_user(
                    username=_username_unico(cuenta['correo'], cuenta['documento']),
                    email=cuenta['correo'],
                    password=cuenta['password'],
                    first_name=cuenta['nombres'],
                    last_name=cuenta['apellidos'],
                )
                creados += 1
            else:
                if reset:
                    user.set_password(cuenta['password'])
                actualizados += 1

            user.is_staff = cuenta['is_staff']
            user.is_superuser = cuenta['is_superuser']
            user.is_active = True
            user.first_name = cuenta['nombres']
            user.last_name = cuenta['apellidos']
            user.save()

            Usuario.objects.update_or_create(
                user=user,
                defaults={
                    'documento': cuenta['documento'],
                    'nombres': cuenta['nombres'],
                    'apellidos': cuenta['apellidos'],
                    'correo': cuenta['correo'],
                    'rol': roles[cuenta['rol']],
                    'estado': cuenta.get('estado', 'ACTIVO'),
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f'Usuarios de prueba listos: {creados} creados, {actualizados} actualizados.'
        ))
        self.stdout.write('')
        self.stdout.write('  Rol            Documento     Clave')
        self.stdout.write('  -------------  ------------  ---------')
        for cuenta in CUENTAS:
            self.stdout.write(
                f"  {cuenta['rol']:<13}  {cuenta['documento']:<12}  {cuenta['password']}"
            )
        self.stdout.write('')
        self.stdout.write('Puedes iniciar sesión con el documento, el correo o el usuario.')
