from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class AuthFlowTests(TestCase):
    def setUp(self):
        # El throttle de login vive en el cache: se limpia antes de cada clase.
        cache.clear()
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
        from django.core.cache import cache
        from back.apps.usuarios.models import Role, Usuario

        # El throttle de login vive en el cache y persiste entre tests del
        # mismo proceso: se limpia para que un test no multiplique los
        # intentos del siguiente.
        cache.clear()
        self.cache = cache
        self.addCleanup(cache.clear)
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

        # El throttle del cache no debe interferir con esta verificación.
        self.cache.clear()

        # Incluso con la contraseña correcta queda bloqueada.
        response = self._login('cardina')
        self.assertEqual(response.status_code, 400)
        self.assertIn('bloqueada', str(response.data).lower())

    def test_sexta_peticion_recibe_429(self):
        """Entregable A11: límite de 5 intentos por minuto en la API."""
        for _ in range(5):
            self._login('cardina', password='incorrecta')

        response = self._login('cardina', password='incorrecta')
        self.assertEqual(response.status_code, 429)

        # Un ataque contra una cuenta no la bloquea a las demás: la otra
        # cuenta no acumula intentos ni quedará bloqueada.
        from back.apps.usuarios.models import Usuario

        otro_user = self.user_model.objects.create_user(
            username='otro', password='otro-clave-1'
        )
        otro_perfil = Usuario.objects.create(
            user=otro_user,
            documento='1022222222',
            nombres='Otro',
            apellidos='Vecino',
            correo='otro@test.com',
            rol=self.rol,
        )
        self.assertEqual(otro_perfil.intentos_fallidos, 0)
        self.assertIsNone(otro_perfil.bloqueado_hasta)

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


