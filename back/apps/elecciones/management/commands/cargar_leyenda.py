"""Carga la edición demo del Festival de la Leyenda Vallenata.

Crea la edición con tres categorías (Rey Vallenato, Canción Inédita y
Leyendas del Vallenato), cada una con su votación activa, opciones y un
voto en blanco, para probar el flujo completo: inicio → edición → tarjetón.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion

CATEGORIAS = [
    {
        'categoria': ('Rey Vallenato', 'Competencia por el título de Rey Vallenato de la edición.'),
        'votacion': (
            'Rey Vallenato 2026',
            'Elige quién se corona como Rey Vallenato de esta edición.',
        ),
        'opciones': [
            (1, 'Silvestre Dangond', 'Candidato A · Academia del Acordeón'),
            (2, 'Alfredo Gutiérrez', 'Candidato B · Maestro del acordeón'),
            (3, 'Iván Villazón', 'Candidato C · La voz tradicional'),
        ],
    },
    {
        'categoria': ('Canción Inédita', 'Temas creados especialmente para el festival.'),
        'votacion': (
            'Canción Inédita del Público',
            '¿Cuál canción inédita merece el premio del festival?',
        ),
        'opciones': [
            (1, 'La Tierra del Presente', 'Autor: Juan Pérez Peña'),
            (2, 'Travesía por Valledupar', 'Autor: Karla Molina'),
            (3, 'Alma del Acordeón', 'Autor: Diego Restrepo'),
        ],
    },
    {
        'categoria': ('Leyendas del Vallenato', 'Los clásicos que hicieron historia del género.'),
        'votacion': (
            'La Canción de las Leyendas',
            'Vota por el clásico vallenato que más te gusta.',
        ),
        'opciones': [
            (1, 'La Gota Fría', 'Interpretada por Carlos Vives'),
            (2, 'El Visitante', 'Interpretada por Diomedes Díaz'),
            (3, 'Matilde Lina', 'Interpretada por Iván Villazón'),
        ],
    },
]


class Command(BaseCommand):
    help = (
        'Crea la edición demo Festival de la Leyenda Vallenata 2026 con sus '
        'categorías, votaciones activas y opciones (incluye voto en blanco).'
    )

    def handle(self, *args, **options):
        ahora = timezone.now()

        edicion, creada = Edicion.objects.get_or_create(
            nombre='Festival de la Leyenda Vallenata',
            anio=2026,
            defaults={'estado': 'ACTIVA'},
        )
        if not creada and edicion.estado != 'ACTIVA':
            edicion.estado = 'ACTIVA'
            edicion.save(update_fields=['estado'])

        for indice, datos in enumerate(CATEGORIAS):
            nombre_cat, desc_cat = datos['categoria']
            categoria, _ = Categoria.objects.get_or_create(
                nombre=nombre_cat,
                defaults={'descripcion': desc_cat},
            )

            nombre_vot, desc_vot = datos['votacion']
            votacion, _ = Votacion.objects.get_or_create(
                edicion=edicion,
                categoria=categoria,
                nombre=nombre_vot,
                defaults={
                    'descripcion': desc_vot,
                    # Aperturas escalonadas (la primera abrió hace 30 min) para
                    # que esta edición gane el orden "proceso más reciente".
                    'fecha_apertura': ahora - timedelta(minutes=30 - indice * 5),
                    'fecha_cierre': ahora + timedelta(days=30),
                    'estado': 'ACTIVA',
                    'mostrar_resultados_en_vivo': True,
                },
            )

            for orden, nombre_op, subtitulo in datos['opciones']:
                Opcion.objects.get_or_create(
                    votacion=votacion,
                    orden=orden,
                    defaults={'nombre': nombre_op, 'subtitulo': subtitulo},
                )

            # Casilla de voto en blanco al final del tarjetón.
            Opcion.objects.get_or_create(
                votacion=votacion,
                orden=99,
                defaults={
                    'nombre': 'Voto en blanco',
                    'es_voto_blanco': True,
                    'subtitulo': 'No favorece a ninguna candidatura.',
                },
            )

            self.stdout.write(f'  {edicion} -> {categoria} -> {votacion}')

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {edicion} con {edicion.votaciones.count()} votaciones activas.'
        ))
