"""Dispara solicitudes de voto simultáneas contra el servidor en ejecución.

Sirve como evidencia de CP-09: un mismo votante envía N veces el tarjetón
al mismo instante (como un doble clic o varias pestañas) y el sistema
registra un solo voto. Necesita el servidor encendido:

    python manage.py runserver
    python manage.py probar_concurrencia --usuario cardi.renteria --password voto123

Al final consulta la base de datos (MySQL si .env la define) para mostrar
cuántos votos y cuántas marcas de padrón quedaron.
"""

import http.cookiejar
import re
import threading
import time
import urllib.parse
import urllib.request
from html import unescape

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from back.apps.elecciones.models import Votacion
from back.apps.votacion.models import PadronVotante, Voto

PATRON_TOKEN = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')
PATRON_MENSAJE = re.compile(r'<li class="msg ([^"]*)">(.*?)</li>', re.S)


class Command(BaseCommand):
    help = 'Envía votos simultáneos de un mismo votante y comprueba que solo cuente uno.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--usuario', default='cardi.renteria')
        parser.add_argument('--password', default='voto123')
        parser.add_argument('--hilos', type=int, default=10)
        parser.add_argument('--base', default='http://127.0.0.1:8000')
        parser.add_argument('--votacion', type=int, help='Id de la votación (por defecto, la primera abierta sin voto).')

    def handle(self, *args, **opciones):
        base = opciones['base'].rstrip('/')
        user = get_user_model().objects.filter(username=opciones['usuario']).first()
        if not user:
            raise CommandError(f'No existe el usuario {opciones["usuario"]}.')

        votacion = self._elegir_votacion(user, opciones['votacion'])
        opcion = votacion.opciones.order_by('orden').first()

        votos_antes = Voto.objects.filter(opcion__votacion=votacion).count()

        cookies = self._iniciar_sesion(base, opciones['usuario'], opciones['password'])
        token = next(c.value for c in cookies if c.name == 'csrftoken')

        self.stdout.write(self.style.MIGRATE_HEADING('Prueba de solicitudes simultáneas'))
        self.stdout.write(f'  Base de datos : {connection.vendor} ({connection.settings_dict["NAME"]})')
        self.stdout.write(f'  Votante       : {user.username}')
        self.stdout.write(f'  Votación      : #{votacion.pk} {votacion.nombre} ({votacion.edicion})')
        self.stdout.write(f'  Opción        : {opcion.nombre}')
        self.stdout.write(f'  Solicitudes   : {opciones["hilos"]} al mismo instante\n')

        resultados = [None] * opciones['hilos']
        barrera = threading.Barrier(opciones['hilos'])
        url = f'{base}/votaciones/{votacion.pk}/votar/'
        cuerpo = urllib.parse.urlencode(
            {'opcion': opcion.pk, 'csrfmiddlewaretoken': token}
        ).encode()

        def enviar(i):
            # Cada hilo copia las cookies de la sesión: misma persona,
            # peticiones independientes.
            jar = http.cookiejar.CookieJar()
            for c in cookies:
                jar.set_cookie(c)
            abridor = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
            peticion = urllib.request.Request(url, data=cuerpo, headers={'Referer': url})
            barrera.wait()
            inicio = time.perf_counter()
            try:
                html = abridor.open(peticion, timeout=30).read().decode('utf-8', 'replace')
                mensajes = PATRON_MENSAJE.findall(html)
                tipo, texto = mensajes[-1] if mensajes else ('?', '(sin mensaje)')
            except Exception as error:  # noqa: BLE001 - se reporta tal cual
                tipo, texto = 'error', str(error)
            resultados[i] = (tipo, unescape(re.sub(r'\s+', ' ', texto)).strip(), time.perf_counter() - inicio)

        hilos = [threading.Thread(target=enviar, args=(i,)) for i in range(opciones['hilos'])]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        for i, (tipo, texto, segundos) in enumerate(resultados, 1):
            estilo = self.style.SUCCESS if 'success' in tipo else self.style.WARNING
            self.stdout.write(estilo(f'  Solicitud {i:>2} ({segundos * 1000:5.0f} ms): {texto}'))

        votos_despues = Voto.objects.filter(opcion__votacion=votacion).count()
        marcas = PadronVotante.objects.filter(
            usuario=user, edicion=votacion.edicion, categoria=votacion.categoria, ha_votado=True
        ).count()
        aceptadas = sum('success' in r[0] for r in resultados)

        self.stdout.write('')
        self.stdout.write(f'  Solicitudes aceptadas          : {aceptadas}')
        self.stdout.write(f'  Votos nuevos en la urna        : {votos_despues - votos_antes}')
        self.stdout.write(f'  Marcas de padrón en la categoría: {marcas}')
        if aceptadas == 1 and votos_despues - votos_antes == 1 and marcas == 1:
            self.stdout.write(self.style.SUCCESS('\n  OK: solo se registró un voto.'))
        else:
            self.stdout.write(self.style.ERROR('\n  Revisar: el resultado no es un único voto.'))

    def _elegir_votacion(self, user, votacion_id):
        votadas = PadronVotante.objects.filter(usuario=user, ha_votado=True).values_list(
            'edicion_id', 'categoria_id'
        )
        votadas = set(votadas)
        candidatas = Votacion.objects.filter(estado='ACTIVA').select_related('edicion', 'categoria')
        if votacion_id:
            candidatas = candidatas.filter(pk=votacion_id)
        # El Festival de la Leyenda Vallenata va primero: es el proceso principal.
        candidatas = sorted(
            candidatas, key=lambda v: ('Leyenda' not in v.edicion.nombre, -v.edicion.anio, v.pk)
        )
        for v in candidatas:
            if v.esta_abierta and v.opciones.exists() and (v.edicion_id, v.categoria_id) not in votadas:
                return v
        raise CommandError(
            'El votante ya votó en todas las categorías abiertas. Usa otro --usuario '
            '(p. ej. cardi.renteria) o vuelve a ejecutar "preparar" sobre una base limpia.'
        )

    def _iniciar_sesion(self, base, usuario, password):
        jar = http.cookiejar.CookieJar()
        abridor = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        login = f'{base}/accounts/login/'
        try:
            html = abridor.open(login, timeout=10).read().decode()
        except OSError as error:
            raise CommandError(f'No responde {base}. ¿Está corriendo "python manage.py runserver"? ({error})')
        token = PATRON_TOKEN.search(html).group(1)
        datos = urllib.parse.urlencode(
            {'identificador': usuario, 'password': password, 'csrfmiddlewaretoken': token}
        ).encode()
        respuesta = abridor.open(urllib.request.Request(login, data=datos, headers={'Referer': login}))
        if respuesta.geturl().rstrip('/').endswith('/accounts/login'):
            raise CommandError('No se pudo iniciar sesión: revisa usuario y contraseña.')
        return list(jar)
