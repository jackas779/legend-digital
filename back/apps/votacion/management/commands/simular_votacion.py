"""Datos de votación simulados: votantes de demo y votos emitidos.

Sirve para ver el sistema con vida: padrón con participantes y pendientes,
resultados con porcentajes, comprobantes y auditoría. Es idempotente: los
votantes se reconocen por su documento y nadie vota dos veces.
"""

from collections import defaultdict

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from back.apps.auditoria.servicio import registrar_evento
from back.apps.elecciones.models import Votacion
from back.apps.usuarios.models import Role, Usuario
from back.apps.votacion.models import PadronVotante, Voto

CLAVE_DEMO = 'voto123'

NOMBRES = [
    'María José', 'Andrés', 'Daniela', 'Carlos', 'Valentina', 'Jorge', 'Camila',
    'Luis Fernando', 'Natalia', 'Sebastián', 'Laura', 'Miguel Ángel', 'Paola',
    'Juan David', 'Mariana', 'Alejandro', 'Diana', 'Santiago', 'Isabella', 'Felipe',
    'Yulieth', 'Óscar', 'Karen', 'Esteban', 'Leidy', 'Jhon Jairo', 'Angélica',
    'Ricardo', 'Melissa', 'Cristian',
]
APELLIDOS = [
    'Oñate', 'Daza', 'Gutiérrez', 'Maestre', 'Zuleta', 'Romero', 'Castro',
    'Mendoza', 'Pimienta', 'Araújo', 'Molina', 'Quintero', 'Celedón', 'Ariza',
    'Fragozo', 'Cuello', 'Baquero', 'Bolaño', 'Mejía', 'Ospino', 'Pinto',
    'Restrepo', 'Martínez', 'Durán', 'Villazón', 'Herrera', 'Peralta',
]


def nombre_votante(numero):
    """Nombre y dos apellidos colombianos, fijos para cada número de votante."""
    nombres = NOMBRES[(numero * 7) % len(NOMBRES)]
    primero = APELLIDOS[(numero * 11) % len(APELLIDOS)]
    segundo = APELLIDOS[(numero * 5 + 3) % len(APELLIDOS)]
    if segundo == primero:
        segundo = APELLIDOS[(numero * 5 + 4) % len(APELLIDOS)]
    return nombres, f'{primero} {segundo}'


def pesos_opciones(opciones, semilla):
    """Peso de cada opción para el reparto simulado: distinto en cada
    votación y con el voto en blanco siempre minoritario."""
    pesos = []
    for indice, opcion in enumerate(opciones):
        if opcion.es_voto_blanco:
            pesos.append(4)
        else:
            pesos.append(12 + (semilla * 31 + indice * 17) % 45)
    return pesos


def emitir_voto(user, opcion):
    """Emite el voto de ``user`` por ``opcion`` y marca su padrón.

    Devuelve True si emitió un voto nuevo y False si ya había votado o si la
    regla de un voto por categoría lo impide.
    """
    votacion = opcion.votacion
    try:
        with transaction.atomic():
            padron, _ = PadronVotante.objects.get_or_create(
                usuario=user,
                votacion=votacion,
                defaults={
                    'edicion': votacion.edicion,
                    'categoria': votacion.categoria,
                },
            )
            if padron.ha_votado:
                return False
            voto = Voto.objects.create(opcion=opcion)
            padron.ha_votado = True
            padron.hash_comprobante = voto.firma_criptografica
            padron.save(update_fields=['ha_votado', 'hash_comprobante'])
    except Exception:
        return False  # No interrumpe la carga por un usuario puntual.
    return True

# Reparto realista: 45 / 33 / 22 sobre el total de votantes.
PESOS = (45, 33, 22)


