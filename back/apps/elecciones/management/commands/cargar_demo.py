"""Carga la jerarquía de ejemplo del MVP: Festival 2027 → Música → Canción."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion


class Command(BaseCommand):
    help = 'Crea la edición de ejemplo Festival 2027 con sus categorías, votación y opciones.'

    def handle(self, *args, **options):
        ahora = timezone.now()

        edicion, creada = Edicion.objects.get_or_create(
            nombre='Festival 2027',
            anio=2027,
            defaults={'estado': 'ACTIVA'},
        )
        if not creada and edicion.estado != 'ACTIVA':
            edicion.estado = 'ACTIVA'
            edicion.save(update_fields=['estado'])

        categoria, _ = Categoria.objects.get_or_create(
            nombre='Música',
            defaults={'descripcion': 'Categorías musicales del festival.'},
        )

        votacion, _ = Votacion.objects.get_or_create(
            edicion=edicion,
            categoria=categoria,
            nombre='Canción favorita del público',
            defaults={
                'descripcion': 'Elige tu canción preferida del festival.',
                'fecha_apertura': ahora - timedelta(hours=1),
                'fecha_cierre': ahora + timedelta(days=30),
                'estado': 'ACTIVA',
                'mostrar_resultados_en_vivo': True,
            },
        )

        canciones = [
            (1, 'Canción A', 'Artista A'),
            (2, 'Canción B', 'Artista B'),
            (3, 'Canción C', 'Artista C'),
        ]

        for orden, nombre, artista in canciones:
            Opcion.objects.get_or_create(
                votacion=votacion,
                orden=orden,
                defaults={'nombre': nombre, 'subtitulo': artista},
            )

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {edicion} -> {categoria} -> {votacion} con '
            f'{votacion.opciones.count()} opciones.'
        ))
