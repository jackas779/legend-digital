"""Rondas y reglas de resultado: clasificatoria, 50 % + 1, repetición y empates."""

import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from back.apps.elecciones import ciclo
from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion
from back.apps.usuarios.models import Role, Usuario
from back.apps.votacion.models import PadronVotante, Voto

import tempfile

MEDIA_TEMPORAL = tempfile.mkdtemp(prefix='media-tests-')


def votos(opcion, cantidad):
    for _ in range(cantidad):
        Voto.objects.create(opcion=opcion)


class Escenario:
    """Edición activa con una votación (ronda 1) y su ronda siguiente configurada."""

    def armar(self, regla, candidatos=3, clasifican=2, repetir=False, con_siguiente=True):
        ahora = timezone.now()
        self.edicion = Edicion.objects.create(
            nombre='Festival', anio=2027, estado='BORRADOR',
            fecha_inicio=ahora - timedelta(hours=1), fecha_fin=ahora + timedelta(days=10),
        )
        categoria = Categoria.objects.create(nombre='Rey Vallenato')
        self.ronda1 = Votacion.objects.create(
            edicion=self.edicion, categoria=categoria, nombre='Primera vuelta',
            fecha_apertura=ahora - timedelta(minutes=30), fecha_cierre=ahora + timedelta(days=2),
            regla_resultado=regla, clasifican=clasifican, repetir_si_gana_blanco=repetir,
        )
        self.opciones = [
            Opcion.objects.create(votacion=self.ronda1, nombre=f'Candidato {i}', orden=i)
            for i in range(1, candidatos + 1)
        ]
        self.blanco = Opcion.objects.create(
            votacion=self.ronda1, nombre='Voto en blanco', orden=99, es_voto_blanco=True
        )
        self.ronda2 = None
        if con_siguiente:
            self.ronda2 = Votacion.objects.create(
                edicion=self.edicion, categoria=categoria, nombre='Segunda ronda',
                fecha_apertura=ahora + timedelta(days=3), fecha_cierre=ahora + timedelta(days=5),
                ronda_anterior=self.ronda1, numero_ronda=2,
            )
        ciclo.programar(self.edicion)
        self.ronda1.refresh_from_db()
        return self

    def cerrar_ronda1(self):
        ciclo.cerrar_votacion(self.ronda1)  # Se escruta sola: alimenta otra ronda.
        self.ronda1.refresh_from_db()
        if self.ronda2:
            self.ronda2.refresh_from_db()


class ProgramarConRondasTests(TestCase):

    def test_regla_que_requiere_otra_ronda_sin_configurarla_no_programa(self):
        with self.assertRaises(ciclo.TransicionInvalida) as error:
            Escenario().armar(Votacion.MAYORIA_ABSOLUTA, con_siguiente=False)
        self.assertTrue(any('ronda siguiente' in e for e in error.exception.errores))

    def test_la_ronda_derivada_espera_sin_candidatos(self):
        esc = Escenario().armar(Votacion.CLASIFICAN_N)

        self.assertEqual(esc.ronda1.estado, 'ABIERTA')
        esc.ronda2.refresh_from_db()
        self.assertEqual(esc.ronda2.estado, 'BORRADOR')
        self.assertFalse(esc.ronda2.opciones.exists())


