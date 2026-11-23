"""Aplica los cambios de estado que tocan por fecha (para un cron).

El middleware ya los aplica en cada petición; este comando sirve para que
ocurran a la hora exacta aunque nadie esté usando la plataforma:

    */5 * * * *  python manage.py sincronizar_estados
"""

from django.core.management.base import BaseCommand

from back.apps.elecciones.ciclo import sincronizar


class Command(BaseCommand):
    help = 'Activa, abre y cierra ediciones y votaciones según sus fechas.'

    def handle(self, *args, **options):
        procesadas = sincronizar()
        self.stdout.write(self.style.SUCCESS(
            f'Estados sincronizados: {procesadas} edición(es) con cambios por fecha.'
        ))