class Command(BaseCommand):
    help = (
        'Crea votantes de demo (por defecto 40) y emite votos simulados en '
        'la votación activa para poblar el padrón, resultados y auditoría.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--votantes',
            type=int,
            default=40,
            help='Cantidad de votantes de demo (por defecto 40).',
        )
        parser.add_argument(
            '--votacion',
            type=int,
            default=None,
            help='Id de la votación; por defecto se usa la primera ACTIVA.',
        )
        parser.add_argument(
            '--participacion',
            type=int,
            default=80,
            help='Porcentaje de votantes que emiten voto (por defecto 80).',
        )
        parser.add_argument(
            '--todas',
            action='store_true',
            help=(
                'Simula en todas las votaciones ACTIVAS. Si una categoría tiene '
                'varias votaciones en la edición, reparte a los votantes entre '
                'ellas (un voto por categoría).'
            ),
        )

    def handle(self, *args, **options):
        total_votantes = max(0, options['votantes'])
        participacion = min(100, max(0, options['participacion']))

        if options['todas']:
            return self._simular_todas(total_votantes, participacion)

        votacion = self._obtener_votacion(options['votacion'])
        if votacion is None:
            raise CommandError(
                'No hay votaciones ACTIVAS para simular; ejecuta '
                'cargar_demo primero (python manage.py preparar).'
            )

        opciones = list(votacion.opciones.order_by('orden', 'nombre'))
        if not opciones:
            raise CommandError(
                f'La votación «{votacion}» no tiene opciones; no se puede simular.'
            )

        rol_votante, _ = Role.objects.get_or_create(
            nombre='Votante',
            defaults={'descripcion': 'Usuario común: elige una opción y vota'},
        )

        nuevos, votantes = self._crear_votantes(total_votantes, rol_votante)
        votos_nuevos, conteo = self._emitir_votos(
            votacion, votantes, opciones, participacion
        )

        total_urna = votacion.total_votos
        self.stdout.write(self.style.SUCCESS(
            f'Votantes de demo: {len(votantes)} ({nuevos} nuevos). '
            f'Votos simulados: {votos_nuevos} nuevos; total en la urna: {total_urna}.'
        ))
        for opcion in opciones:
            self.stdout.write(
                f"  {opcion.nombre}: {conteo.get(opcion.id, 0)} voto(s)"
            )
        self.stdout.write('')
        self.stdout.write('Clave de los votantes de demo: voto123')
        self.stdout.write('Para repetir la demo sin borrar cuentas:')
        self.stdout.write('  python manage.py reset_demo --confirmar')

        registrar_evento(
            modulo='votacion',
            accion='votos_simulados',
            detalles={
                'votacion': votacion.id,
                'votantes_demo': len(votantes),
                'votos_nuevos': votos_nuevos,
            },
        )

    def _simular_todas(self, total_votantes, participacion):
        """Simula en cada votación activa respetando un voto por categoría."""
        # También las FINALIZADAS: así las ediciones anteriores tienen resultados.
        votaciones = list(
            Votacion.objects.filter(estado__in=['ACTIVA', 'FINALIZADA'])
            .select_related('edicion', 'categoria')
            .order_by('edicion_id', 'categoria_id', 'id')
        )
        if not votaciones:
            raise CommandError(
                'No hay votaciones ACTIVAS para simular; ejecuta '
                'python manage.py preparar.'
            )

        rol_votante, _ = Role.objects.get_or_create(
            nombre='Votante',
            defaults={'descripcion': 'Usuario común: elige una opción y vota'},
        )
        nuevos, votantes = self._crear_votantes(total_votantes, rol_votante)

        grupos = defaultdict(list)
        for votacion in votaciones:
            grupos[(votacion.edicion_id, votacion.categoria_id)].append(votacion)

        total_nuevos = 0
        for (edicion_id, categoria_id), lista in grupos.items():
            for posicion, votacion in enumerate(lista):
                opciones = list(votacion.opciones.order_by('orden', 'nombre'))
                if not opciones:
                    continue
                # Quien ya está en el padrón de otra votación de la misma
                # categoría no puede entrar en esta (regla de unicidad).
                ocupados = set(
                    PadronVotante.objects.filter(
                        edicion_id=edicion_id, categoria_id=categoria_id
                    )
                    .exclude(votacion=votacion)
                    .values_list('usuario_id', flat=True)
                )
                asignados = [
                    user for numero, user in enumerate(votantes)
                    if numero % len(lista) == posicion and user.id not in ocupados
                ]
                # Participación distinta en cada votación (entre 55 % y el
                # valor pedido) para que los números se vean reales.
                participacion_votacion = max(
                    min(participacion, 55), participacion - (votacion.id * 7) % 26
                )
                votos_nuevos, _ = self._emitir_votos(
                    votacion,
                    asignados,
                    opciones,
                    participacion_votacion,
                    semilla=votacion.id,
                    pesos=pesos_opciones(opciones, votacion.id),
                )
                total_nuevos += votos_nuevos
                self.stdout.write(
                    f'  {votacion.titulo}: {votacion.total_votos} voto(s) en la urna'
                )

        self.stdout.write(self.style.SUCCESS(
            f'Votantes de demo: {len(votantes)} ({nuevos} nuevos). '
            f'Votos simulados nuevos: {total_nuevos} en {len(votaciones)} votaciones.'
        ))
        registrar_evento(
            modulo='votacion',
            accion='votos_simulados',
            detalles={
                'votaciones': len(votaciones),
                'votantes_demo': len(votantes),
                'votos_nuevos': total_nuevos,
            },
        )

    def _obtener_votacion(self, id_votacion):
        if id_votacion:
            return Votacion.objects.filter(pk=id_votacion).first()
        return (
            Votacion.objects
            .filter(estado='ACTIVA')
            .order_by('id')
            .first()
        )

    def _crear_votantes(self, total, rol_votante):
        """Crea los votantes de demo que falten; reconoce los existentes."""
        User = get_user_model()
        creados = 0
        votantes = []

        # Se calcula el hash una sola vez: todas las cuentas comparten clave
        # y así la carga de muchos votantes no tarda minutos.
        clave = make_password(CLAVE_DEMO)

        for numero in range(1, total + 1):
            documento = f'90{numero:08d}'
            correo = f'votante{numero:02d}@demo.uni.edu.co'
            nombres, apellidos = nombre_votante(numero)

            perfil = (
                Usuario.objects
                .select_related('user')
                .filter(documento=documento)
                .first()
            )
            if perfil is not None and perfil.nombres == 'Votante de demo':
                # Cuentas de versiones anteriores: reciben un nombre realista.
                perfil.nombres, perfil.apellidos = nombres, apellidos
                perfil.save(update_fields=['nombres', 'apellidos'])
                User.objects.filter(pk=perfil.user_id).update(
                    first_name=nombres, last_name=apellidos
                )
            if perfil is None:
                user = User(
                    username=f'votante.demo.{numero:02d}',
                    email=correo,
                    password=clave,
                    first_name=nombres,
                    last_name=apellidos,
                )
                user.save()
                Usuario.objects.create(
                    user=user,
                    documento=documento,
                    nombres=nombres,
                    apellidos=apellidos,
                    correo=correo,
                    rol=rol_votante,
                    estado='ACTIVO',
                )
                creados += 1
                votantes.append(user)
            else:
                votantes.append(perfil.user)

        votantes = [v for v in votantes if v.is_active]
        return creados, votantes

    def _emitir_votos(self, votacion, votantes, opciones, participacion, semilla=0, pesos=None):
        """Habilita a todos en el padrón y emite los votos que falten
        hasta llegar a la participación pedida.

        ``pesos`` (uno por opción) define el reparto; sin él se usa PESOS."""
        for user in votantes:
            PadronVotante.objects.get_or_create(
                usuario=user,
                votacion=votacion,
                defaults={'edicion': votacion.edicion, 'categoria': votacion.categoria},
            )

        ya_votaron = PadronVotante.objects.filter(
            votacion=votacion, ha_votado=True
        ).count()
        objetivo = round(len(votantes) * participacion / 100)
        pendientes = max(0, objetivo - ya_votaron)

        acumulados = []
        suma = 0
        if pesos:
            # Cortes acumulados sobre 100 a partir de los pesos dados.
            total_pesos = sum(pesos)
            for peso in pesos[:-1]:
                suma += peso
                acumulados.append(round(suma * 100 / total_pesos))
        else:
            for peso in PESOS[:len(opciones) - 1] if len(opciones) > 1 else ():
                suma += peso
                acumulados.append(suma)

        emitidos = 0
        conteo = {}
        for numero, user in enumerate(votantes):
            if emitidos >= pendientes:
                break
            # La semilla cambia el reparto entre votaciones para que cada
            # una tenga resultados distintos.
            posicion = (numero * 37 + 11 + semilla * 23) % 100
            indice = 0
            for corte in acumulados:
                if posicion >= corte:
                    indice += 1
            opcion = opciones[indice] if indice < len(opciones) else opciones[-1]

            if not emitir_voto(user, opcion):
                continue

            emitidos += 1
            conteo[opcion.id] = conteo.get(opcion.id, 0) + 1

        return emitidos, conteo
