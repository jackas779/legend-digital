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


class GestionEdicionesTests(TestCase):
    """Entregables ED1-ED4: gestión MVT de ediciones con permisos."""

    def setUp(self):
        from django.core.cache import cache
        from django.core.management import call_command
        from django.contrib.auth import get_user_model

        from back.apps.usuarios.models import Role, Usuario

        cache.clear()
        call_command('cargar_permisos', stdout=io.StringIO())
        self.rol_organizador = Role.objects.get(nombre='Organizador')
        self.rol_votante = Role.objects.get(nombre='Votante')
        self.user_model = get_user_model()

    def _sesion(self, rol):
        """Crea un usuario real y lo deja con sesión iniciada."""
        zeros = int(rol.id)
        user = self.user_model.objects.create_user(
            username=f'gestor-{rol.nombre.lower()}', password='clave-test-2026'
        )
        Usuario.objects.create(
            user=user,
            documento=f'88{zeros:08d}',
            nombres='Gestor',
            apellidos='Prueba',
            correo=f'gestor-{rol.nombre.lower()}@test.com',
            rol=rol,
        )
        self.client.force_login(user)
        return user

    def _edicion(self, nombre='Festival', anio=2027, **extra):
        from back.apps.elecciones.models import Edicion

        return Edicion.objects.create(nombre=nombre, anio=anio, **extra)

    def test_anonimo_redirige_al_login(self):
        respuesta = self.client.get(reverse('gestion:ediciones'))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/accounts/login/', respuesta['Location'])

    def test_votante_recibe_403(self):
        self._sesion(self.rol_votante)

        respuesta = self.client.get(reverse('gestion:ediciones'))

        self.assertEqual(respuesta.status_code, 403)

    def test_listado_muestra_estado_y_votaciones(self):
        self._sesion(self.rol_organizador)
        self._edicion(estado='ACTIVA')

        respuesta = self.client.get(reverse('gestion:ediciones'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Festival 2027')
        self.assertContains(respuesta, 'ACTIVA')
        primera = respuesta.context['ediciones'].first()
        self.assertEqual(primera.num_votaciones, 0)

    def test_crear_edicion_valida(self):
        self._sesion(self.rol_organizador)

        respuesta = self.client.post(
            reverse('gestion:edicion_crear'),
            {'nombre': 'Festival', 'anio': 2027, 'estado': 'BORRADOR'},
        )

        self.assertRedirects(respuesta, reverse('gestion:ediciones'))
        from back.apps.elecciones.models import Edicion

        self.assertTrue(Edicion.objects.filter(nombre='Festival', anio=2027).exists())

    def test_nombre_y_anio_duplicado_da_error_en_formulario(self):
        self._sesion(self.rol_organizador)
        self._edicion()

        respuesta = self.client.post(
            reverse('gestion:edicion_crear'),
            {'nombre': 'Festival', 'anio': 2027, 'estado': 'BORRADOR'},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors['nombre'])

    def test_editar_edicion(self):
        self._sesion(self.rol_organizador)
        edicion = self._edicion()

        respuesta = self.client.post(
            reverse('gestion:edicion_editar', args=[edicion.id]),
            {'nombre': 'Festival de Invierno', 'anio': 2027, 'estado': 'BORRADOR'},
        )

        self.assertRedirects(respuesta, reverse('gestion:ediciones'))
        edicion.refresh_from_db()
        self.assertEqual(edicion.nombre, 'Festival de Invierno')

    def test_eliminar_con_confirmacion(self):
        self._sesion(self.rol_organizador)
        edicion = self._edicion()

        confirmacion = self.client.get(
            reverse('gestion:edicion_eliminar', args=[edicion.id])
        )
        self.assertEqual(confirmacion.status_code, 200)
        self.assertContains(confirmacion, 'Confirmas')

        borrado = self.client.post(reverse('gestion:edicion_eliminar', args=[edicion.id]))
        self.assertRedirects(borrado, reverse('gestion:ediciones'))

        from back.apps.elecciones.models import Edicion

        self.assertFalse(Edicion.objects.filter(pk=edicion.id).exists())

    def test_no_deja_eliminar_mientras_haya_votos(self):
        from datetime import timedelta

        from django.utils import timezone

        from back.apps.elecciones.models import Categoria, Edicion, Opcion, Votacion
        from back.apps.votacion.models import Voto

        self._sesion(self.rol_organizador)
        edicion = self._edicion(estado='ACTIVA')
        categoria = Categoria.objects.create(nombre='Música')
        votacion = Votacion.objects.create(
            edicion=edicion,
            categoria=categoria,
            nombre='Canción favorita',
            estado='ACTIVA',
            fecha_apertura=timezone.now() - timedelta(days=1),
            fecha_cierre=timezone.now() + timedelta(days=1),
        )
        opcion = Opcion.objects.create(votacion=votacion, nombre='Canción A', orden=1)
        Voto.objects.create(opcion=opcion)

        bloqueado = self.client.post(
            reverse('gestion:edicion_eliminar', args=[edicion.id])
        )

        self.assertRedirects(bloqueado, reverse('gestion:ediciones'))
        self.assertTrue(Edicion.objects.filter(pk=edicion.id).exists())

    def test_finalizar_sin_regreso(self):
        self._sesion(self.rol_organizador)
        edicion = self._edicion(estado='ACTIVA')

        respuesta = self.client.post(
            reverse('gestion:edicion_finalizar', args=[edicion.id]),
        )
        self.assertRedirects(respuesta, reverse('gestion:ediciones'))
        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'FINALIZADA')

        # Publicar sobre FINALIZADA no cambia nada (ED4).
        respuesta = self.client.post(
            reverse('gestion:edicion_publicar', args=[edicion.id]),
        )
        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'FINALIZADA')

    def test_publicar_borrador(self):
        self._sesion(self.rol_organizador)
        edicion = self._edicion(estado='BORRADOR')

        respuesta = self.client.post(
            reverse('gestion:edicion_publicar', args=[edicion.id]),
        )

        self.assertRedirects(respuesta, reverse('gestion:ediciones'))
        edicion.refresh_from_db()
        self.assertEqual(edicion.estado, 'ACTIVA')


