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

    def test_me_and_roles_are_protected(self):
        from django.contrib.auth import get_user_model
        from back.apps.usuarios.models import Role, Usuario

        role = Role.objects.create(nombre='Administrador', descripcion='Admin general')
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username='admin1',
            email='admin@test.com',
            password='admin1234'
        )
        Usuario.objects.create(
            user=user,
            documento='999999999',
            nombres='Admin',
            apellidos='Sistema',
            correo='admin@test.com',
            rol=role,
        )

        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, 401)

        login = self.client.post(
            reverse('login'),
            {'correo': 'admin@test.com', 'password': 'admin1234'},
            format='json'
        )
        token = login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        me = self.client.get(reverse('me'))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['correo'], 'admin@test.com')

        roles = self.client.get(reverse('roles'))
        self.assertEqual(roles.status_code, 200)
        self.assertGreaterEqual(len(roles.data), 1)

    def test_login_accepts_username(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user_model.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin1234',
        )

        response = self.client.post(
            reverse('login'),
            {'correo': 'admin', 'password': 'admin1234'},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_me_works_for_user_without_profile(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username='root',
            email='root@test.com',
            password='root1234',
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('me'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['correo'], 'root@test.com')
        self.assertIsNone(response.data['rol'])


class LoginEndurecidoTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from back.apps.usuarios.models import Role, Usuario

        self.user_model = get_user_model()
        self.rol = Role.objects.create(nombre='Votante', descripcion='Usuario votante')
        self.user = self.user_model.objects.create_user(
            username='cardina',
            email='cardina@test.com',
            password='voto1234',
        )
        self.perfil = Usuario.objects.create(
            user=self.user,
            documento='1015488962',
            nombres='Cardina',
            apellidos='Rentería',
            correo='cardina@test.com',
            rol=self.rol,
        )

    def _login(self, identificador, password='voto1234'):
        return self.client.post(
            reverse('login'),
            {'correo': identificador, 'password': password},
            format='json',
        )

    def test_login_acepta_documento(self):
        response = self._login('1015488962')

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_login_rechaza_usuario_suspendido(self):
        self.perfil.estado = 'SUSPENDIDO'
        self.perfil.save(update_fields=['estado'])

        response = self._login('cardina')

        self.assertEqual(response.status_code, 400)

    def test_intento_fallido_incrementa_el_contador(self):
        self._login('cardina', password='incorrecta')

        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.intentos_fallidos, 1)

    def test_cinco_fallos_bloquean_la_cuenta(self):
        for _ in range(5):
            self._login('cardina', password='incorrecta')

        self.perfil.refresh_from_db()
        self.assertIsNotNone(self.perfil.bloqueado_hasta)

        # Incluso con la contraseña correcta queda bloqueada.
        response = self._login('cardina')
        self.assertEqual(response.status_code, 400)
        self.assertIn('bloqueada', str(response.data).lower())

    def test_login_exitoso_limpia_los_intentos(self):
        self._login('cardina', password='incorrecta')
        self._login('cardina')

        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.intentos_fallidos, 0)
        self.assertIsNone(self.perfil.bloqueado_hasta)


class RegistroWebTests(TestCase):
    """Entregables A3 y A6: alta de votante por el sitio."""

    def setUp(self):
        self.datos = {
            'documento': '1015488962',
            'nombres': 'Cardina',
            'apellidos': 'Rentería',
            'correo': 'cardina@test.com',
            'password': 'clave-segura-2026',
            'password_confirm': 'clave-segura-2026',
        }

    def test_registro_crea_cuenta_e_inicia_sesion(self):
        from django.contrib.auth import get_user_model
        from back.apps.usuarios.models import Usuario

        respuesta = self.client.post(
            reverse('registro'),
            self.datos,
            follow=True,
        )

        self.assertRedirects(respuesta, reverse('inicio'))
        self.assertTrue(respuesta.context['user'].is_authenticated)

        user = get_user_model().objects.get(email=self.datos['correo'])
        self.assertEqual(user.first_name, 'Cardina')

        perfil = Usuario.objects.get(user=user)
        self.assertEqual(perfil.documento, '1015488962')
        self.assertEqual(perfil.rol.nombre, 'Votante')

    def test_registro_rechaza_correo_duplicado(self):
        from back.apps.usuarios.models import Usuario

        self.client.post(reverse('registro'), self.datos.copy())
        self.client.logout()
        total = Usuario.objects.count()

        respuesta = self.client.post(
            reverse('registro'),
            {
                **self.datos,
                'documento': '999999999',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.context['form'].is_valid())
        self.assertEqual(
            respuesta.context['form'].errors['correo'],
            ['Este correo ya está registrado.'],
        )
        self.assertEqual(Usuario.objects.count(), total)

    def test_registro_rechaza_documento_duplicado(self):
        from back.apps.usuarios.models import Usuario

        self.client.post(reverse('registro'), self.datos.copy())
        self.client.logout()
        total = Usuario.objects.count()

        respuesta = self.client.post(
            reverse('registro'),
            {
                **self.datos,
                'correo': 'otro@test.com',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.context['form'].errors['documento'],
            ['Este documento ya está registrado.'],
        )
        self.assertEqual(Usuario.objects.count(), total)

    def test_registro_aplica_politica_de_contraseña(self):
        respuesta = self.client.post(
            reverse('registro'),
            {
                **self.datos,
                'password': '123',
                'password_confirm': '123',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.context['form'].is_valid())
        self.assertTrue(respuesta.context['form'].errors['password'])

    def test_registro_rechaza_contraseñas_distintas(self):
        respuesta = self.client.post(
            reverse('registro'),
            {
                **self.datos,
                'password_confirm': 'otra-contraseña',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.context['form'].errors['password_confirm'],
            ['Las contraseñas no coinciden.'],
        )
