"""Carga el escenario principal del demo: el Festival de la Leyenda Vallenata.

- 2026 (ACTIVA): la edición protagonista, con cinco categorías abiertas.
- 2025 (FINALIZADA): edición anterior con resultados, para ver el historial.
- 2027 (PROGRAMADA): próxima edición, aún sin candidatos inscritos.

Cada votación lleva su casilla de voto en blanco. Es idempotente: reconoce
lo que ya existe y no lo duplica.
"""

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion

NOMBRE_FESTIVAL = 'Festival de la Leyenda Vallenata'

CATEGORIAS = {
    'Rey Vallenato': 'Competencia por el título de Rey Vallenato de la edición.',
    'Canción Inédita': 'Temas creados especialmente para el festival.',
    'Leyendas del Vallenato': 'Los clásicos que hicieron historia del género.',
    'Piqueria': 'Duelo de versos improvisados entre piqueros.',
    'Rey Infantil': 'Acordeoneros menores de 12 años que llevan la tradición.',
}

EDICIONES = [
    {
        'anio': 2026,
        'estado': 'ACTIVA',
        'votaciones': [
            {
                'categoria': 'Rey Vallenato',
                'nombre': 'Rey Vallenato 2026',
                'descripcion': 'Elige quién se corona como Rey Vallenato de esta edición.',
                'opciones': [
                    (1, 'Silvestre Dangond', 'Candidato A · Academia del Acordeón'),
                    (2, 'Alfredo Gutiérrez', 'Candidato B · Maestro del acordeón'),
                    (3, 'Iván Villazón', 'Candidato C · La voz tradicional'),
                ],
            },
            {
                'categoria': 'Canción Inédita',
                'nombre': 'Canción Inédita del Público',
                'descripcion': '¿Cuál canción inédita merece el premio del festival?',
                'opciones': [
                    (1, 'La Tierra del Presente', 'Autor: Juan Pérez Peña'),
                    (2, 'Travesía por Valledupar', 'Autor: Karla Molina'),
                    (3, 'Alma del Acordeón', 'Autor: Diego Restrepo'),
                ],
            },
            {
                'categoria': 'Leyendas del Vallenato',
                'nombre': 'La Canción de las Leyendas',
                'descripcion': 'Vota por el clásico vallenato que más te gusta.',
                'opciones': [
                    (1, 'La Gota Fría', 'Interpretada por Carlos Vives'),
                    (2, 'El Visitante', 'Interpretada por Diomedes Díaz'),
                    (3, 'Matilde Lina', 'Interpretada por Iván Villazón'),
                ],
            },
            {
                'categoria': 'Piqueria',
                'nombre': 'Rey de la Piqueria 2026',
                'descripcion': '¿Quién improvisó los mejores versos en la tarima?',
                'opciones': [
                    (1, 'Rafael Mendoza Ochoa', 'Piquero de San Juan del Cesar'),
                    (2, 'Wilber Arzuaga Pinto', 'Piquero de La Paz'),
                    (3, 'Hernán Pimienta Gil', 'Piquero de Valledupar'),
                ],
            },
            {
                'categoria': 'Rey Infantil',
                'nombre': 'Rey Vallenato Infantil 2026',
                'descripcion': 'El futuro del acordeón: elige al Rey Infantil.',
                'opciones': [
                    (1, 'Samuel Daza Molina', 'Acordeonero · 11 años'),
                    (2, 'Valentina Oñate Ruiz', 'Acordeonera · 10 años'),
                    (3, 'Juan José Ariza', 'Acordeonero · 12 años'),
                ],
            },
        ],
    },
    {
        'anio': 2025,
        'estado': 'FINALIZADA',
        'votaciones': [
            {
                'categoria': 'Rey Vallenato',
                'nombre': 'Rey Vallenato 2025',
                'descripcion': 'Votación del público de la edición 2025.',
                'opciones': [
                    (1, 'Andrés Felipe Cuello', 'Acordeonero de Fonseca'),
                    (2, 'Luis Carlos Bolaño', 'Acordeonero de Valledupar'),
                    (3, 'Kevin Fragozo Daza', 'Acordeonero de Villanueva'),
                ],
            },
            {
                'categoria': 'Canción Inédita',
                'nombre': 'Canción Inédita 2025',
                'descripcion': 'La canción inédita favorita del público en 2025.',
                'opciones': [
                    (1, 'Sabanas del Cesar', 'Autor: Óscar Maestre'),
                    (2, 'Mi Pedazo de Acordeón', 'Autor: Lina Celedón'),
                    (3, 'Brisas del Guatapurí', 'Autor: Ramiro Quintero'),
                ],
            },
            {
                'categoria': 'Piqueria',
                'nombre': 'Rey de la Piqueria 2025',
                'descripcion': 'El mejor piquero de la edición 2025.',
                'opciones': [
                    (1, 'Efraín Baquero Soto', 'Piquero de Codazzi'),
                    (2, 'Daniel Mejía Ospino', 'Piquero de Riohacha'),
                ],
            },
        ],
    },
    {
        'anio': 2027,
        'estado': 'PROGRAMADA',
        'votaciones': [
            {
                'categoria': 'Rey Vallenato',
                'nombre': 'Rey Vallenato 2027',
                'descripcion': 'Los candidatos se anunciarán al cierre de inscripciones.',
                'opciones': [],
            },
            {
                'categoria': 'Canción Inédita',
                'nombre': 'Canción Inédita 2027',
                'descripcion': 'Recepción de canciones abierta hasta febrero.',
                'opciones': [],
            },
        ],
    },
]