class SesionWebTests(TestCase):
    """Entregables A1, A7 y A8: login/logout por sesión."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        from back.apps.usuarios.models import Role, Usuario

        self.rol = Role.objects.create(nombre='Votante', descripcion='Votante')
        self.user = get_user_model().objects.create_user(
            username='cardina',
            email='cardina@test.com',
            password='voto1234',
        )
        Usuario.objects.create(
            user=self.user,
            documento='1015488962',
            nombres='Cardina',
            apellidos='Rentería',
            correo='cardina@test.com',
            rol=self.rol,
        )

    def _entrar(self, identificador='cardina', **extra):
        return self.client.post(
            reverse('auth:login'),
            {'identificador': identificador, 'password': 'voto1234', **extra},
        )

    def test_login_web_acepta_documento(self):
        respuesta = self._entrar('1015488962')

        self.assertRedirects(respuesta, reverse('inicio'))
        self.assertTrue(respuesta.wsgi_request.user.is_authenticated)

    def test_recordarme_extiende_la_sesion_a_7_dias(self):
        respuesta = self._entrar(recordarme='on')

        # ~7 días en segundos (con holgura por la petición en curso).
        self.assertAlmostEqual(
            respuesta.wsgi_request.session.get_expiry_age(),
            7 * 24 * 60 * 60,
            delta=60,
        )

    def test_sin_recordarme_expira_al_30_minutos(self):
        respuesta = self._entrar()

        self.assertAlmostEqual(
            respuesta.wsgi_request.session.get_expiry_age(),
            30 * 60,
            delta=60,
        )

    def test_next_inseguro_se_ignora(self):
        respuesta = self._entrar(next='http://maligno.example/robar')

        self.assertRedirects(respuesta, reverse('inicio'))

    def test_logout_por_post_cierra_la_sesion(self):
        self._entrar()
        csrf_token = self.client.cookies['csrftoken'].value

        respuesta = self.client.post(
            reverse('auth:logout'),
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertRedirects(respuesta, reverse('inicio'))
        seguimiento = self.client.get(reverse('inicio'))
        self.assertFalse(seguimiento.wsgi_request.user.is_authenticated)


class CambioPasswordWebTests(TestCase):
    """Entregable A9: cambio de contraseña en /cuenta/password/."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        from back.apps.usuarios.models import Role, Usuario

        self.rol = Role.objects.create(nombre='Votante', descripcion='Votante')
        self.user = get_user_model().objects.create_user(
            username='cardina',
            email='cardina@test.com',
            password='clave-vieja-2026',
        )
        Usuario.objects.create(
            user=self.user,
            documento='1015488962',
            nombres='Cardina',
            apellidos='Rentería',
            correo='cardina@test.com',
            rol=self.rol,
        )
        self.assertTrue(
            self.client.login(username='cardina', password='clave-vieja-2026'),
        )

    def test_cambio_invalida_la_vieja(self):
        respuesta = self.client.post(
            reverse('cambiar_password'),
            {
                'old_password': 'clave-vieja-2026',
                'new_password1': 'clave-nueva-2026',
                'new_password2': 'clave-nueva-2026',
            },
        )

        self.assertRedirects(respuesta, reverse('inicio'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('clave-nueva-2026'))
        # La sesión sigue abierta: no pide iniciar sesión de nuevo.
        dos = self.client.get(reverse('cambiar_password'))
        self.assertEqual(dos.status_code, 200)

    def test_exige_la_contraseña_actual(self):
        respuesta = self.client.post(
            reverse('cambiar_password'),
            {
                'old_password': 'equivocada',
                'new_password1': 'clave-nueva-2026',
                'new_password2': 'clave-nueva-2026',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors['old_password'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('clave-vieja-2026'))

    def test_aplica_la_politica_de_contraseñas(self):
        respuesta = self.client.post(
            reverse('cambiar_password'),
            {
                'old_password': 'clave-vieja-2026',
                'new_password1': '12345678',
                'new_password2': '12345678',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors['new_password2'])

    def test_requiere_sesion(self):
        self.client.logout()

        respuesta = self.client.get(reverse('cambiar_password'))

        self.assertRedirects(respuesta, f"{reverse('auth:login')}?next=/cuenta/password/")


class ResetDemoTests(TestCase):
    """Entregable U4: reset_demo borra votos y padrones, nada más."""

    def setUp(self):
        from datetime import timedelta

        from django.contrib.auth import get_user_model
        from django.utils import timezone

        from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion
        from back.apps.votacion.models import PadronVotante, Voto

        self.user = get_user_model().objects.create_user(
            username='cardina', password='voto1234'
        )
        edicion = Edicion.objects.create(nombre='Festival', anio=2027, estado='ACTIVA')
        categoria = Categoria.objects.create(nombre='Música')
        votacion = Votacion.objects.create(
            edicion=edicion,
            categoria=categoria,
            nombre='Canción favorita',
            estado='ACTIVA',
            fecha_apertura=timezone.now() - timedelta(days=1),
            fecha_cierre=timezone.now() + timedelta(days=1),
        )
        self.opcion = Opcion.objects.create(votacion=votacion, nombre='Canción A', orden=1)
        self.voto = Voto.objects.create(opcion=self.opcion)
        self.padron = PadronVotante.objects.create(
            votacion=votacion,
            usuario=self.user,
            ha_votado=True,
            hash_comprobante='abc123',
        )

    def test_borra_votos_y_padrones_conserva_estructuras(self):
        import io

        from django.core.management import call_command
        from back.apps.elecciones.models import Edicion, Opcion, Votacion
        from back.apps.votacion.models import PadronVotante, Voto

        call_command('reset_demo', '--confirmar', stdout=io.StringIO())

        self.assertEqual(Voto.objects.count(), 0)
        self.assertEqual(PadronVotante.objects.count(), 0)
        self.assertEqual(Edicion.objects.count(), 1)
        self.assertEqual(Votacion.objects.count(), 1)
        self.assertEqual(Opcion.objects.count(), 1)

    def test_sin_confirmar_no_borra_nada(self):
        from django.core.management import call_command
        from back.apps.votacion.models import Voto

        with self.assertRaises(SystemExit):
            call_command('reset_demo')
        self.assertEqual(Voto.objects.count(), 1)
