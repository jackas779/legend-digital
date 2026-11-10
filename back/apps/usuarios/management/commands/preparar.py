"""Prepara la aplicación en una máquina nueva con un solo comando.

Hace todo lo que necesita un arranque limpio: migraciones, catálogo de
permisos, escenario de demo y cuentas de prueba. Después solo falta
``manage.py runserver``.

Con MySQL, si la base de datos definida en ``DB_NAME`` no existe la crea
(``CREATE DATABASE IF NOT EXISTS``, juego de caracteres utf8mb4); si ya
existe simplemente la usa sin tocar su contenido.
"""

import re

import MySQLdb
from django.conf import settings
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

        self.stdout.write('Escenario de demo...')
        call_command('cargar_demo')

        self.stdout.write('Cuentas de prueba...')
        call_command('cargar_usuarios_demo')

        self.stdout.write('Datos de votación simulados...')
        call_command('simular_votacion')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            'Aplicación preparada. Cuentas de prueba:'
        ))
        self.stdout.write('  Administrador  100200300 / admin123')
        self.stdout.write('  Organizador    100200301 / org123')
        self.stdout.write('  Votante        1015487962 / voto123')
        self.stdout.write('  Auditor        100200302 / aud123')
        self.stdout.write('  Votantes demo  90XXXXXXXX  / voto123 (40 cuentas)')
        self.stdout.write('')
        self.stdout.write('Para empezar:')
        self.stdout.write('  python manage.py runserver')
