"""Panel del auditor: verificación automática y flujo de discrepancias."""

import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from back.apps.auditoria.models import Discrepancia
from back.apps.auditoria.verificacion import verificar_edicion
from back.apps.elecciones import ciclo
from back.apps.elecciones.tests_ciclo import armar_edicion, votar
from back.apps.usuarios.models import Permission, Role, RolPermiso, Usuario
from back.apps.votacion.models import Voto


def cuenta(nombre_rol, username):
    user = get_user_model().objects.create_user(username=username, password='x')
    Usuario.objects.create(
        user=user,
        documento=f'44{user.pk:08d}',
        nombres=nombre_rol,
        apellidos='Prueba',
        correo=f'{username}@test.com',
        rol=Role.objects.get(nombre=nombre_rol),
    )
    return user


class VerificacionAutomaticaTests(TestCase):

    def setUp(self):
        ahora = timezone.now()
        self.edicion = armar_edicion(inicio=ahora - timedelta(hours=1))
        ciclo.programar(self.edicion)
        self.votacion = self.edicion.votaciones.get()

    def _tipos(self):
        return {h['tipo'] for h in verificar_edicion(self.edicion)}

    def test_todo_en_orden_no_da_hallazgos(self):
        votar(self.votacion, 1)

        self.assertEqual(verificar_edicion(self.edicion), [])

    def test_voto_sin_participante_en_padron(self):
        Voto.objects.create(opcion=self.votacion.opciones.first())

        self.assertIn('PADRON_URNA', self._tipos())

    def test_firma_alterada(self):
        voto = votar(self.votacion, 1)
        Voto.objects.filter(pk=voto.pk).update(firma_criptografica='0' * 64)

        self.assertIn('FIRMA_INVALIDA', self._tipos())

    def test_voto_fuera_de_horario(self):
        voto = votar(self.votacion, 1)
        fuera = self.votacion.fecha_cierre + timedelta(hours=1)
        Voto.objects.filter(pk=voto.pk).update(fecha_registro=fuera)

        self.assertIn('VOTO_FUERA_DE_HORARIO', self._tipos())

    def test_voto_agregado_despues_del_acta(self):
        votar(self.votacion, 1)
        ciclo.cerrar(self.edicion, motivo='Cierre de prueba', anticipado=True)
        ciclo.escrutar_edicion(self.edicion)
        votar(self.votacion, 2)

        self.assertIn('ACTA_DESCUADRADA', self._tipos())

    def test_votacion_abierta_con_edicion_cerrada(self):
        ciclo.cerrar(self.edicion, motivo='Cierre de prueba', anticipado=True)
        type(self.votacion).objects.filter(pk=self.votacion.pk).update(estado='ABIERTA')

        self.assertIn('ABIERTA_CON_EDICION_CERRADA', self._tipos())