class GestionCategoriasTests(TestCase):
    """Entregables CA1-CA3: gestión MVT de categorías con permisos."""

    def setUp(self):
        from django.core.cache import cache
        from django.core.management import call_command
        from django.contrib.auth import get_user_model

        from back.apps.usuarios.models import Role, Usuario

        cache.clear()
        call_command('cargar_permisos', stdout=io.StringIO())
        self.rol_organizador = Role.objects.get(nombre='Organizador')
        self.rol_votante = Role.objects.get(nombre='Votante')
        self.user_model = get_user_model()

        user = self.user_model.objects.create_user(
            username='organizador-gestion', password='clave-test-2026'
        )
        Usuario.objects.create(
            user=user,
            documento='8810000001',
            nombres='Organizador',
            apellidos='Prueba',
            correo='organizador-gestion@test.com',
            rol=self.rol_organizador,
        )
        self.client.force_login(user)

    def test_votante_recibe_403(self):
        zeros = int(self.rol_votante.id)
        votante = self.user_model.objects.create_user(
            username='votante-gestion', password='clave-test-2026'
        )
        Usuario.objects.create(
            user=votante,
            documento=f'88{zeros:08d}',
            nombres='Votante',
            apellidos='Prueba',
            correo='votante-gestion@test.com',
            rol=self.rol_votante,
        )
        self.client.force_login(votante)

        respuesta = self.client.get(reverse('gestion:categorias'))

        self.assertEqual(respuesta.status_code, 403)

    def test_listado_cuenta_usos(self):
        from back.apps.elecciones.models import Categoria

        categoria = Categoria.objects.create(nombre='Música')

        respuesta = self.client.get(reverse('gestion:categorias'))

        self.assertEqual(respuesta.status_code, 200)
        anotada = [c for c in respuesta.context['categorias'] if c.pk == categoria.pk][0]
        self.assertEqual(anotada.num_votaciones, 0)

    def test_crear_y_duplicado_en_formulario(self):
        from back.apps.elecciones.models import Categoria

        self.client.post(
            reverse('gestion:categoria_crear'),
            {'nombre': 'Música', 'descripcion': ''},
        )
        self.assertTrue(Categoria.objects.filter(nombre='Música').exists())

        dup = self.client.post(
            reverse('gestion:categoria_crear'),
            {'nombre': 'Música', 'descripcion': ''},
        )
        self.assertEqual(dup.status_code, 200)
        self.assertTrue(dup.context['form'].errors['nombre'])
        self.assertEqual(Categoria.objects.count(), 1)

    def test_no_deja_eliminar_si_esta_en_uso(self):
        from datetime import timedelta

        from django.utils import timezone

        from back.apps.elecciones.models import Categoria, Edicion, Votacion

        categoria = Categoria.objects.create(nombre='Música')
        edicion = Edicion.objects.create(nombre='Festival', anio=2027)
        Votacion.objects.create(
            edicion=edicion,
            categoria=categoria,
            nombre='Canción favorita',
            estado='ACTIVA',
            fecha_apertura=timezone.now() - timedelta(days=1),
            fecha_cierre=timezone.now() + timedelta(days=1),
        )

        bloqueado = self.client.post(
            reverse('gestion:categoria_eliminar', args=[categoria.id])
        )

        self.assertRedirects(bloqueado, reverse('gestion:categorias'))
        self.assertTrue(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_elimina_cuando_esta_libre(self):
        from back.apps.elecciones.models import Categoria

        categoria = Categoria.objects.create(nombre='Literatura')

        respuesta = self.client.post(
            reverse('gestion:categoria_eliminar', args=[categoria.id]),
        )

        self.assertRedirects(respuesta, reverse('gestion:categorias'))
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())


