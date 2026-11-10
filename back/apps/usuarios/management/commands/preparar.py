"""Prepara la aplicación en una máquina nueva con un solo comando.

Hace todo lo que necesita un arranque limpio: migraciones, catálogo de
permisos, escenario de demo y cuentas de prueba. Después solo falta
``manage.py runserver``.

Con MySQL, si la base de datos definida en ``DB_NAME`` no existe la crea
(``CREATE DATABASE IF NOT EXISTS``, juego de caracteres utf8mb4); si ya
existe simplemente la usa sin tocar su contenido.
"""

import re

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, OperationalError


def _asegurar_mysql(self):
    """Crea la BD de MySQL si falta; la usa tal cual si existe.

    Django no puede crear la base de datos con ``migrate`` (necesita
    conectarse a ella), así que se intenta conectar normal y solo cuando
    el error sea "unknown database" se reconecta sin BD y se crea.
    """
    if connection.settings_dict['ENGINE'] != 'django.db.backends.mysql':
        return
    configuracion = connection.settings_dict
    nombre = configuracion['NAME']
    if not re.fullmatch(r'[A-Za-z0-9_\-]+', str(nombre)):
        raise CommandError(
            f'El nombre de base de datos "{nombre}" tiene caracteres no válidos.'
        )

    try:
        connection.ensure_connection()
        return  # La BD responde: existe, se usa tal cual.
    except OperationalError as error:
        if not any(m in str(error).lower() for m in ('unknown database', "doesn't exist")):
            # No coincide la clave o el servidor está apagado, etc.: es error real.
            raise

    # Import local: con SQLite no se necesita el conector de MySQL instalado.
    import MySQLdb

    db = MySQLdb.connect(
        host=configuracion['HOST'],
        port=int(configuracion['PORT']),
        user=configuracion['USER'],
        passwd=configuracion['PASSWORD'],
        charset='utf8mb4',
    )
    with db.cursor() as cursor:
        cursor.execute(
            f'CREATE DATABASE IF NOT EXISTS `{nombre}` '
            'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
        )
    db.close()
    self.stdout.write(self.style.WARNING(
        f'Base de datos MySQL "{nombre}" creada (no existía). Si ya tenía '
        'datos, revise que sea la correcta.'
    ))


# Votantes de demo con nombre realista que crea la simulación.
VOTANTES_DEMO = 120

# Votos ya emitidos por las cuentas de prueba (documento, votación, orden de
# la opción), para que su historial y sus comprobantes se vean desde el inicio.
VOTOS_CUENTAS_DEMO = [
    ('1015487962', 'Canción favorita del público', 1),  # Cardina
    ('1015987412', 'Canción favorita del público', 2),  # Sofía
]


def _votos_cuentas_demo(self):
    """Emite los votos de las cuentas de prueba que aún no hayan votado."""
    from back.apps.elecciones.models import Opcion
    from back.apps.votacion.management.commands.simular_votacion import emitir_voto

    User = get_user_model()
    for documento, nombre_votacion, orden in VOTOS_CUENTAS_DEMO:
        user = User.objects.filter(perfil_usuario__documento=documento).first()
        opcion = (
            Opcion.objects.select_related('votacion')
            .filter(
                votacion__nombre=nombre_votacion,
                votacion__edicion__nombre='Festival 2027',
                orden=orden,
            )
            .first()
        )
        if user and opcion:
            emitir_voto(user, opcion)


class Command(BaseCommand):
    help = (
        'Prepara la aplicación: aplica migraciones, carga el catálogo de '
        'permisos, el escenario de demo (Festival 2027), las cuentas de '
        'prueba y votos simulados. Es idempotente: puedes ejecutarlo '
        'tantas veces como quieras sin duplicar datos.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--sin-demo',
            action='store_true',
            help='Aplica solo migraciones, sin datos ni permisos de prueba.',
        )

    def handle(self, *args, **options):
        _asegurar_mysql(self)

        self.stdout.write('Migraciones...')
        call_command('migrate', interactive=False)

        if options['sin_demo']:
            self.stdout.write(self.style.SUCCESS(
                'Aplicación preparada (sin datos de demo).'
            ))
            return

        self.stdout.write('Permisos...')
        call_command('cargar_permisos')

        self.stdout.write('Escenario de demo: Festival 2027...')
        call_command('cargar_demo')

        self.stdout.write('Escenario de demo: Festival de la Leyenda Vallenata...')
        call_command('cargar_leyenda')

        self.stdout.write('Cuentas de prueba...')
        call_command('cargar_usuarios_demo')

        self.stdout.write('Votos de las cuentas de prueba...')
        _votos_cuentas_demo(self)

        self.stdout.write('Datos de votación simulados en todas las votaciones...')
        call_command('simular_votacion', todas=True, votantes=VOTANTES_DEMO)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            'Aplicación preparada. Cuentas de prueba:'
        ))
        self.stdout.write('  Administrador  100200300 / admin123')
        self.stdout.write('  Organizador    100200301 / org123')
        self.stdout.write('  Votante        1015487962 / voto123')
        self.stdout.write('  Auditor        100200302 / aud123')
        self.stdout.write(
            f'  Votantes demo  90XXXXXXXX  / voto123 ({VOTANTES_DEMO} cuentas)'
        )
        self.stdout.write('')
        self.stdout.write('Para empezar:')
        self.stdout.write('  python manage.py runserver')
