from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from back.apps.usuarios.models import Role, Usuario


class EleccionesFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.role = Role.objects.create(nombre='Organizador', descripcion='Gestor electoral')
        self.user = self.user_model.objects.create_user(
            username='organizador1',
            email='organizador@test.com',
            password='organizador1234'
        )
        self.perfil = Usuario.objects.create(
            user=self.user,
            documento='123456789',
            nombres='Organizador',
            apellidos='Prueba',
            correo='organizador@test.com',
            rol=self.role,
        )

        login = self.client.post(
            reverse('login'),
            {'correo': 'organizador@test.com', 'password': 'organizador1234'},
            format='json'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def _crear_edicion(self):
        return self.client.post(
            reverse('ediciones-list'),
            {'nombre': 'Elecciones 2026', 'anio': 2026, 'estado': 'BORRADOR'},
            format='json',
        )

    def _crear_categoria(self, nombre='Consejo Estudiantil'):
        return self.client.post(
            reverse('categorias-list'),
            {'nombre': nombre, 'descripcion': 'Categoría de prueba'},
            format='json',
        )

    def _crear_votacion(self, edicion_id, categoria_id):
        return self.client.post(
            reverse('votaciones-list'),
            {
                'edicion': edicion_id,
                'categoria': categoria_id,
                'fecha_apertura': '2026-11-01T10:00:00Z',
                'fecha_cierre': '2026-11-02T18:00:00Z',
                'estado': 'BORRADOR',
                'mostrar_resultados_en_vivo': False,
            },
            format='json',
        )

    def test_crear_edicion_asigna_creador(self):
        response = self._crear_edicion()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nombre'], 'Elecciones 2026')
        self.assertEqual(response.data['anio'], 2026)
        self.assertEqual(response.data['creador'], self.perfil.id)

    def test_crear_categoria(self):
        response = self._crear_categoria()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nombre'], 'Consejo Estudiantil')

    def test_crear_votacion_con_edicion_y_categoria(self):
        edicion = self._crear_edicion()
        categoria = self._crear_categoria()

        response = self._crear_votacion(edicion.data['id'], categoria.data['id'])

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data['titulo'],
            'Consejo Estudiantil · Elecciones 2026',
        )
        self.assertEqual(response.data['edicion'], edicion.data['id'])
        self.assertEqual(response.data['categoria'], categoria.data['id'])

    def test_crear_normativa_y_opcion_de_votacion(self):
        edicion = self._crear_edicion()
        categoria = self._crear_categoria()
        votacion = self._crear_votacion(edicion.data['id'], categoria.data['id'])
        votacion_id = votacion.data['id']

        normativa = self.client.post(
            reverse('normativas-list', kwargs={'votacion_id': votacion_id}),
            {'titulo': 'Reglamento', 'contenido_html': '<p>Texto</p>'},
            format='json',
        )
        self.assertEqual(normativa.status_code, 201)
        self.assertEqual(normativa.data['votacion'], votacion_id)

        opcion = self.client.post(
            reverse('opciones-list'),
            {
                'nombre': 'Juan Pérez',
                'identificador_unico': 'juan-perez',
                'biografia': 'Candidato de prueba',
            },
            format='json',
        )
        self.assertEqual(opcion.status_code, 201)

        opcion_votacion = self.client.post(
            reverse('opciones-votacion-list', kwargs={'votacion_id': votacion_id}),
            {
                'opcion': opcion.data['id'],
                'numero_casilla': 1,
                'es_voto_blanco': False,
                'partido_lista': 'Lista A',
            },
            format='json',
        )
        self.assertEqual(opcion_votacion.status_code, 201)
        self.assertEqual(opcion_votacion.data['opcion_detalle']['nombre'], 'Juan Pérez')
        self.assertEqual(opcion_votacion.data['numero_casilla'], 1)

    def test_no_permite_dos_casillas_con_el_mismo_numero(self):
        edicion = self._crear_edicion()
        categoria = self._crear_categoria()
        votacion = self._crear_votacion(edicion.data['id'], categoria.data['id'])
        votacion_id = votacion.data['id']

        opcion_1 = self.client.post(
            reverse('opciones-list'),
            {'nombre': 'Opción 1', 'identificador_unico': 'opcion-1'},
            format='json',
        )
        opcion_2 = self.client.post(
            reverse('opciones-list'),
            {'nombre': 'Opción 2', 'identificador_unico': 'opcion-2'},
            format='json',
        )

        url = reverse('opciones-votacion-list', kwargs={'votacion_id': votacion_id})
        self.client.post(
            url,
            {'opcion': opcion_1.data['id'], 'numero_casilla': 1},
            format='json',
        )
        repetida = self.client.post(
            url,
            {'opcion': opcion_2.data['id'], 'numero_casilla': 1},
            format='json',
        )

        self.assertEqual(repetida.status_code, 400)
