from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion
from back.apps.votacion.models import PadronVotante, Voto


def crear_escenario():
    """Festival 2027 → Música → Canción favorita del público → A / B."""
    ahora = timezone.now()
    edicion = Edicion.objects.create(nombre='Festival 2027', anio=2027, estado='ACTIVA')
    categoria = Categoria.objects.create(nombre='Música')
    votacion = Votacion.objects.create(
        edicion=edicion,
        categoria=categoria,
        nombre='Canción favorita del público',
        fecha_apertura=ahora - timedelta(hours=2),
        fecha_cierre=ahora + timedelta(days=1),
        estado='ACTIVA',
        mostrar_resultados_en_vivo=True,
    )
    cancion_a = Opcion.objects.create(votacion=votacion, nombre='Canción A', subtitulo='Artista A', orden=1)
    cancion_b = Opcion.objects.create(votacion=votacion, nombre='Canción B', subtitulo='Artista B', orden=2)
    return edicion, categoria, votacion, cancion_a, cancion_b


def crear_votacion_extra(edicion, nombre_categoria, nombre_votacion, estado='ACTIVA', abierta=True, opcion='Opción extra'):
    ahora = timezone.now()
    categoria = Categoria.objects.create(nombre=nombre_categoria)
    votacion = Votacion.objects.create(
        edicion=edicion,
        categoria=categoria,
        nombre=nombre_votacion,
        fecha_apertura=ahora - timedelta(hours=2) if abierta else ahora + timedelta(days=1),
        fecha_cierre=ahora + timedelta(days=1) if abierta else ahora + timedelta(days=2),
        estado=estado,
    )
    return votacion, Opcion.objects.create(votacion=votacion, nombre=opcion, orden=1)


class OpcionesVotacionEndpointTests(APITestCase):

    def setUp(self):
        self.edicion, self.categoria, self.votacion, self.cancion_a, self.cancion_b = crear_escenario()
        self.otra_votacion, _ = crear_votacion_extra(
            self.edicion,
            'Letra inédita',
            'Mejor letra',
            opcion='Letra de otra categoría',
        )

    def test_ruta_opciones_esta_registrada(self):
        url = reverse('votacion-opciones', kwargs={'votacion_id': self.votacion.id})

        self.assertEqual(url, f'/api/votacion/votaciones/{self.votacion.id}/opciones/')

    def test_consulta_opciones_responde_correctamente(self):
        url = reverse('votacion-opciones', kwargs={'votacion_id': self.votacion.id})

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_consulta_devuelve_solo_opciones_de_su_votacion(self):
        url = reverse('votacion-opciones', kwargs={'votacion_id': self.votacion.id})

        respuesta = self.client.get(url)

        self.assertEqual(len(respuesta.data), 2)
        nombres = [fila['nombre'] for fila in respuesta.data]
        self.assertEqual(nombres, ['Canción A', 'Canción B'])

    def test_consulta_incluye_numero_de_casilla(self):
        url = reverse('votacion-opciones', kwargs={'votacion_id': self.votacion.id})

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.data[0]['orden'], 1)
        self.assertEqual(respuesta.data[0]['subtitulo'], 'Artista A')


class FlujoVotacionMVTTest(TestCase):

    def setUp(self):
        self.edicion, self.categoria, self.votacion, self.cancion_a, self.cancion_b = crear_escenario()
        self.user = get_user_model().objects.create_user(
            username='votante',
            password='clave-segura-123',
        )

    def test_inicio_lista_la_edicion(self):
        respuesta = self.client.get(reverse('inicio'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Festival 2027')

    def test_tarjeton_muestra_las_opciones(self):
        self.client.force_login(self.user)

        respuesta = self.client.get(reverse('tarjeton', args=[self.votacion.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Canción A')
        self.assertContains(respuesta, 'Canción B')

    def test_votar_registra_voto_y_marca_padron(self):
        self.client.force_login(self.user)

        respuesta = self.client.post(
            reverse('votar', args=[self.votacion.pk]),
            {'opcion': self.cancion_a.pk},
        )

        self.assertRedirects(respuesta, reverse('resultados', args=[self.votacion.pk]))
        self.assertEqual(Voto.objects.count(), 1)
        self.assertEqual(Voto.objects.first().opcion, self.cancion_a)

        padron = PadronVotante.objects.get(usuario=self.user, votacion=self.votacion)
        self.assertTrue(padron.ha_votado)
        self.assertTrue(padron.hash_comprobante)

    def test_el_voto_queda_firmado(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse('votar', args=[self.votacion.pk]),
            {'opcion': self.cancion_a.pk},
        )

        voto = Voto.objects.first()
        self.assertEqual(len(voto.firma_criptografica), 64)

    def test_no_se_puede_votar_dos_veces(self):
        self.client.force_login(self.user)
        url = reverse('votar', args=[self.votacion.pk])

        self.client.post(url, {'opcion': self.cancion_a.pk})
        self.client.post(url, {'opcion': self.cancion_b.pk})

        self.assertEqual(Voto.objects.count(), 1)
        self.assertEqual(Voto.objects.first().opcion, self.cancion_a)

    def test_no_permite_votar_una_opcion_de_otra_votacion(self):
        _, opcion_ajena = crear_votacion_extra(
            self.edicion,
            'Letra inédita',
            'Mejor letra',
            opcion='Canción de otra votación',
        )
        self.client.force_login(self.user)

        respuesta = self.client.post(
            reverse('votar', args=[self.votacion.pk]),
            {'opcion': opcion_ajena.pk},
        )

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(Voto.objects.count(), 0)

    def test_no_permite_votar_si_la_votacion_esta_cerrada(self):
        cerrada, opcion = crear_votacion_extra(
            self.edicion,
            'Letra inédita',
            'Mejor letra',
            estado='FINALIZADA',
            abierta=False,
        )
        self.client.force_login(self.user)

        respuesta = self.client.post(
            reverse('votar', args=[cerrada.pk]),
            {'opcion': opcion.pk},
        )

        self.assertRedirects(respuesta, reverse('tarjeton', args=[cerrada.pk]))
        self.assertEqual(Voto.objects.count(), 0)

    def test_resultados_muestra_el_conteo(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse('votar', args=[self.votacion.pk]),
            {'opcion': self.cancion_a.pk},
        )

        respuesta = self.client.get(reverse('resultados', args=[self.votacion.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Canción A')
        self.assertEqual(respuesta.context['total'], 1)
