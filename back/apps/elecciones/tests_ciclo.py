"""Ciclo de vida de la edición y reglas en cascada (R1-R5)."""

import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from back.apps.elecciones import ciclo
from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion
from back.apps.usuarios.models import Role, Usuario
from back.apps.votacion.models import ActaEscrutinio, PadronVotante, Voto


def armar_edicion(estado='BORRADOR', inicio=None, fin=None, votaciones=1, opciones=2):
    """Edición con ``votaciones`` votaciones y ``opciones`` opciones válidas cada una."""
    ahora = timezone.now()
    inicio = inicio or ahora + timedelta(days=1)
    fin = fin or ahora + timedelta(days=10)
    edicion = Edicion.objects.create(
        nombre='Festival', anio=2027, estado=estado, fecha_inicio=inicio, fecha_fin=fin
    )
    for indice in range(votaciones):
        votacion = Votacion.objects.create(
            edicion=edicion,
            categoria=Categoria.objects.create(nombre=f'Categoría {indice}'),
            nombre=f'Votación {indice}',
            fecha_apertura=inicio,
            fecha_cierre=fin,
        )
        for orden in range(1, opciones + 1):
            Opcion.objects.create(votacion=votacion, nombre=f'Opción {orden}', orden=orden)
        Opcion.objects.create(votacion=votacion, nombre='Voto en blanco', orden=99, es_voto_blanco=True)
    return edicion


def votar(votacion, numero):
    """Registra un voto válido de un votante nuevo (padrón + urna)."""
    user = get_user_model().objects.create_user(username=f'v{votacion.pk}-{numero}', password='x')
    voto = Voto.objects.create(opcion=votacion.opciones.first())
    PadronVotante.objects.create(
        usuario=user, votacion=votacion, ha_votado=True, hash_comprobante=voto.firma_criptografica
    )
    return voto


class ProgramarTests(TestCase):

    def test_programar_valida_y_deja_las_votaciones_listas(self):
        edicion = armar_edicion()

        ciclo.programar(edicion)

        self.assertEqual(edicion.estado, 'PROGRAMADA')
        self.assertEqual(set(edicion.votaciones.values_list('estado', flat=True)), {'LISTA'})

    def test_sin_categorias_no_se_programa(self):
        edicion = armar_edicion(votaciones=0)

        with self.assertRaises(ciclo.TransicionInvalida) as error:
            ciclo.programar(edicion)

        self.assertTrue(any('al menos una categoría' in e for e in error.exception.errores))
        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'BORRADOR')

    def test_el_voto_en_blanco_no_cuenta_como_opcion_valida(self):
        edicion = armar_edicion(opciones=1)

        with self.assertRaises(ciclo.TransicionInvalida) as error:
            ciclo.programar(edicion)

        self.assertTrue(any('2 opciones válidas' in e for e in error.exception.errores))

    def test_votacion_fuera_del_periodo_no_se_programa(self):
        """R2: las fechas de cada votación dentro del periodo de la edición."""
        edicion = armar_edicion()
        edicion.votaciones.update(fecha_cierre=edicion.fecha_fin + timedelta(days=1))

        with self.assertRaises(ciclo.TransicionInvalida):
            ciclo.programar(edicion)

    def test_fecha_fin_vencida_no_se_programa(self):
        ahora = timezone.now()
        edicion = armar_edicion(inicio=ahora - timedelta(days=5), fin=ahora - timedelta(days=1))

        with self.assertRaises(ciclo.TransicionInvalida):
            ciclo.programar(edicion)

    def test_programar_con_inicio_vencido_activa_de_inmediato(self):
        ahora = timezone.now()
        edicion = armar_edicion(inicio=ahora - timedelta(hours=1), fin=ahora + timedelta(days=1))

        ciclo.programar(edicion)

        self.assertEqual(edicion.estado, 'ACTIVA')
        self.assertEqual(edicion.votaciones.get().estado, 'ABIERTA')

    def test_desprogramar_vuelve_a_borrador(self):
        edicion = armar_edicion()
        ciclo.programar(edicion)

        ciclo.desprogramar(edicion)

        self.assertEqual(edicion.estado, 'BORRADOR')
        self.assertEqual(edicion.votaciones.get().estado, 'BORRADOR')

    def test_desde_activa_no_se_vuelve_atras(self):
        edicion = armar_edicion(estado='ACTIVA')

        with self.assertRaises(ciclo.TransicionInvalida):
            ciclo.desprogramar(edicion)
        with self.assertRaises(ciclo.TransicionInvalida):
            ciclo.programar(edicion)