def _fechas(anio, estado, indice, ahora):
    """Fechas de apertura y cierre coherentes con el estado de la edición."""
    if estado == 'ACTIVA':
        # Aperturas escalonadas recientes: la edición en curso más reciente
        # encabeza la pantalla de inicio.
        return ahora - timedelta(minutes=30 - indice * 5), ahora + timedelta(days=30)
    # El festival se celebra a finales de abril en Valledupar.
    apertura = timezone.make_aware(datetime(anio, 4, 26, 9, 0) + timedelta(hours=indice))
    return apertura, apertura + timedelta(days=4)


class Command(BaseCommand):
    help = (
        'Crea el Festival de la Leyenda Vallenata: edición 2026 activa, 2025 '
        'finalizada y 2027 programada, con categorías, votaciones y opciones.'
    )

    def handle(self, *args, **options):
        ahora = timezone.now()

        categorias = {}
        for nombre, descripcion in CATEGORIAS.items():
            categorias[nombre], _ = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion},
            )

        for datos_edicion in EDICIONES:
            estado = datos_edicion['estado']
            edicion, creada = Edicion.objects.get_or_create(
                nombre=NOMBRE_FESTIVAL,
                anio=datos_edicion['anio'],
                defaults={'estado': estado},
            )
            if not creada and edicion.estado != estado:
                edicion.estado = estado
                edicion.save(update_fields=['estado'])

            for indice, datos in enumerate(datos_edicion['votaciones']):
                apertura, cierre = _fechas(edicion.anio, estado, indice, ahora)
                votacion, _ = Votacion.objects.get_or_create(
                    edicion=edicion,
                    categoria=categorias[datos['categoria']],
                    nombre=datos['nombre'],
                    defaults={
                        'descripcion': datos['descripcion'],
                        'fecha_apertura': apertura,
                        'fecha_cierre': cierre,
                        'estado': estado,
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
                if datos['opciones']:
                    Opcion.objects.get_or_create(
                        votacion=votacion,
                        orden=99,
                        defaults={
                            'nombre': 'Voto en blanco',
                            'es_voto_blanco': True,
                            'subtitulo': 'No favorece a ninguna candidatura.',
                        },
                    )

            self.stdout.write(
                f'  {edicion} ({edicion.get_estado_display()}): '
                f'{edicion.votaciones.count()} votaciones'
            )

        self.stdout.write(self.style.SUCCESS('Listo: Festival de la Leyenda Vallenata.'))