class FlujoDiscrepanciasTests(TestCase):

    def setUp(self):
        call_command('cargar_permisos', stdout=io.StringIO())
        self.auditor = cuenta('Auditor', 'auditor-d')
        self.organizador = cuenta('Organizador', 'organizador-d')
        self.administrador = cuenta('Administrador', 'admin-d')
        self.edicion = armar_edicion(estado='ACTIVA')

    def _reportar(self):
        self.client.force_login(self.auditor)
        self.client.post(
            reverse('auditoria_reportar', args=[self.edicion.id]),
            {'tipo': 'OTRA', 'descripcion': 'El conteo de la mesa 3 no cuadra.'},
        )
        self.client.logout()
        return Discrepancia.objects.get()

    def _accion(self, user, discrepancia, accion, texto=''):
        self.client.force_login(user)
        respuesta = self.client.post(
            reverse('auditoria_discrepancia_accion', args=[discrepancia.id, accion]),
            {'texto': texto},
        )
        self.client.logout()
        discrepancia.refresh_from_db()
        return respuesta

    def test_el_auditor_registra_pero_no_resuelve(self):
        discrepancia = self._reportar()
        self.assertEqual(discrepancia.estado, 'ABIERTA')
        self.assertEqual(discrepancia.reportada_por, self.auditor)

        self._accion(self.auditor, discrepancia, 'resolver', 'Lo resuelvo yo mismo.')

        self.assertEqual(discrepancia.estado, 'ABIERTA')

    def test_el_organizador_resuelve_y_el_auditor_confirma(self):
        discrepancia = self._reportar()

        self._accion(self.organizador, discrepancia, 'resolver', 'Se recontó la mesa 3 y cuadra.')
        self.assertEqual(discrepancia.estado, 'RESUELTA')
        self.assertEqual(discrepancia.resuelta_por, self.organizador)

        self._accion(self.auditor, discrepancia, 'confirmar')
        self.assertEqual(discrepancia.confirmada_por, self.auditor)

    def test_resolver_exige_explicacion(self):
        discrepancia = self._reportar()

        self._accion(self.organizador, discrepancia, 'resolver', 'ok')

        self.assertEqual(discrepancia.estado, 'ABIERTA')

    def test_descartar_como_falso_positivo(self):
        discrepancia = self._reportar()

        self._accion(self.organizador, discrepancia, 'descartar', 'Era un error de digitación del acta.')

        self.assertEqual(discrepancia.estado, 'DESCARTADA')

    def test_el_auditor_reabre(self):
        discrepancia = self._reportar()
        self._accion(self.organizador, discrepancia, 'resolver', 'Se recontó la mesa 3 y cuadra.')

        self._accion(self.auditor, discrepancia, 'reabrir', 'El recuento no incluyó los votos en blanco.')

        self.assertEqual(discrepancia.estado, 'ABIERTA')
        self.assertEqual(discrepancia.veces_reabierta, 1)

    def test_sin_permiso_del_organizador_pasa_al_administrador(self):
        from back.apps.auditoria.discrepancias import responsable_actual

        self.assertEqual(responsable_actual(), 'Organizador')
        RolPermiso.objects.filter(
            rol__nombre='Organizador',
            permiso=Permission.objects.get(codigo='discrepancias.resolver'),
        ).delete()
        self.assertEqual(responsable_actual(), 'Administrador')

        discrepancia = self._reportar()
        self._accion(self.organizador, discrepancia, 'resolver', 'Intento sin permiso suficiente.')
        self.assertEqual(discrepancia.estado, 'ABIERTA')

        self._accion(self.administrador, discrepancia, 'resolver', 'Revisado por el administrador.')
        self.assertEqual(discrepancia.estado, 'RESUELTA')

    def test_discrepancia_abierta_no_bloquea_la_finalizacion(self):
        discrepancia = self._reportar()

        ciclo.cerrar(self.edicion, motivo='Cierre de prueba', anticipado=True)

        self.edicion.refresh_from_db()
        self.assertEqual(self.edicion.estado, 'FINALIZADA')  # Nada que escrutar.
        self.assertTrue(discrepancia.esta_abierta)
        self.assertTrue(self.edicion.finalizada_con_pendientes)

    def test_el_auditor_confirma_que_la_edicion_esta_en_orden(self):
        self.client.force_login(self.auditor)

        self.client.post(
            reverse('auditoria_confirmar_edicion', args=[self.edicion.id]),
            {'observacion': 'Revisión de mitad de jornada.'},
        )

        confirmacion = self.edicion.confirmaciones.get()
        self.assertEqual(confirmacion.estado_edicion, 'ACTIVA')
        self.assertEqual(confirmacion.auditor, self.auditor)

    def test_el_votante_no_ve_el_panel(self):
        votante = cuenta('Votante', 'votante-d')
        self.client.force_login(votante)

        respuesta = self.client.get(reverse('discrepancias'))

        self.assertEqual(respuesta.status_code, 403)

    def test_pantallas_responden(self):
        discrepancia = self._reportar()
        self.client.force_login(self.auditor)

        for url in (
            reverse('auditoria_ediciones'),
            reverse('auditoria_edicion', args=[self.edicion.id]),
            reverse('discrepancias'),
            reverse('auditoria_discrepancia', args=[discrepancia.id]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
