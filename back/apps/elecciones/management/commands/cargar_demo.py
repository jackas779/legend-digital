"""Carga la edición de ejemplo del MVP: Festival 2027.

Música tiene dos votaciones (para ver la regla de un voto por categoría) y
Deportes una. Es idempotente: reconoce lo que ya existe y no lo duplica.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion

CATEGORIAS = {
    'Música': 'Categorías musicales del festival.',
    'Deportes': 'Competencias y equipos representativos.',
}

VOTACIONES = [
    {
        'categoria': 'Música',
        'nombre': 'Canción favorita del público',
        'descripcion': 'Elige tu canción preferida del festival.',
        'opciones': [
            (1, 'Canción A', 'Artista A'),
            (2, 'Canción B', 'Artista B'),
            (3, 'Canción C', 'Artista C'),
        ],
    },
    {
        'categoria': 'Música',
        'nombre': 'Mejor artista del público',
        'descripcion': (
            'Segunda votación de la categoría Música en una edición: '
            'comprueba la regla de un voto por categoría.'
        ),
        'opciones': [
            (1, 'Artista Aurora', 'Candidato 1'),
            (2, 'Banda Sol', 'Candidato 2'),
            (3, 'Nucla Rá', 'Candidato 3'),
        ],
    },
    {
        'categoria': 'Deportes',
        'nombre': 'Mejor equipo representativo',
        'descripcion': None,
        'opciones': [
            (1, 'Equipo Ámbar', None),
            (2, 'Equipo Cobalto', None),
        ],
    },
]


class Command(BaseCommand):
    help = (
        'Crea la edición de ejemplo Festival 2027 con sus categorías '
        '(Música y Deportes), votaciones y opciones.'
    )

    def handle(self, *args, **options):
        ahora = timezone.now()
        fin = ahora + timedelta(days=30)

        edicion, creada = Edicion.objects.get_or_create(
            nombre='Festival 2027',
            anio=2027,
            defaults={
                'estado': Edicion.ACTIVA,
                'fecha_inicio': ahora - timedelta(hours=2),
                'fecha_fin': fin,
            },
        )
        if not creada:
            # Su estado lo lleva el ciclo de vida (pudo cerrarse sola al
            # llegar su fecha de fin); la semilla no lo revive.
            self.stdout.write(
                f'Listo: {edicion} ya existía ({edicion.get_estado_display()}).'
            )
            return

        categorias = {}
        for nombre, descripcion in CATEGORIAS.items():
            categorias[nombre], _ = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion},
            )

        for datos in VOTACIONES:
            votacion, _ = Votacion.objects.get_or_create(
                edicion=edicion,
                categoria=categorias[datos['categoria']],
                nombre=datos['nombre'],
                defaults={
                    'descripcion': datos['descripcion'],
                    'fecha_apertura': ahora - timedelta(hours=1),
                    'fecha_cierre': fin,
                    'estado': Votacion.ABIERTA,
                },
            )

            for orden, nombre, subtitulo in datos['opciones']:
                Opcion.objects.get_or_create(
                    votacion=votacion,
                    orden=orden,
                    defaults={'nombre': nombre, 'subtitulo': subtitulo},
                )

            self.stdout.write(f'  {edicion} -> {votacion.categoria} -> {votacion}')

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {edicion} con {edicion.votaciones.count()} votaciones.'
        ))
