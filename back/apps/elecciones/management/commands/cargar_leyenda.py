"""Carga el escenario principal del demo: el Festival de la Leyenda Vallenata.

- 2026 (ACTIVA): la edición protagonista, con cinco categorías abiertas.
- 2025 (EN ESCRUTINIO → FINALIZADA): edición anterior. Sus votaciones quedan
  CERRADAS para que la simulación les cargue votos; ``preparar`` las
  escruta después y la edición pasa sola a FINALIZADA, como en la vida real.
- 2027 (PROGRAMADA): próxima edición con sus precandidatos; se programa
  con la validación real de ``elecciones.ciclo``.

Cada votación lleva su casilla de voto en blanco. Es idempotente: reconoce
lo que ya existe y no lo duplica ni le cambia el estado.
"""

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from back.apps.elecciones import ciclo
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
        'estado': 'CERRANDO',
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
                # Preselección abierta al público: los 2 primeros pasan a la
                # gran final, que solo votan los inscritos.
                'categoria': 'Rey Vallenato',
                'nombre': 'Preselección Rey Vallenato 2027',
                'descripcion': 'Vota quién entra a la gran final. Abierta a todo el público.',
                'regla': Votacion.CLASIFICAN_N,
                'clasifican': 2,
                'dias': 2,
                'opciones': [
                    (1, 'Camilo Molina Daza', 'Acordeonero de Valledupar'),
                    (2, 'Rubén Lanao Ariza', 'Acordeonero de Patillal'),
                    (3, 'Hugo Carlos Granados', 'Acordeonero de Mariangola'),
                ],
                'ronda': {
                    'nombre': 'Gran final Rey Vallenato 2027',
                    'descripcion': 'Los 2 finalistas de la preselección. Solo para inscritos.',
                    'modo': Votacion.INSCRITOS,
                },
            },
            {
                'categoria': 'Canción Inédita',
                'nombre': 'Canción Inédita 2027',
                'descripcion': 'Canciones preseleccionadas por el jurado.',
                'opciones': [
                    (1, 'Luna sobre el Guatapurí', 'Autor: Mario Zuleta'),
                    (2, 'El Último Juglar', 'Autora: Rosa Maestre'),
                ],
            },
        ],
    },
]


def _periodo(anio, estado, ahora):
    """Periodo de la edición: en curso para la ACTIVA, finales de abril para el resto."""
    if estado == 'ACTIVA':
        return ahora - timedelta(hours=1), ahora + timedelta(days=30)
    # El festival se celebra a finales de abril en Valledupar.
    inicio = timezone.make_aware(datetime(anio, 4, 26, 8, 0))
    return inicio, inicio + timedelta(days=5)


def _fechas(anio, estado, indice, ahora):
    """Fechas de apertura y cierre dentro del periodo de la edición."""
    inicio, fin = _periodo(anio, estado, ahora)
    if estado == 'ACTIVA':
        # Aperturas escalonadas recientes: la edición en curso más reciente
        # encabeza la pantalla de inicio.
        return ahora - timedelta(minutes=30 - indice * 5), fin
    apertura = inicio + timedelta(hours=1 + indice)
    return apertura, apertura + timedelta(days=4)


# Estado de cada votación según el estado con que se siembra su edición.
ESTADO_VOTACION = {
    'ACTIVA': Votacion.ABIERTA,
    'CERRANDO': Votacion.CERRADA,
    'PROGRAMADA': Votacion.BORRADOR,  # Pasa a LISTA al programar la edición.
}


class Command(BaseCommand):
    help = (
        'Crea el Festival de la Leyenda Vallenata: edición 2026 activa, 2025 '
        'en escrutinio y 2027 programada, con categorías, votaciones y opciones.'
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
            inicio, fin = _periodo(datos_edicion['anio'], estado, ahora)
            # La de 2027 nace en BORRADOR y se programa con la validación real.
            estado_siembra = Edicion.BORRADOR if estado == Edicion.PROGRAMADA else estado
            edicion, creada = Edicion.objects.get_or_create(
                nombre=NOMBRE_FESTIVAL,
                anio=datos_edicion['anio'],
                defaults={'estado': estado_siembra, 'fecha_inicio': inicio, 'fecha_fin': fin},
            )
            if not creada:
                # Ya existe: su estado lo lleva el ciclo de vida, no la semilla.
                self.stdout.write(f'  {edicion} ({edicion.get_estado_display()}): ya existía')
                continue

            for indice, datos in enumerate(datos_edicion['votaciones']):
                apertura, cierre = _fechas(edicion.anio, estado, indice, ahora)
                if 'dias' in datos:
                    cierre = apertura + timedelta(days=datos['dias'])
                votacion, _ = Votacion.objects.get_or_create(
                    edicion=edicion,
                    categoria=categorias[datos['categoria']],
                    nombre=datos['nombre'],
                    defaults={
                        'descripcion': datos['descripcion'],
                        'fecha_apertura': apertura,
                        'fecha_cierre': cierre,
                        'estado': ESTADO_VOTACION[estado],
                        'regla_resultado': datos.get('regla', Votacion.MAYORIA_SIMPLE),
                        'clasifican': datos.get('clasifican', 2),
                    },
                )
                ronda = datos.get('ronda')
                if ronda:
                    # Ronda siguiente: vacía, recibe a los clasificados al escrutar.
                    Votacion.objects.get_or_create(
                        ronda_anterior=votacion,
                        defaults={
                            'edicion': edicion,
                            'categoria': votacion.categoria,
                            'nombre': ronda['nombre'],
                            'descripcion': ronda['descripcion'],
                            'fecha_apertura': cierre + timedelta(hours=2),
                            'fecha_cierre': fin - timedelta(hours=1),
                            'modo_participacion': ronda['modo'],
                            'numero_ronda': votacion.numero_ronda + 1,
                            'estado': Votacion.BORRADOR,
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

            if estado == Edicion.PROGRAMADA:
                ciclo.programar(edicion)
            elif estado == Edicion.CERRANDO:
                edicion.fecha_cierre_real = fin
                edicion.save(update_fields=['fecha_cierre_real'])

            self.stdout.write(
                f'  {edicion} ({edicion.get_estado_display()}): '
                f'{edicion.votaciones.count()} votaciones'
            )

        self.stdout.write(self.style.SUCCESS('Listo: Festival de la Leyenda Vallenata.'))