class GestionVotacionesTests(TestCase):
    """Entregables VO1-VO5: gestión MVT de votaciones."""

    def setUp(self):
        from datetime import timedelta

        from django.core.cache import cache
        from django.core.management import call_command
        from django.utils import timezone

        from back.apps.elecciones.models import Categoria, Edicion
        from django.contrib.auth import get_user_model

        from back.apps.usuarios.models import Role, Usuario

        cache.clear()
        call_command('cargar_permisos', stdout=io.StringIO())

        self.edicion = Edicion.objects.create(nombre='Festival', anio=2027)
        self.otra_edicion = Edicion.objects.create(nombre='Congreso', anio=2028)
        self.categoria = Categoria.objects.create(nombre='Música')
        self.rol_organizador = Role.objects.get(nombre='Organizador')
        self.rol_votante = Role.objects.get(nombre='Votante')

        self.user_model = get_user_model()
        user = self.user_model.objects.create_user(
            username='organizador-votes', password='clave-test-2026'
        )
        Usuario.objects.create(
            user=user,
            documento='8809000001',
            nombres='Organizador',
            apellidos='Prueba',
            correo='organizador-votes@test.com',
            rol=self.rol_organizador,
        )
        self.client.force_login(user)

        self.ahora = timezone.now()
        self.delta = timedelta(days=1)
        self.datos_base = {
            'edicion': self.edicion.id,
            'categoria': self.categoria.id,
            'nombre': 'Canción favorita',
            'fecha_apertura': (self.ahora - self.delta).strftime('%Y-%m-%dT%H:%M'),
            'fecha_cierre': (self.ahora + self.delta).strftime('%Y-%m-%dT%H:%M'),
            'estado': 'ACTIVA',
        }

    def _votacion(self, **extra):
        from django.utils import timezone
        from datetime import timedelta

        from back.apps.elecciones.models import Votacion

        datos = {
            'edicion': self.edicion,
            'categoria': self.categoria,
            'nombre': 'Canción favorita',
            'fecha_apertura': timezone.now() - timedelta(days=1),
            'fecha_cierre': timezone.now() + timedelta(days=1),
        }
        datos.update(extra)
        return Votacion.objects.create(**datos)

    def test_votante_recibe_403(self):
        zeros = int(self.rol_votante.id)
        votante = self.user_model.objects.create_user(
            username='votante-votes', password='clave-test-2026'
        )
        Usuario.objects.create(
            user=votante,
            documento=f'88{zeros:08d}',
            nombres='Votante',
            apellidos='Prueba',
            correo='votante-votes@test.com',
            rol=self.rol_votante,
        )
        self.client.force_login(votante)

        respuesta = self.client.get(reverse('gestion:votaciones'))

        self.assertEqual(respuesta.status_code, 403)

    def test_listado_filtra_por_edicion_y_categoria(self):
        self._votacion(nombre='A de musica')
        self._votacion(edicion=self.otra_edicion, nombre='B de musica')
        self._votacion(nombre='C de otra', edicion=self.edicion)

        respuesta = self.client.get(
            reverse('gestion:votaciones'),
            {'edicion': self.otra_edicion.id, 'categoria': self.categoria.id},
        )

        self.assertEqual(respuesta.status_code, 200)
        nombres = [v.nombre for v in respuesta.context['votaciones']]
        self.assertEqual(nombres, ['B de musica'])

    def test_listado_muestra_total_de_votos(self):
        from back.apps.elecciones.models import Opcion
        from back.apps.votacion.models import Voto

        votacion = self._votacion()
        opcion = Opcion.objects.create(votacion=votacion, nombre='Canción A', orden=1)
        Voto.objects.create(opcion=opcion)

        respuesta = self.client.get(reverse('gestion:votaciones'))

        anotada = [v for v in respuesta.context['votaciones'] if v.pk == votacion.pk][0]
        self.assertEqual(anotada.num_votos, 1)

    def test_crear_votacion_valida(self):
        respuesta = self.client.post(
            reverse('gestion:votacion_crear'), self.datos_base
        )

        self.assertRedirects(respuesta, reverse('gestion:votaciones'))
        from back.apps.elecciones.models import Votacion

        self.assertTrue(
            Votacion.objects.filter(nombre='Canción favorita', edicion=self.edicion).exists()
        )

    def test_nombre_unico_por_edicion_y_categoria(self):
        self._votacion()

        # Misma edición y categoría: rechaza el duplicado en el formulario.
        duplicada = self.client.post(
            reverse('gestion:votacion_crear'), self.datos_base
        )
        self.assertEqual(duplicada.status_code, 200)
        self.assertTrue(duplicada.context['form'].errors['nombre'])

        # Otra edición admite el mismo nombre (la clave es edición+categoría).
        ok = self.client.post(
            reverse('gestion:votacion_crear'),
            {**self.datos_base, 'edicion': self.otra_edicion.id, 'nombre': 'Canción favorita'},
        )
        self.assertRedirects(ok, reverse('gestion:votaciones'))

    def test_fechas_apertura_menor_que_cierre(self):
        respuesta = self.client.post(
            reverse('gestion:votacion_crear'),
            {
                **self.datos_base,
                'fecha_apertura': self.datos_base['fecha_cierre'],
                'fecha_cierre': self.datos_base['fecha_apertura'],
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors['fecha_cierre'])

    def test_editar_votacion(self):
        votacion = self._votacion()

        respuesta = self.client.post(
            reverse('gestion:votacion_editar', args=[votacion.id]),
            {
                **self.datos_base,
                'nombre': 'Canción del público',
            },
        )

        self.assertRedirects(respuesta, reverse('gestion:votaciones'))
        votacion.refresh_from_db()
        self.assertEqual(votacion.nombre, 'Canción del público')

    def test_abrir_y_no_reabrir_finalizada(self):
        votacion = self._votacion(estado='BORRADOR')

        self.client.post(reverse('gestion:votacion_abrir', args=[votacion.id]))
        votacion.refresh_from_db()
        self.assertEqual(votacion.estado, 'ACTIVA')

        self.client.post(reverse('gestion:votacion_cerrar', args=[votacion.id]))
        votacion.refresh_from_db()
        self.assertEqual(votacion.estado, 'FINALIZADA')

        self.client.post(reverse('gestion:votacion_abrir', args=[votacion.id]))
        votacion.refresh_from_db()
        self.assertEqual(votacion.estado, 'FINALIZADA')

    def test_cerrar_no_borra_votos(self):
        from back.apps.elecciones.models import Opcion
        from back.apps.votacion.models import Voto

        votacion = self._votacion(estado='ACTIVA')
        opcion = Opcion.objects.create(votacion=votacion, nombre='Canción A', orden=1)
        Voto.objects.create(opcion=opcion)

        respuesta = self.client.post(reverse('gestion:votacion_cerrar', args=[votacion.id]))

        self.assertRedirects(respuesta, reverse('gestion:votaciones'))
        votacion.refresh_from_db()
        self.assertEqual(votacion.estado, 'FINALIZADA')
        self.assertEqual(Voto.objects.count(), 1)

    def test_fuera_de_rango_no_se_vota(self):
        from datetime import timedelta

        from django.utils import timezone

        from back.apps.elecciones.models import Opcion
        from django.contrib.auth import get_user_model

        from back.apps.usuarios.models import Usuario

        # VO4: estado ACTIVA pero la ventana ya terminó; no se permite votar.
        votacion = self._votacion(
            estado='ACTIVA',
            fecha_apertura=timezone.now() - timedelta(days=2),
            fecha_cierre=timezone.now() - timedelta(days=1),
        )
        Opcion.objects.create(votacion=votacion, nombre='Canción A', orden=1)

        votante = self.user_model.objects.create_user(
            username='votante-rango', password='voto1234'
        )
        Usuario.objects.create(
            user=votante,
            documento='8809000009',
            nombres='Votante',
            apellidos='Prueba',
            correo='votante-rango@test.com',
            rol=self.rol_votante,
        )
        self.client.force_login(votante)

        respuesta = self.client.post(
            reverse('votar', args=[votacion.id]), {'opcion': 1}
        )

        self.assertRedirects(respuesta, reverse('tarjeton', args=[votacion.id]))
        from back.apps.votacion.models import Voto

        self.assertEqual(Voto.objects.count(), 0)


class GestionOpcionesTests(TestCase):
    """Entregables OP1-OP4: opciones dentro de una votación."""

    def setUp(self):
        from datetime import timedelta

        from django.core.cache import cache
        from django.core.management import call_command
        from django.contrib.auth import get_user_model
        from django.utils import timezone

        from back.apps.elecciones.models import Categoria, Edicion, Votacion
        from back.apps.usuarios.models import Role, Usuario

        cache.clear()
        call_command('cargar_permisos', stdout=io.StringIO())

        self.rol_organizador = Role.objects.get(nombre='Organizador')
        edicion = Edicion.objects.create(nombre='Festival', anio=2027)
        categoria = Categoria.objects.create(nombre='Música')
        self.votacion = Votacion.objects.create(
            edicion=edicion,
            categoria=categoria,
            nombre='Canción favorita',
            estado='ACTIVA',
            fecha_apertura=timezone.now() - timedelta(days=1),
            fecha_cierre=timezone.now() + timedelta(days=1),
        )

        self.user_model = get_user_model()
        user = self.user_model.objects.create_user(
            username='organizador-opc', password='clave-test-2026'
        )
        Usuario.objects.create(
            user=user,
            documento='8809000055',
            nombres='Organizador',
            apellidos='Prueba',
            correo='organizador-opc@test.com',
            rol=self.rol_organizador,
        )
        self.client.force_login(user)

    def _opcion(self, nombre='Canción A', orden=1, **extra):
        from back.apps.elecciones.models import Opcion

        return Opcion.objects.create(votacion=self.votacion, nombre=nombre, orden=orden, **extra)

    def test_listado_ordenado_por_casilla(self):
        self._opcion(nombre='Canción B', orden=2)
        self._opcion(nombre='Canción C', orden=3)
        self._opcion(nombre='Canción A', orden=1)

        respuesta = self.client.get(
            reverse('gestion:opcion_lista', args=[self.votacion.id])
        )

        self.assertEqual(respuesta.status_code, 200)
        nombres = [o.nombre for o in respuesta.context['opciones']]
        self.assertEqual(nombres, ['Canción A', 'Canción B', 'Canción C'])

    def test_crear_opcion(self):
        respuesta = self.client.post(
            reverse('gestion:opcion_crear', args=[self.votacion.id]),
            {'nombre': 'Canción X', 'orden': 1, 'subtitulo': 'Nuevo artista'},
        )

        self.assertRedirects(
            respuesta,
            reverse('gestion:opcion_lista', args=[self.votacion.id]),
        )
        from back.apps.elecciones.models import Opcion

        self.assertTrue(
            Opcion.objects.filter(votacion=self.votacion, nombre='Canción X').exists()
        )

    def test_orden_unico_por_votacion(self):
        self._opcion(orden=1)

        repetida = self.client.post(
            reverse('gestion:opcion_crear', args=[self.votacion.id]),
            {'nombre': 'Canción B', 'orden': 1, 'subtitulo': ''},
        )

        self.assertEqual(repetida.status_code, 200)
        self.assertTrue(repetida.context['form'].errors['orden'])

    def test_mismo_orden_en_otra_votacion_es_valido(self):
        from datetime import timedelta

        from django.utils import timezone

        from back.apps.elecciones.models import Edicion, Opcion, Votacion

        self._opcion(orden=1)

        categoria = self.votacion.categoria
        otra = Votacion.objects.create(
            edicion=Edicion.objects.first(),
            categoria=categoria,
            nombre='Otra votación',
            estado='BORRADOR',
            fecha_apertura=timezone.now() + timedelta(days=1),
            fecha_cierre=timezone.now() + timedelta(days=2),
        )

        respuesta = self.client.post(
            reverse('gestion:opcion_crear', args=[otra.id]),
            {'nombre': 'Otra canción', 'orden': 1, 'subtitulo': ''},
        )

        self.assertRedirects(respuesta, reverse('gestion:opcion_lista', args=[otra.id]))

    def test_editar_opcion(self):
        opcion = self._opcion()

        respuesta = self.client.post(
            reverse('gestion:opcion_editar', args=[self.votacion.id, opcion.id]),
            {'nombre': 'Canción A (regrabada)', 'orden': 1, 'subtitulo': 'Remix'},
        )

        self.assertRedirects(
            respuesta,
            reverse('gestion:opcion_lista', args=[self.votacion.id]),
        )
        opcion.refresh_from_db()
        self.assertEqual(opcion.nombre, 'Canción A (regrabada)')

    def test_no_deja_eliminar_opcion_con_votos(self):
        from back.apps.elecciones.models import Opcion
        from back.apps.votacion.models import Voto

        opcion = self._opcion()
        Voto.objects.create(opcion=opcion)

        bloqueado = self.client.post(
            reverse('gestion:opcion_eliminar', args=[self.votacion.id, opcion.id])
        )

        self.assertRedirects(
            bloqueado,
            reverse('gestion:opcion_lista', args=[self.votacion.id]),
        )
        self.assertTrue(Opcion.objects.filter(pk=opcion.pk).exists())
        self.assertEqual(Voto.objects.count(), 1)

    def test_elimina_opcion_libre(self):
        opcion = self._opcion()

        respuesta = self.client.post(
            reverse('gestion:opcion_eliminar', args=[self.votacion.id, opcion.id])
        )

        self.assertRedirects(
            respuesta,
            reverse('gestion:opcion_lista', args=[self.votacion.id]),
        )
        from back.apps.elecciones.models import Opcion

        self.assertFalse(Opcion.objects.filter(pk=opcion.pk).exists())

    def test_votante_no_gestiona_opciones(self):
        from back.apps.usuarios.models import Role, Usuario

        rol_votante = Role.objects.get(nombre='Votante')
        votante = self.user_model.objects.create_user(
            username='votante-opc', password='clave-test-2026'
        )
        Usuario.objects.create(
            user=votante,
            documento=f'88{int(rol_votante.id):08d}',
            nombres='Votante',
            apellidos='Prueba',
            correo='votante-opc@test.com',
            rol=rol_votante,
        )
        self.client.force_login(votante)

        respuesta = self.client.get(
            reverse('gestion:opcion_lista', args=[self.votacion.id])
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_inline_admin_sigue_disponible(self):
        """OP4: el inline de opciones se mantiene como vía alterna."""
        from django.contrib import admin as admin_site

        from back.apps.elecciones.admin import VotacionAdmin

        inline_context = VotacionAdmin(self.votacion.__class__, admin_site.site).inlines
        from back.apps.elecciones.models import Opcion

        self.assertIn(
            [i for i in inline_context if i.model == Opcion][0].model,
            (Opcion,),
        )
