"""Modos de participación: votación libre vs. solo inscritos."""

import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from back.apps.auditoria.verificacion import verificar_edicion
from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion
from back.apps.usuarios.models import Role, Usuario
from back.apps.votacion.models import InscripcionEdicion, PadronVotante, Voto


def cuenta(rol, username, documento):
    user = get_user_model().objects.create_user(username=username, password='x')
    Usuario.objects.create(
        user=user, documento=documento, nombres=username, apellidos='Prueba',
        correo=f'{username}@test.com', rol=Role.objects.get(nombre=rol),
    )
    return user


class ModosDeParticipacionTests(TestCase):

    def setUp(self):
        call_command('cargar_permisos', stdout=io.StringIO())
        ahora = timezone.now()
        self.edicion = Edicion.objects.create(
            nombre='Festival', anio=2027, estado='ACTIVA',
            fecha_inicio=ahora - timedelta(days=1), fecha_fin=ahora + timedelta(days=5),
        )
        self.libre = self._votacion('Preselección', 'LIBRE', 'Rey')
        self.cerrada = self._votacion('Final', 'INSCRITOS', 'Canción')
        self.votante = cuenta('Votante', 'votante', '7000000001')

    def _votacion(self, nombre, modo, categoria):
        ahora = timezone.now()
        votacion = Votacion.objects.create(
            edicion=self.edicion, categoria=Categoria.objects.create(nombre=categoria),
            nombre=nombre, estado='ABIERTA', modo_participacion=modo,
            fecha_apertura=ahora - timedelta(hours=1), fecha_cierre=ahora + timedelta(days=1),
        )
        Opcion.objects.create(votacion=votacion, nombre=f'{nombre} A', orden=1)
        Opcion.objects.create(votacion=votacion, nombre=f'{nombre} B', orden=2)
        return votacion

    def _votar(self, votacion):
        self.client.force_login(self.votante)
        return self.client.post(
            reverse('votar', args=[votacion.pk]), {'opcion': votacion.opciones.first().pk}
        )

    def test_en_la_libre_vota_cualquiera(self):
        self._votar(self.libre)

        self.assertEqual(Voto.objects.filter(opcion__votacion=self.libre).count(), 1)

    def test_en_solo_inscritos_no_vota_quien_no_se_inscribio(self):
        self._votar(self.cerrada)

        self.assertFalse(Voto.objects.filter(opcion__votacion=self.cerrada).exists())

    def test_inscribirse_despues_de_la_apertura_no_habilita(self):
        self.client.force_login(self.votante)
        self.client.post(reverse('inscribirse', args=[self.edicion.pk]))
        self.assertTrue(InscripcionEdicion.objects.filter(usuario=self.votante).exists())

        self._votar(self.cerrada)

        self.assertFalse(Voto.objects.filter(opcion__votacion=self.cerrada).exists())

    def test_inscrito_antes_de_la_apertura_vota(self):
        inscripcion = InscripcionEdicion.objects.create(edicion=self.edicion, usuario=self.votante)
        InscripcionEdicion.objects.filter(pk=inscripcion.pk).update(
            fecha_inscripcion=self.cerrada.fecha_apertura - timedelta(days=1)
        )

        self._votar(self.cerrada)

        self.assertEqual(Voto.objects.filter(opcion__votacion=self.cerrada).count(), 1)

    def test_participacion_en_porcentaje_de_inscritos(self):
        for numero in range(4):
            user = cuenta('Votante', f'ins{numero}', f'71000000{numero}')
            inscripcion = InscripcionEdicion.objects.create(edicion=self.edicion, usuario=user)
            InscripcionEdicion.objects.filter(pk=inscripcion.pk).update(
                fecha_inscripcion=self.cerrada.fecha_apertura - timedelta(days=1)
            )
            if numero == 0:
                PadronVotante.objects.create(usuario=user, votacion=self.cerrada, ha_votado=True)

        self.assertEqual(self.cerrada.participacion()['porcentaje'], 25)
        self.assertIsNone(self.libre.participacion())

    def test_el_organizador_inscribe_por_documento(self):
        organizador = cuenta('Organizador', 'org', '7000000002')
        auditor = cuenta('Auditor', 'aud', '7000000003')
        del auditor
        self.client.force_login(organizador)

        respuesta = self.client.post(
            reverse('gestion:inscritos', args=[self.edicion.pk]),
            {'documentos': '7000000001\n9999999999, 7000000003'},
        )

        informe = respuesta.context['informe']
        self.assertEqual(informe['inscritos'], ['7000000001'])
        self.assertEqual(informe['sin_cuenta'], ['9999999999'])
        self.assertEqual(informe['no_votantes'], ['7000000003'])
        inscripcion = InscripcionEdicion.objects.get(usuario=self.votante)
        self.assertEqual(inscripcion.origen, 'ORGANIZADOR')

    def test_el_auditor_detecta_votos_de_no_inscritos(self):
        PadronVotante.objects.create(usuario=self.votante, votacion=self.cerrada, ha_votado=True)

        tipos = {h['tipo'] for h in verificar_edicion(self.edicion)}

        self.assertIn('NO_INSCRITO', tipos)


class RegistroDelAuditorTests(TestCase):
    """El auditor ve las acciones de gestión, no la actividad de cada votante."""

    def setUp(self):
        from back.apps.auditoria.servicio import registrar_evento

        call_command('cargar_permisos', stdout=io.StringIO())
        self.votante = cuenta('Votante', 'votante-log', '7200000001')
        self.organizador = cuenta('Organizador', 'org-log', '7200000002')
        self.auditor = cuenta('Auditor', 'aud-log', '7200000003')

        class Peticion:
            META = {}

            def __init__(self, user):
                self.user = user

        registrar_evento(Peticion(self.votante), 'usuarios', 'login')
        registrar_evento(Peticion(self.organizador), 'ediciones', 'edicion_programada')
        registrar_evento(None, 'usuarios', 'login_fallido')

    def test_el_auditor_no_ve_las_acciones_de_los_votantes(self):
        self.client.force_login(self.auditor)

        eventos = list(self.client.get(reverse('auditoria_lista')).context['eventos'])

        acciones = {e.accion for e in eventos}
        self.assertIn('edicion_programada', acciones)
        self.assertIn('login_fallido', acciones)
        self.assertNotIn(self.votante.pk, {e.usuario_id for e in eventos})