class AutomaticoPorFechaTests(TestCase):

    def test_programada_se_activa_al_llegar_su_inicio(self):
        edicion = armar_edicion()
        ciclo.programar(edicion)
        momento = edicion.fecha_inicio + timedelta(minutes=1)

        ciclo.sincronizar(momento)

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'ACTIVA')
        self.assertEqual(edicion.votaciones.get().estado, 'ABIERTA')

    def test_borrador_no_se_activa_solo(self):
        """Solo se abre sola una edición PROGRAMADA; la otra queda "no lista"."""
        ahora = timezone.now()
        edicion = armar_edicion(inicio=ahora - timedelta(hours=1))

        ciclo.sincronizar()

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'BORRADOR')
        self.assertTrue(edicion.no_lista)

    def test_votacion_lista_espera_su_propia_apertura(self):
        ahora = timezone.now()
        edicion = armar_edicion(inicio=ahora - timedelta(hours=1), fin=ahora + timedelta(days=5))
        edicion.votaciones.update(fecha_apertura=ahora + timedelta(days=1))
        ciclo.programar(edicion)

        self.assertEqual(edicion.estado, 'ACTIVA')
        votacion = edicion.votaciones.get()
        self.assertEqual(votacion.estado, 'LISTA')

        ciclo.sincronizar(ahora + timedelta(days=1, minutes=1))
        votacion.refresh_from_db()
        self.assertEqual(votacion.estado, 'ABIERTA')

    def test_votacion_se_cierra_sola_en_su_fecha(self):
        ahora = timezone.now()
        edicion = armar_edicion(inicio=ahora - timedelta(hours=1), fin=ahora + timedelta(days=5))
        edicion.votaciones.update(fecha_cierre=ahora + timedelta(days=1))
        ciclo.programar(edicion)

        ciclo.sincronizar(ahora + timedelta(days=1, minutes=1))

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'ACTIVA')
        self.assertEqual(edicion.votaciones.get().estado, 'CERRADA')

    def test_la_edicion_se_cierra_sola_al_llegar_su_fin(self):
        """R3: abiertas → CERRADA; las que nunca se abrieron → CANCELADA."""
        ahora = timezone.now()
        edicion = armar_edicion(
            inicio=ahora - timedelta(hours=1), fin=ahora + timedelta(days=5), votaciones=2
        )
        nunca_abre = edicion.votaciones.order_by('pk').last()
        Votacion.objects.filter(pk=nunca_abre.pk).update(
            fecha_apertura=ahora + timedelta(days=4), fecha_cierre=ahora + timedelta(days=5)
        )
        ciclo.programar(edicion)

        ciclo.sincronizar(edicion.fecha_fin + timedelta(seconds=1))

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'CERRANDO')
        self.assertFalse(edicion.cierre_anticipado)
        estados = dict(edicion.votaciones.values_list('pk', 'estado'))
        self.assertEqual(estados[nunca_abre.pk], 'CANCELADA')
        self.assertIn('CERRADA', estados.values())

    def test_ningun_voto_entra_despues_del_fin_aunque_no_haya_sincronizado(self):
        """El cierre manda: esta_abierta revisa las fechas de la edición."""
        ahora = timezone.now()
        edicion = armar_edicion(estado='ACTIVA', inicio=ahora - timedelta(days=2), fin=ahora - timedelta(minutes=1))
        votacion = edicion.votaciones.get()
        Votacion.objects.filter(pk=votacion.pk).update(
            estado='ABIERTA', fecha_apertura=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=1)
        )
        votacion.refresh_from_db()

        self.assertFalse(votacion.esta_abierta)

    def test_el_middleware_aplica_el_cierre_en_la_primera_peticion(self):
        ahora = timezone.now()
        edicion = armar_edicion(estado='ACTIVA', inicio=ahora - timedelta(days=2), fin=ahora - timedelta(minutes=1))

        self.client.get(reverse('inicio'))

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'FINALIZADA')  # Nada que escrutar: todo cancelado.

    def test_comando_sincronizar_estados(self):
        edicion = armar_edicion()
        ciclo.programar(edicion)
        Edicion.objects.filter(pk=edicion.pk).update(fecha_inicio=timezone.now() - timedelta(minutes=1))
        Votacion.objects.filter(edicion=edicion).update(fecha_apertura=timezone.now() - timedelta(minutes=1))

        call_command('sincronizar_estados', stdout=io.StringIO())

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'ACTIVA')


