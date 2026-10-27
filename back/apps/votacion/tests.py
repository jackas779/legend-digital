import io
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


class FlujoVotanteTests(TestCase):
    """Entregables V4, V5 y Q4: comprobante e historial del votante."""

    def setUp(self):
        from django.core.cache import cache
        from django.core.management import call_command

        from back.apps.usuarios.models import Role, Usuario

        cache.clear()
        call_command('cargar_permisos', stdout=io.StringIO())
        self.edicion, self.categoria, self.votacion, self.cancion_a, self.cancion_b = (
            crear_escenario()
        )
        self.user_model = get_user_model()

        self.votante = self.user_model.objects.create_user(
            username='votante-flujo', password='voto1234'
        )
        rol_votante = Role.objects.get(nombre='Votante')
        Usuario.objects.create(
            user=self.votante,
            documento='8806000001',
            nombres='Votante',
            apellidos='Prueba',
            correo='votante-flujo@test.com',
            rol=rol_votante,
        )
        self.otro = self.user_model.objects.create_user(
            username='otro-votante', password='voto1234'
        )

    def _votar(self):
        self.client.force_login(self.votante)
        self.client.post(
            reverse('votar', args=[self.votacion.pk]),
            {'opcion': self.cancion_a.pk},
        )
        from back.apps.votacion.models import PadronVotante

        return PadronVotante.objects.get(usuario=self.votante, votacion=self.votacion)

    def test_comprobante_muestra_hash_y_sin_la_opcion(self):
        """V4/Q4: votación, fecha y hash; nunca revela la opción elegida."""
        padron = self._votar()

        respuesta = self.client.get(
            reverse('comprobante', args=[padron.hash_comprobante])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Canción favorita del público')
        self.assertContains(respuesta, padron.hash_comprobante)
        self.assertNotContains(respuesta, 'Canción A')
        self.assertNotContains(respuesta, 'Artista A')

    def test_comprobante_solo_lo_ve_el_dueno(self):
        padron = self._votar()

        # Otro usuario con sesión: prohibido.
        self.client.force_login(self.otro)
        self.assertEqual(
            self.client.get(
                reverse('comprobante', args=[padron.hash_comprobante])
            ).status_code,
            403,
        )

        # Anónimo: al login.
        self.client.logout()
        respuesta = self.client.get(
            reverse('comprobante', args=[padron.hash_comprobante])
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/accounts/login/', respuesta['Location'])

    def test_historial_lista_las_votaciones_votadas(self):
        """V5: /mis-votos/ lista sus votaciones con enlace al comprobante."""
        padron = self._votar()

        respuesta = self.client.get(reverse('mis_votos'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Canción favorita del público')
        self.assertContains(
            respuesta,
            reverse('comprobante', args=[padron.hash_comprobante]),
        )
        # Sin votos: mensaje de vacío para el otro usuario.
        self.client.force_login(self.otro)
        vacio = self.client.get(reverse('mis_votos'))
        self.assertContains(vacio, 'Aún no has votado')


class RedireccioneRolTests(TestCase):
    """Entregable V6: destino por rol tras el login."""

    def setUp(self):
        from django.core.cache import cache
        from django.core.management import call_command

        from back.apps.usuarios.models import Role, Usuario

        cache.clear()
        call_command('cargar_permisos', stdout=io.StringIO())
        self.user_model = get_user_model()
        cache.clear()
        self.pares = []
        for nombre in ('Administrador', 'Organizador', 'Votante', 'Auditor'):
            rol = Role.objects.get(nombre=nombre)
            user = self.user_model.objects.create_user(
                username=f'acc-{nombre.lower()}', password='clave-test-2026'
            )
            Usuario.objects.create(
                user=user,
                documento=f'8806-{int(rol.id):08d}',
                nombres=nombre,
                apellidos='Prueba',
                correo=f'acc-{nombre.lower()}@test.com',
                rol=rol,
            )
            self.pares.append((nombre, user))

    def _entrar(self, user):
        return self.client.post(
            reverse('auth:login'),
            {'identificador': user.username, 'password': 'clave-test-2026'},
        )

    def test_destino_por_rol(self):
        esperado = {
            'Administrador': '/admin/',
            'Organizador': reverse('gestion:ediciones'),
            'Votante': '/',  # listado de ediciones
            'Auditor': reverse('resultados_indice'),
        }
        for nombre, user in self.pares:
            with self.subTest(rol=nombre):
                respuesta = self._entrar(user)
                self.assertEqual(respuesta['Location'], esperado[nombre])
                self.client.logout()

    def test_next_seguro_tiene_prioridad_sobre_el_rol(self):
        _, votante = self.pares[2]

        respuesta = self.client.post(
            reverse('auth:login'),
            {
                'identificador': votante.username,
                'password': 'clave-test-2026',
                'next': '/mis-votos/',
            },
        )

        self.assertEqual(respuesta['Location'], '/mis-votos/')


class ResultadosVisibilidadTests(TestCase):
    """Entregables R2 y R3: visibilidad y consolidado por edición."""

    def setUp(self):
        from django.core.cache import cache
        from django.core.management import call_command

        from back.apps.usuarios.models import Role, Usuario

        cache.clear()
        call_command('cargar_permisos', stdout=io.StringIO())
        # R2: ACTIVA sin resultados en vivo.
        self.edicion, self.categoria, self.votacion, self.cancion_a, self.cancion_b = (
            crear_escenario()
        )
        self.votacion.mostrar_resultados_en_vivo = False
        self.votacion.save(update_fields=['mostrar_resultados_en_vivo'])

        self.user_model = get_user_model()
        self.votante = self.user_model.objects.create_user(
            username='votante-res', password='voto1234'
        )
        Usuario.objects.create(
            user=self.votante,
            documento='8806000044',
            nombres='Votante',
            apellidos='Prueba',
            correo='votante-res@test.com',
            rol=Role.objects.get(nombre='Votante'),
        )
        self.otro = self.user_model.objects.create_user(
            username='otro-res', password='voto1234'
        )

    def test_activa_sin_vivo_se_oculta_al_anonimo(self):
        self.client.force_login(self.user_model.objects.create_user(
            username='anonimo-real', password='voto1234'
        ))
        self.client.logout()

        respuesta = self.client.get(reverse('resultados', args=[self.votacion.pk]))

        self.assertRedirects(respuesta, reverse('tarjeton', args=[self.votacion.pk]))

    def test_resultados_ver_los_ve_antes_del_cierre(self):
        self.client.force_login(self.votante)

        respuesta = self.client.get(reverse('resultados', args=[self.votacion.pk]))

        self.assertEqual(respuesta.status_code, 200)

    def test_finalizada_es_publica(self):
        self.votacion.estado = 'FINALIZADA'
        self.votacion.save(update_fields=['estado'])
        self.client.logout()

        respuesta = self.client.get(reverse('resultados', args=[self.votacion.pk]))

        self.assertEqual(respuesta.status_code, 200)

    def test_consolidado_por_edicion(self):
        """R3: todas las votaciones de la edición; exige resultados.ver."""
        votacion_extra = crear_votacion_extra(self.edicion, 'Letra inédita', 'Mejor letra')
        self.client.force_login(self.otro)
        self.client.post(
            reverse('votar', args=[self.votacion.pk]), {'opcion': self.cancion_a.pk}
        )

        # Anónimo: exige permiso, redirige al login.
        self.client.logout()
        respuesta = self.client.get(
            reverse('resultados_consolidado', args=[self.edicion.pk])
        )
        self.assertEqual(respuesta.status_code, 302)

        # Votante (resultados.ver): ve el consolidado con las dos votaciones.
        self.client.force_login(self.votante)
        respuesta = self.client.get(
            reverse('resultados_consolidado', args=[self.edicion.pk])
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Canción favorita del público')
        self.assertContains(respuesta, 'Mejor letra')
        self.assertEqual(respuesta.context['total_edicion'], 1)
        del votacion_extra


class SimularVotacionTests(TestCase):
    """Datos simulados: crea votantes, emite votos y es idempotente."""

    def setUp(self):
        self.edicion, self.categoria, self.votacion, self.cancion_a, self.cancion_b = (
            crear_escenario()
        )

    def test_creates_voters_and_votes(self):
        from django.core.management import call_command

        call_command('simular_votacion', votantes=5, participacion=80, stdout=io.StringIO())

        padrones = PadronVotante.objects.filter(votacion=self.votacion)
        habilitados = padrones.count()
        votaron = padrones.filter(ha_votado=True).count()

        self.assertEqual(habilitados, 5)  # 5 votantes de demo
        self.assertEqual(votaron, 4)      # 80% de participación
        self.assertEqual(Voto.objects.count(), 4)
        # El voto de demo también deja su comprobante.
        self.assertFalse(
            padrones.filter(ha_votado=True, hash_comprobante__isnull=True).exists()
        )

    def test_nadie_vota_dos_veces(self):
        from django.core.management import call_command

        call_command('simular_votacion', votantes=6, participacion=100, stdout=io.StringIO())
        call_command('simular_votacion', votantes=6, participacion=100, stdout=io.StringIO())

        self.assertEqual(Voto.objects.count(), 6)
        padrones = PadronVotante.objects.filter(votacion=self.votacion, ha_votado=True)
        self.assertEqual(padrones.count(), 6)

    def test_participacion_cero_no_emite_votos(self):
        from django.core.management import call_command

        call_command('simular_votacion', votantes=4, participacion=0, stdout=io.StringIO())

        self.assertEqual(PadronVotante.objects.count(), 4)
        self.assertEqual(Voto.objects.count(), 0)

    def test_sin_votaciones_activas_falla_con_mensaje(self):
        from django.core.management import CommandError, call_command

        self.votacion.estado = 'FINALIZADA'
        self.votacion.save(update_fields=['estado'])

        with self.assertRaises(CommandError):
            call_command('simular_votacion', stdout=io.StringIO())


class AuditoriaLogTests(TestCase):
    """Registro de auditoría: eventos en el flujo y pantalla por rol."""

    def setUp(self):
        from django.core.cache import cache
        from django.core.management import call_command

        from back.apps.auditoria.models import LogAuditoriaEvento
        from back.apps.usuarios.models import Role, Usuario

        cache.clear()
        call_command('cargar_permisos', stdout=io.StringIO())
        self.LogAuditoriaEvento = LogAuditoriaEvento
        self.edicion, self.categoria, self.votacion, self.cancion_a, self.cancion_b = (
            crear_escenario()
        )
        self.user_model = get_user_model()
        self.votante = self.user_model.objects.create_user(
            username='votante-aud', password='voto1234'
        )
        Usuario.objects.create(
            user=self.votante,
            documento='8870111144',
            nombres='Votante',
            apellidos='Auditoría',
            correo='votante-aud@test.com',
            rol=Role.objects.get(nombre='Votante'),
        )
        self.auditor = self.user_model.objects.create_user(
            username='auditor-aud', password='audito1234'
        )
        Usuario.objects.create(
            user=self.auditor,
            documento='8870111155',
            nombres='Auditor',
            apellidos='Prueba',
            correo='auditor-aud@test.com',
            rol=Role.objects.get(nombre='Auditor'),
        )

    def test_el_voto_deja_evento_sin_revelar_la_opcion(self):
        self.client.force_login(self.votante)
        self.client.post(
            reverse('votar', args=[self.votacion.pk]), {'opcion': self.cancion_a.pk}
        )

        evento = self.LogAuditoriaEvento.objects.filter(accion='voto_emitido').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.modulo, 'votacion')
        self.assertEqual(evento.detalles_json['votacion'], self.votacion.pk)
        # El secreto del voto: el evento no menciona la opción elegida.
        self.assertNotIn('opcion', evento.detalles_json)

    def test_login_deja_evento_y_fallo_tambien(self):
        self.client.post(
            reverse('auth:login'),
            {'identificador': self.votante.username, 'password': 'clave-mala'},
        )
        self.assertTrue(
            self.LogAuditoriaEvento.objects.filter(accion='login_fallido').exists()
        )

        self.client.post(
            reverse('auth:login'),
            {'identificador': self.votante.username, 'password': 'voto1234'},
        )
        self.assertTrue(
            self.LogAuditoriaEvento.objects.filter(accion='login').exists()
        )

    def test_el_hash_se_encadena_con_el_evento_anterior(self):
        """La cadena se puede rehacer con los campos guardados de cada fila."""
        import hashlib

        from back.apps.auditoria.servicio import registrar_evento

        registrar_evento(modulo='usuarios', accion='login')
        registrar_evento(modulo='votacion', accion='voto_emitido')

        eventos = list(self.LogAuditoriaEvento.objects.order_by('id')[:2])
        self.assertEqual(len(eventos), 2)
        primero, segundo = eventos

        self.assertNotEqual(
            primero.hash_trazabilidad, segundo.hash_trazabilidad
        )

        # Un tercero puede verificar el segundo evento desde el primero.
        contenido = '|'.join([
            primero.hash_trazabilidad,
            segundo.timestamp.isoformat(),
            segundo.modulo,
            segundo.accion,
            str(segundo.usuario_id or ''),
        ])
        esperado = hashlib.sha256(contenido.encode('utf-8')).hexdigest()
        self.assertEqual(segundo.hash_trazabilidad, esperado)

    def test_pantalla_de_auditoria_por_rol(self):
        # Anónimo: exige inicio de sesión.
        respuesta = self.client.get(reverse('auditoria_lista'))
        self.assertEqual(respuesta.status_code, 302)

        # Votante sin ``auditoria.ver``: 403.
        self.client.force_login(self.votante)
        respuesta = self.client.get(reverse('auditoria_lista'))
        self.assertEqual(respuesta.status_code, 403)

        # Auditor con el permiso: ve la tabla.
        self.client.logout()
        self.client.force_login(self.auditor)
        respuesta = self.client.get(reverse('auditoria_lista'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Registro de auditoría')
