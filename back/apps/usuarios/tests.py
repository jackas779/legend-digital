from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_and_profile(self):
        payload = {
            'documento': '1015488962',
            'nombres': 'Cardina',
            'apellidos': 'Rentería',
            'correo': 'cardina@test.com',
            'password': 'voto1234',
            'rol_id': 1,
        }

        response = self.client.post(reverse('register'), payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['correo'], 'cardina@test.com')

    def test_login_returns_tokens(self):
        # setup role and user
        from back.apps.usuarios.models import Role, Usuario
        from django.contrib.auth import get_user_model

        role = Role.objects.create(nombre='Votante', descripcion='Usuario votante')
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username='cardina',
            email='cardina@test.com',
            password='voto1234'
        )
        Usuario.objects.create(
            user=user,
            documento='1015488962',
            nombres='Cardina',
            apellidos='Rentería',
            correo='cardina@test.com',
            rol=role,
        )

        response = self.client.post(
            reverse('login'),
            {'correo': 'cardina@test.com', 'password': 'voto1234'},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
