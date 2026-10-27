"""Prepara la aplicación en una máquina nueva con un solo comando.

Hace todo lo que necesita un arranque limpio: migraciones, catálogo de
permisos, escenario de demo y cuentas de prueba. Después solo falta
``manage.py runserver``.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Prepara la aplicación: aplica migraciones, carga el catálogo de '
        'permisos, el escenario de demo (Festival 2027) y las cuentas de '
        'prueba. Es idempotente: puedes ejecutarlo tantas veces como '
        'quieras sin duplicar datos.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--sin-demo',
            action='store_true',
            help='Aplica solo migraciones, sin datos ni permisos de prueba.',
        )

    def handle(self, *args, **options):
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

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            'Aplicación preparada. Cuentas de prueba:'
        ))
        self.stdout.write('  Administrador  100200300 / admin123')
        self.stdout.write('  Organizador    100200301 / org123')
        self.stdout.write('  Votante        1015487962 / voto123')
        self.stdout.write('  Auditor        100200302 / aud123')
        self.stdout.write('')
        self.stdout.write('Para empezar:')
        self.stdout.write('  python manage.py runserver')