class CierreYFinalizacionTests(TestCase):

    def _activa(self, votaciones=2):
        ahora = timezone.now()
        edicion = armar_edicion(
            inicio=ahora - timedelta(hours=1), fin=ahora + timedelta(days=5), votaciones=votaciones
        )
        ciclo.programar(edicion)
        return edicion

    def test_cierre_anticipado_exige_motivo(self):
        edicion = self._activa()

        with self.assertRaises(ciclo.TransicionInvalida):
            ciclo.cerrar(edicion, motivo='  ', anticipado=True)

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'ACTIVA')

    def test_cierre_anticipado_queda_registrado(self):
        from back.apps.auditoria.models import LogAuditoriaEvento

        edicion = self._activa()

        ciclo.cerrar(edicion, motivo='Falla eléctrica en la tarima', anticipado=True)

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'CERRANDO')
        self.assertTrue(edicion.cierre_anticipado)
        self.assertEqual(edicion.motivo_cierre, 'Falla eléctrica en la tarima')
        self.assertIsNotNone(edicion.fecha_cierre_real)
        evento = LogAuditoriaEvento.objects.get(accion='edicion_cerrada_anticipadamente')
        self.assertEqual(evento.detalles_json['motivo'], 'Falla eléctrica en la tarima')

    def test_no_se_vota_con_la_edicion_cerrada(self):
        edicion = self._activa()
        votacion = edicion.votaciones.first()
        self.assertTrue(votacion.esta_abierta)

        ciclo.cerrar(edicion, motivo='Suspensión del evento', anticipado=True)

        votacion.refresh_from_db()
        self.assertEqual(votacion.estado, 'CERRADA')
        self.assertFalse(votacion.esta_abierta)

    def test_escrutar_todo_finaliza_la_edicion(self):
        """R4: FINALIZADA cuando cada votación está ESCRUTADA o CANCELADA."""
        edicion = self._activa()
        primera, segunda = edicion.votaciones.order_by('pk')
        votar(primera, 1)
        votar(primera, 2)
        ciclo.cerrar(edicion, motivo='Cierre de prueba', anticipado=True)

        ciclo.escrutar(Votacion.objects.get(pk=primera.pk))
        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'CERRANDO')

        ciclo.escrutar(Votacion.objects.get(pk=segunda.pk))
        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'FINALIZADA')

        acta = ActaEscrutinio.objects.get(votacion=primera)
        self.assertEqual(acta.total_votos_urna, 2)
        self.assertEqual(acta.total_participantes, 2)
        self.assertEqual(acta.hash_sello_bd, ciclo.sello_de_urna(primera))

    def test_escrutar_durante_activa_no_finaliza(self):
        edicion = self._activa(votaciones=1)
        votacion = edicion.votaciones.get()
        ciclo.cerrar_votacion(votacion)

        ciclo.escrutar(votacion)

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'ACTIVA')

    def test_solo_se_escruta_una_votacion_cerrada(self):
        edicion = self._activa(votaciones=1)

        with self.assertRaises(ciclo.TransicionInvalida):
            ciclo.escrutar(edicion.votaciones.get())

    def test_cerrada_no_se_reabre(self):
        edicion = self._activa(votaciones=1)
        votacion = edicion.votaciones.get()
        ciclo.cerrar_votacion(votacion)

        with self.assertRaises(ciclo.TransicionInvalida):
            ciclo.abrir_votacion(votacion)


class PanelCicloTests(TestCase):
    """Las acciones del ciclo desde el panel MVT del organizador."""

    def setUp(self):
        call_command('cargar_permisos', stdout=io.StringIO())
        user = get_user_model().objects.create_user(username='org-ciclo', password='x')
        Usuario.objects.create(
            user=user,
            documento='5500000001',
            nombres='Org',
            apellidos='Ciclo',
            correo='org-ciclo@test.com',
            rol=Role.objects.get(nombre='Organizador'),
        )
        self.client.force_login(user)

    def test_programar_desde_el_panel(self):
        edicion = armar_edicion()

        self.client.post(reverse('gestion:edicion_programar', args=[edicion.id]))

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'PROGRAMADA')

    def test_panel_muestra_lo_que_falta_para_programar(self):
        edicion = armar_edicion(opciones=1)

        respuesta = self.client.get(reverse('gestion:edicion_gestionar', args=[edicion.id]))

        self.assertTrue(respuesta.context['pendientes_programar'])
        self.assertContains(respuesta, 'Le falta para programarse')

    def test_cierre_anticipado_por_formulario(self):
        ahora = timezone.now()
        edicion = armar_edicion(inicio=ahora - timedelta(hours=1))
        ciclo.programar(edicion)
        url = reverse('gestion:edicion_cerrar', args=[edicion.id])

        sin_motivo = self.client.post(url, {'motivo': ''})
        self.assertEqual(sin_motivo.status_code, 200)
        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'ACTIVA')

        self.client.post(url, {'motivo': 'Lluvia torrencial en el parque'})
        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'CERRANDO')

    def test_escrutar_desde_el_panel_finaliza(self):
        ahora = timezone.now()
        edicion = armar_edicion(inicio=ahora - timedelta(hours=1))
        ciclo.programar(edicion)
        ciclo.cerrar(edicion, motivo='Cierre de prueba', anticipado=True)

        self.client.post(reverse('gestion:edicion_escrutar', args=[edicion.id]))

        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'FINALIZADA')


class PadronObligatorioTests(TestCase):

    def test_el_padron_copia_edicion_y_categoria_de_la_votacion(self):
        edicion = armar_edicion()
        votacion = edicion.votaciones.get()
        user = get_user_model().objects.create_user(username='padron', password='x')

        padron = PadronVotante.objects.create(usuario=user, votacion=votacion)

        self.assertEqual(padron.edicion_id, edicion.id)
        self.assertEqual(padron.categoria_id, votacion.categoria_id)
