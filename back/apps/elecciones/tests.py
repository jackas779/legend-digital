from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from back.apps.usuarios.models import Role, Usuario

import io


class EleccionesFlowTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        from django.core.management import call_command

        # El throttle de login vive en el cache: se limpia antes de cada clase.
        cache.clear()
        self.client = APIClient()
        self.user_model = get_user_model()
        self.role = Role.objects.create(nombre='Organizador', descripcion='Gestor electoral')
        # P2: carga el catálogo y asigna los permisos del rol Organizador.
        call_command('cargar_permisos', stdout=io.StringIO())
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
            {'nombre': 'Festival 2027', 'anio': 2027, 'estado': 'BORRADOR'},
            format='json',
        )

    def _crear_categoria(self, nombre='Música'):
        return self.client.post(
            reverse('categorias-list'),
            {'nombre': nombre, 'descripcion': 'Categoría de prueba'},
            format='json',
        )

    def _crear_votacion(self, edicion_id, categoria_id, nombre='Canción favorita del público'):
        return self.client.post(
            reverse('votaciones-list'),
            {
                'edicion': edicion_id,
                'categoria': categoria_id,
                'nombre': nombre,
                'fecha_apertura': '2027-11-01T10:00:00Z',
                'fecha_cierre': '2027-11-02T18:00:00Z',
                'estado': 'BORRADOR',
                'mostrar_resultados_en_vivo': False,
            },
            format='json',
        )

    def test_crear_edicion_asigna_creador(self):
        response = self._crear_edicion()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nombre'], 'Festival 2027')
        self.assertEqual(response.data['anio'], 2027)
        self.assertEqual(response.data['creador'], self.perfil.id)

    def test_crear_categoria(self):
        response = self._crear_categoria()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nombre'], 'Música')

    def test_crear_votacion_con_edicion_y_categoria(self):
        edicion = self._crear_edicion()
        categoria = self._crear_categoria()

        response = self._crear_votacion(edicion.data['id'], categoria.data['id'])

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data['titulo'],
            'Canción favorita del público · Festival 2027',
        )
        self.assertEqual(response.data['nombre'], 'Canción favorita del público')
        self.assertEqual(response.data['edicion'], edicion.data['id'])
        self.assertEqual(response.data['categoria'], categoria.data['id'])

    def test_votacion_exige_nombre(self):
        edicion = self._crear_edicion()
        categoria = self._crear_categoria()

        response = self.client.post(
            reverse('votaciones-list'),
            {
                'edicion': edicion.data['id'],
                'categoria': categoria.data['id'],
                'fecha_apertura': '2027-11-01T10:00:00Z',
                'fecha_cierre': '2027-11-02T18:00:00Z',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('nombre', response.data)

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
                'votacion': votacion_id,
                'nombre': 'Canción A',
                'subtitulo': 'Artista A',
                'orden': 1,
            },
            format='json',
        )
        self.assertEqual(opcion.status_code, 201)
        self.assertEqual(opcion.data['nombre'], 'Canción A')
        self.assertEqual(opcion.data['orden'], 1)

    def test_no_permite_dos_opciones_con_la_misma_casilla(self):
        edicion = self._crear_edicion()
        categoria = self._crear_categoria()
        votacion = self._crear_votacion(edicion.data['id'], categoria.data['id'])
        votacion_id = votacion.data['id']

        url = reverse('opciones-list')
        self.client.post(
            url,
            {'votacion': votacion_id, 'nombre': 'Canción A', 'orden': 1},
            format='json',
        )
        repetida = self.client.post(
            url,
            {'votacion': votacion_id, 'nombre': 'Canción B', 'orden': 1},
            format='json',
        )

        self.assertEqual(repetida.status_code, 400)
        self.assertIn('orden', repetida.data)
