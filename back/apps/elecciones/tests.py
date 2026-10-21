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

    def test_create_categoria(self):
        payload = {
            'titulo': 'Elección de ejemplo',
            'descripcion': 'Primera categoría',
            'fecha_apertura': '2026-11-01T10:00:00Z',
            'fecha_cierre': '2026-11-02T18:00:00Z',
            'estado': 'BORRADOR',
            'mostrar_resultados_en_vivo': False,
        }

        response = self.client.post(reverse('categorias-list'), payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['titulo'], 'Elección de ejemplo')