class ClasificatoriaTests(TestCase):

    def test_los_clasificados_pasan_a_la_final_con_su_foto(self):
        esc = Escenario().armar(Votacion.CLASIFICAN_N, candidatos=3, clasifican=2)
        Opcion.objects.filter(pk=esc.opciones[1].pk).update(foto='opciones/2027/foto.jpg')
        votos(esc.opciones[0], 3)
        votos(esc.opciones[1], 5)
        votos(esc.opciones[2], 1)

        esc.cerrar_ronda1()

        self.assertEqual(esc.ronda1.estado, 'ESCRUTADA')
        self.assertEqual(esc.ronda1.resultado, 'CLASIFICADOS')
        self.assertEqual(esc.ronda2.estado, 'LISTA')
        finalistas = list(esc.ronda2.opciones.filter(es_voto_blanco=False).order_by('orden'))
        self.assertEqual([o.nombre for o in finalistas], ['Candidato 2', 'Candidato 1'])
        self.assertEqual(finalistas[0].foto.name, 'opciones/2027/foto.jpg')
        self.assertTrue(esc.ronda2.opciones.filter(es_voto_blanco=True).exists())

    def test_empate_en_el_corte_lo_decide_el_organizador(self):
        esc = Escenario().armar(Votacion.CLASIFICAN_N, candidatos=3, clasifican=2)
        votos(esc.opciones[0], 5)
        votos(esc.opciones[1], 2)
        votos(esc.opciones[2], 2)

        esc.cerrar_ronda1()

        self.assertEqual(esc.ronda1.resultado, 'EMPATE')
        self.assertEqual(esc.ronda2.estado, 'BORRADOR')

        ciclo.resolver_empate(
            esc.ronda1, [esc.opciones[0], esc.opciones[2]], 'Desempate por puntaje del jurado.'
        )

        esc.ronda1.refresh_from_db()
        esc.ronda2.refresh_from_db()
        self.assertEqual(esc.ronda1.resultado, 'CLASIFICADOS')
        self.assertEqual(esc.ronda2.estado, 'LISTA')
        self.assertEqual(
            set(esc.ronda2.opciones.filter(es_voto_blanco=False).values_list('nombre', flat=True)),
            {'Candidato 1', 'Candidato 3'},
        )

    def test_resolver_empate_exige_la_cantidad_justa(self):
        esc = Escenario().armar(Votacion.CLASIFICAN_N, candidatos=3, clasifican=2)
        esc.cerrar_ronda1()  # Sin votos: empate.

        with self.assertRaises(ciclo.TransicionInvalida):
            ciclo.resolver_empate(esc.ronda1, [esc.opciones[0]], 'Solo uno, faltan opciones.')


class MayoriaAbsolutaTests(TestCase):

    def test_con_mas_del_50_hay_ganador_y_la_segunda_vuelta_se_cancela(self):
        esc = Escenario().armar(Votacion.MAYORIA_ABSOLUTA)
        votos(esc.opciones[0], 6)
        votos(esc.opciones[1], 3)
        votos(esc.blanco, 1)

        esc.cerrar_ronda1()

        self.assertEqual(esc.ronda1.resultado, 'GANADOR')
        self.assertEqual(esc.ronda1.opcion_ganadora, esc.opciones[0])
        self.assertEqual(esc.ronda2.estado, 'CANCELADA')

    def test_el_voto_en_blanco_cuenta_para_el_50(self):
        """5 de 10 no es mayoría absoluta si los otros 5 incluyen votos en blanco."""
        esc = Escenario().armar(Votacion.MAYORIA_ABSOLUTA)
        votos(esc.opciones[0], 5)
        votos(esc.opciones[1], 3)
        votos(esc.blanco, 2)

        esc.cerrar_ronda1()

        self.assertEqual(esc.ronda1.resultado, 'SEGUNDA_RONDA')
        self.assertEqual(esc.ronda2.estado, 'LISTA')
        self.assertEqual(esc.ronda2.opciones.filter(es_voto_blanco=False).count(), 2)

    def test_se_vota_en_ambas_vueltas(self):
        """La regla de unicidad es por categoría y ronda."""
        esc = Escenario().armar(Votacion.MAYORIA_ABSOLUTA)
        user = get_user_model().objects.create_user(username='v', password='x')
        PadronVotante.objects.create(usuario=user, votacion=esc.ronda1, ha_votado=True)

        PadronVotante.objects.create(usuario=user, votacion=esc.ronda2, ha_votado=True)

        self.assertEqual(
            set(PadronVotante.objects.filter(usuario=user).values_list('ronda', flat=True)), {1, 2}
        )


