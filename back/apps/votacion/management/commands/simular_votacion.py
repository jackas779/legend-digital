"""Datos de votación simulados: votantes de demo y votos emitidos.

Sirve para ver el sistema con vida: padrón con participantes y pendientes,
resultados con porcentajes, comprobantes y auditoría. Es idempotente: los
votantes se reconocen por su documento y nadie vota dos veces.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from back.apps.auditoria.servicio import registrar_evento
from back.apps.elecciones.models import Votacion
from back.apps.usuarios.models import Role, Usuario
from back.apps.votacion.models import PadronVotante, Voto

CLAVE_DEMO = 'voto123'

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

    def handle(self, *args, **options):
        total_votantes = max(0, options['votantes'])
        participacion = min(100, max(0, options['participacion']))

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

        for numero in range(1, total + 1):
            documento = f'90{numero:08d}'
            correo = f'votante{numero:02d}@demo.uni.edu.co'
            nombres = 'Votante de demo'
            apellidos = f'Número {numero:02d}'

            perfil = (
                Usuario.objects
                .select_related('user')
                .filter(documento=documento)
                .first()
            )
            if perfil is None:
                user = User.objects.create_user(
                    username=f'votante.demo.{numero:02d}',
                    email=correo,
                    password=CLAVE_DEMO,
                    first_name=nombres,
                    last_name=apellidos,
                )
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

    def _emitir_votos(self, votacion, votantes, opciones, participacion):
        """Habilita a todos en el padrón y emite los votos que falten
        hasta llegar a la participación pedida."""
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
        for peso in PESOS[:len(opciones) - 1] if len(opciones) > 1 else ():
            suma += peso
            acumulados.append(suma)

        emitidos = 0
        conteo = {}
        for numero, user in enumerate(votantes):
            if emitidos >= pendientes:
                break
            posicion = (numero * 37 + 11) % 100
            indice = 0
            for corte in acumulados:
                if posicion >= corte:
                    indice += 1
            opcion = opciones[indice] if indice < len(opciones) else opciones[-1]

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
                        continue
                    voto = Voto.objects.create(opcion=opcion)
                    padron.ha_votado = True
                    padron.hash_comprobante = voto.firma_criptografica
                    padron.save(update_fields=['ha_votado', 'hash_comprobante'])
            except Exception:
                continue  # No interrumpe la simulación por un usuario puntual.

            emitidos += 1
            conteo[opcion.id] = conteo.get(opcion.id, 0) + 1

        return emitidos, conteo
