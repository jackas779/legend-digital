"""Borra los datos de votación de prueba para repetir el flujo (entregable U4)."""

from django.core.management.base import BaseCommand

from back.apps.votacion.models import PadronVotante, Voto


class Command(BaseCommand):
    help = (
        'Borra votos y padrones de prueba. Conserva ediciones, categorías, '
        'votaciones y opciones para poder repetir el flujo de votación.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Requerido para ejecutar el borrado.',
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stderr.write(
                'Esto borra TODOS los votos y padrones. Confirma con --confirmar.'
            )
            raise SystemExit(1)

        votos, _ = Voto.objects.all().delete()
        padrones, _ = PadronVotante.objects.all().delete()

        self.stdout.write(
            f'Reset listo: {votos} votos y {padrones} padrones borrados. '
            'Las votaciones y opciones quedan intactas.'
        )