class RepeticionPorVotoEnBlancoTests(TestCase):

    def test_si_gana_el_blanco_se_repite_con_candidatos_nuevos(self):
        esc = Escenario().armar(Votacion.MAYORIA_SIMPLE, repetir=True)
        votos(esc.blanco, 6)
        votos(esc.opciones[0], 4)

        esc.cerrar_ronda1()

        self.assertEqual(esc.ronda1.resultado, 'REPETIR')
        self.assertEqual(esc.ronda2.estado, 'BORRADOR')
        self.assertTrue(esc.ronda2.admite_opciones_nuevas)

        Opcion.objects.create(votacion=esc.ronda2, nombre='Nuevo A', orden=1)
        Opcion.objects.create(votacion=esc.ronda2, nombre='Nuevo B', orden=2)
        ciclo.preparar_ronda(esc.ronda2)

        esc.ronda2.refresh_from_db()
        self.assertEqual(esc.ronda2.estado, 'LISTA')

    def test_sin_repeticion_el_blanco_nunca_gana(self):
        esc = Escenario().armar(Votacion.MAYORIA_SIMPLE, con_siguiente=False)
        votos(esc.blanco, 6)
        votos(esc.opciones[0], 4)
        ciclo.cerrar_votacion(esc.ronda1)

        ciclo.escrutar(esc.ronda1)

        esc.ronda1.refresh_from_db()
        self.assertEqual(esc.ronda1.resultado, 'GANADOR')
        self.assertEqual(esc.ronda1.opcion_ganadora, esc.opciones[0])


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class FotosTests(TestCase):

    def setUp(self):
        call_command('cargar_permisos', stdout=io.StringIO())
        user = get_user_model().objects.create_user(username='org-fotos', password='x')
        Usuario.objects.create(
            user=user, documento='5600000001', nombres='Org', apellidos='Fotos',
            correo='org-fotos@test.com', rol=Role.objects.get(nombre='Organizador'),
        )
        self.client.force_login(user)
        ahora = timezone.now()
        edicion = Edicion.objects.create(nombre='F', anio=2027)
        self.votacion = Votacion.objects.create(
            edicion=edicion, categoria=Categoria.objects.create(nombre='C'), nombre='V',
            fecha_apertura=ahora, fecha_cierre=ahora + timedelta(days=1),
        )

    def _imagen(self, formato='PNG', tamano=(900, 500)):
        salida = io.BytesIO()
        Image.new('RGB', tamano, (200, 30, 30)).save(salida, formato)
        return SimpleUploadedFile(f'foto.{formato.lower()}', salida.getvalue(), content_type='image/png')

    def test_la_foto_se_recorta_cuadrada_y_en_jpeg(self):
        self.client.post(
            reverse('gestion:opcion_crear', args=[self.votacion.id]),
            {'nombre': 'Con foto', 'orden': 1, 'foto': self._imagen()},
        )

        opcion = Opcion.objects.get(nombre='Con foto')
        with Image.open(opcion.foto.path) as imagen:
            self.assertEqual(imagen.size, (600, 600))
            self.assertEqual(imagen.format, 'JPEG')

    def test_un_archivo_que_no_es_imagen_se_rechaza(self):
        falso = SimpleUploadedFile('foto.png', b'no soy una imagen', content_type='image/png')

        respuesta = self.client.post(
            reverse('gestion:opcion_crear', args=[self.votacion.id]),
            {'nombre': 'Sin foto', 'orden': 1, 'foto': falso},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors['foto'])
        self.assertFalse(Opcion.objects.filter(nombre='Sin foto').exists())

    @override_settings(FOTO_MAX_BYTES=100)
    def test_una_foto_muy_pesada_se_rechaza(self):
        respuesta = self.client.post(
            reverse('gestion:opcion_crear', args=[self.votacion.id]),
            {'nombre': 'Pesada', 'orden': 1, 'foto': self._imagen()},
        )

        self.assertTrue(respuesta.context['form'].errors['foto'])
