# Backend Django — Sistema de Votación (MVP)

Backend del sistema de votación. El MVP implementa la jerarquía mínima del
proceso electoral usando **Django puro con MVT** (Model–View–Template), sin
depender del frontend en Vue.

```
Edición → Categoría → Votación → Opción → Voto
Festival 2027 → Música → Canción favorita del público → Canción A / B / C → Voto
```

## Stack

- Python 3.12+ (probado en 3.14)
- Django 6.1.2 (ver `back/requirements.txt`)
- MySQL 8 con PyMySQL, o SQLite si no hay `DB_PASSWORD`
- Pillow (fotos de candidatos)
- Django Templates (MVT) + Django Admin
- Django REST Framework + JWT (API, en segundo plano)

## Estructura

```text
legend-digital/
├── manage.py
├── .env                        # variables de entorno (en la raíz, no en back/)
├── preparar_windows.bat        # instalación en una máquina nueva (Windows)
├── preparar_linux.sh           # instalación en una máquina nueva (Linux/macOS)
├── media/                      # fotos subidas (fuera de git)
├── front/                      # prototipo Vue (referencia de credenciales)
└── back/
    ├── __init__.py             # registra PyMySQL como conector de MySQL
    ├── requirements.txt        # dependencias congeladas
    ├── settings.py             # apps, plantillas, JWT, CORS, i18n, media
    ├── urls.py                 # router raíz: MVT, API, admin y media
    ├── templates/
    │   ├── base.html, 403.html
    │   ├── gestion/            # ediciones, categorías, votaciones, opciones,
    │   │                       # rondas, empates, inscritos y normativas
    │   ├── auditoria/          # registro, verificación y discrepancias
    │   ├── registration/, usuarios/
    │   └── votacion/           # inicio, edición, tarjetón, resultados, comprobante
    └── apps/
        ├── usuarios/           # roles, permisos (sincronizados en migrate), auth, sesión
        ├── elecciones/         # Edición, Categoría, Votación, Opción
        │   ├── ciclo.py        # ciclo de vida, rondas y resultados (única puerta de estados)
        │   ├── imagenes.py     # validación y recorte de fotos
        │   └── middleware.py   # cambios de estado por fecha en cada petición
        ├── votacion/           # Padrón, Voto, Inscripción, Acta
        │   └── inscripciones.py
        └── auditoria/          # registro encadenado, verificación y discrepancias
```

Las apps se importan como `back.apps.<app>` porque `apps/` vive dentro del
paquete `back/`.

## Modelo de datos del MVP

| Nivel | Modelo | Campos clave |
|---|---|---|
| Edición | `elecciones.Edicion` | `nombre`, `anio`, `fecha_inicio`, `fecha_fin`, `estado` (único por nombre+año) |
| Categoría | `elecciones.Categoria` | `nombre`, `archivada` (catálogo global reutilizable entre ediciones) |
| Votación | `elecciones.Votacion` | `edicion`, `categoria`, `nombre`, fechas (dentro del periodo de la edición), `estado` |
| Opción | `elecciones.Opcion` | `votacion`, `nombre`, `subtitulo`, `orden` (casilla única por votación) |
| Voto | `votacion.Voto` | `opcion`, `fecha_registro`, `firma_criptografica` (SHA-256) |

El voto apunta **solo a la opción**: la votación se deriva de ella, así que es
imposible registrar un voto con una opción de otra votación.

## Ciclo de vida (`elecciones/ciclo.py`)

La edición es el contenedor: tiene un periodo y un ciclo de vida, y nada de
lo que contiene se abre ni recibe votos por fuera de ellos. El estado nunca
se edita a mano (ni en formularios, ni en la API, ni en el admin): solo
cambia por las transiciones de `elecciones/ciclo.py`.

| Edición | Cómo entra | Qué se permite |
|---|---|---|
| BORRADOR | Al crearse o al volver desde PROGRAMADA | Armar todo: categorías, votaciones, opciones, periodo |
| PROGRAMADA | El organizador la programa y pasa la validación | Solo cambiar el nombre y textos |
| ACTIVA | **Automático** en `fecha_inicio` | Votar en las votaciones abiertas |
| CERRANDO (en escrutinio) | **Automático** en `fecha_fin` o cierre anticipado con motivo | Generar actas |
| FINALIZADA | **Automático** cuando todo está ESCRUTADO o CANCELADO | Solo lectura |

Votación: BORRADOR → LISTA (al programar la edición) → ABIERTA (en su fecha,
solo con la edición ACTIVA) → CERRADA → ESCRUTADA (con su acta). Las que
nunca se abrieron pasan a CANCELADA cuando la edición se cierra.

Los cambios por fecha los aplica el middleware `SincronizarEstadosMiddleware`
en cada petición y el comando `python manage.py sincronizar_estados` (para
un cron). Además `Votacion.esta_abierta` revisa las fechas de la votación y
de la edición, así que ningún voto entra fuera de tiempo.

El auditor (`/auditoria/ediciones/`) ve verificaciones automáticas (padrón
contra urna, firmas, votos fuera de horario, actas, votos de no inscritos)
y registra discrepancias; las resuelve el organizador con
`discrepancias.resolver` o, si su rol no tiene ese permiso, el
administrador. Una discrepancia abierta no bloquea la finalización. El
auditor audita el proceso y la urna, no a las personas: en su registro ve
las acciones del equipo de gestión y los ingresos fallidos, no la actividad
de cada votante.

## Quién vota, rondas y resultados

**Modo de participación (por votación):** `LIBRE` (cualquier votante con
cuenta) o `INSCRITOS` (solo quien se inscribió a la edición antes de que
esa votación abriera). Se inscribe el propio votante ("Inscribirme" en la
página de la edición) o el organizador pegando documentos en
`/gestion/ediciones/<id>/inscritos/`. Ejemplo: preselección libre y gran
final solo para inscritos en la misma edición.

**Regla de resultado (por votación):**

| Regla | Qué pasa al escrutar |
|---|---|
| Mayoría simple | Gana quien saque más votos |
| Mayoría absoluta (50 % + 1) | Si nadie la supera, los 2 primeros pasan a la segunda vuelta; si alguien la supera, la segunda vuelta se cancela |
| Clasifican N | Los N primeros pasan a la siguiente ronda |
| + Repetir si gana el blanco | Si el voto en blanco supera el 50 %, la ronda siguiente espera candidatos nuevos |

El voto en blanco cuenta como voto válido (también para el 50 % + 1) pero
nunca gana ni clasifica. La ronda siguiente se configura de antemano (sin
candidatos) y los recibe, con sus fotos, al escrutar la anterior; una
votación que alimenta otra ronda se escruta sola al cerrarse. Un empate en
el punto de corte lo decide el organizador con un fundamento obligatorio.
Unicidad: **un voto por categoría y ronda en cada edición**.

**Resultados:** el conteo por opción es público cuando la votación cierra.
Mientras está abierta solo lo ven el organizador, el auditor y el
administrador (`resultados.ver`); el público ve únicamente la participación
en porcentaje de inscritos (en votaciones "solo inscritos").

**Secreto del voto:** el voto no guarda quién votó, su hora se redondea a
la hora, el comprobante del votante es un código aleatorio (no la firma del
voto) y el registro de auditoría anota "voto emitido" sin identidad.

**Fotos:** cada opción admite una foto (JPG, PNG o WEBP de hasta 2 MB) que
se recorta cuadrada a 600 px en JPEG y se guarda en `media/` (en
desarrollo la sirve Django; en producción, el servidor web).

`votacion.PadronVotante` garantiza **un voto por usuario, categoría y edición**
(único por `usuario` + `edicion` + `categoria`; el padrón guarda copias
desnormalizadas de la jerarquía de la votación). Así, aunque una categoría
tenga varias votaciones (subeventos), votar en el segundo se rechaza. Se
apoya en `auth.User` para que cualquier usuario de Django pueda votar sin
perfil adicional.

## Instalación

Desde la raíz del repositorio:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r back\requirements.txt
```

Copia las variables de entorno **a la raíz** (es donde las lee
`settings.py`):

```bash
copy .env.example .env
```

Variables soportadas: `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` y las de
base de datos (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
Sin `DB_PASSWORD` se usa SQLite (`db.sqlite3`); con ella, MySQL.

## Puesta en marcha en una máquina nueva

Solo se necesitan dos pasos: instalar las dependencias y ejecutar **un
comando que prepara todo** (`migrate` + permisos + escenario demo
(Festival 2027) + cuentas de prueba).

```bash
python -m pip install -r back/requirements.txt
python manage.py preparar
python manage.py runserver
```

`preparar` es idempotente: puedes ejecutarlo varias veces sin duplicar nada.
Si prefieres solo las migraciones, sin datos de prueba, usa
`python manage.py preparar --sin-demo`.

> En una máquina nueva conviene primero crear un entorno virtual
> (`python -m venv .venv`) y usar su `python`. En la raíz del proyecto hay
> además dos scripts que hacen incluso ese paso por ti:
>
> - Windows: `preparar_windows.bat`
> - Linux / macOS: `chmod +x preparar_linux.sh && ./preparar_linux.sh`

Luego abre:

- `http://localhost:8000/` — tarjetón público
- `http://localhost:8000/admin/` — panel de administración

El archivo `db.sqlite3` no se versiona (está en `.gitignore`), así que en una
máquina nueva la base se construye desde cero al ejecutar `preparar`. Si
quieres un superusuario propio para el admin, ejecuta después
`python manage.py createsuperuser`.

## MySQL con Docker (producción de datos)

El desarrollo sigue en SQLite hasta que definas `DB_PASSWORD` en el `.env`
de la raíz: con esa variable con contenido el backend alterna a MySQL
automáticamente (ver `back/settings.py`).

1. Copia la plantilla si no existe: `copy .env.example .env`
2. Rellena `DB_PASSWORD` y `DB_ROOT_PASSWORD` en `.env` (y `DB_NAME`/
   `DB_USER`/`DB_PORT` si tu MySQL no usa los valores por defecto)
3. `preparar` **crea la base de datos automáticamente si no existe**
   (`CREATE DATABASE IF NOT EXISTS` con `utf8mb4`); si ya existe la usa
   tal cual, sin tocar su contenido. Con una BD previa con datos, revisa
   antes que sea la correcta.
4. Levanta el contenedor si lo necesitas (MySQL 8.4, puerto 3306, volumen
   persistente `mysql_data`, juego de caracteres `utf8mb4`):

```bash
docker compose up -d
```

5. Crea las tablas y carga datos demo en MySQL:

```bash
python manage.py preparar
python manage.py runserver
```

El compose se niega a arrancar sin las claves (el `:?` del yml) y Django
levanta con el mismo `.env`, así que no hay configuración duplicada. Verifica
la conexión del contenedor con `docker compose ps` (estado `healthy`).

## Navegación por rol

El menú del encabezado cambia según el rol de quien ingresa (igual que en
el prototipo del front), con la sección activa resaltada. Nadie ve enlaces
de secciones para las que no tiene permiso.

| Rol | Menú |
|---|---|
| Votante | Inicio · Resultados · Mis votos · Mi cuenta |
| Organizador | Ediciones · Categorías · Votaciones · Resultados · Discrepancias · Mi cuenta |
| Auditor | Verificación · Discrepancias · Resultados · Registro · Mi cuenta |
| Administrador | Panel admin · Ediciones · Categorías · Votaciones · Resultados · Discrepancias · Auditoría · Mi cuenta |

Anónimo solo ve **Ingresar** y **Registrarse**.

## Roles y permisos

La autorización usa los modelos `Role` / `Permission` / `RolPermiso` propios
(no los grupos de Django). Los códigos siguen el formato `modulo.accion`
(`ediciones.crear`, `votaciones.eliminar`, …) más códigos especiales; el
catálogo completo queda visible en el admin.

| Código | Qué permite |
|---|---|
| `resultados.ver` | Ver resultados **en vivo** (antes del cierre) |
| `padron.ver` | Consultar el padrón |
| `auditoria.ver` | Ver el registro de auditoría |
| `inscripciones.gestionar` | Inscribir votantes a una edición por lista |
| `discrepancias.ver` / `.reportar` / `.resolver` | Ver, registrar/verificar y resolver discrepancias |

| Rol | Permisos |
|---|---|
| Administrador | Todos |
| Organizador | CRUD de ediciones, categorías, votaciones y opciones; `resultados.ver`, `padron.ver`, `inscripciones.gestionar`, `discrepancias.ver`, `discrepancias.resolver` |
| Votante | Ninguno: vota y ve resultados al cierre |
| Auditor | `resultados.ver`, `padron.ver`, `auditoria.ver`, `discrepancias.ver`, `discrepancias.reportar` |

`migrate` sincroniza el catálogo: los permisos nuevos del código llegan
solos a los roles existentes (solo agrega, nunca quita lo que el
administrador haya ajustado). `cargar_permisos` hace lo mismo y además
crea los roles que falten.

Enforcement:

- **API DRF**: las escrituras de `/api/elecciones/` exigen el permiso del
  módulo (`ediciones.crear`, `opciones.editar`, …); un votante recibe 403.
  Solo los superusuarios evitan la verificación.
- **Panel de Django**: cada ModelAdmin consulta los mismos códigos; el
  Organizador ve elecciones y votación pero no usuarios ni auditoría, y la
  urna (`Voto`) y el padrón son de solo lectura para todos.
- **Gestión MVT** (`/gestion/…`): cada vista exige su permiso con el
  decorador `@requiere_permiso(codigo)` del módulo
  `back/apps/usuarios/permisos.py`; anónimo va al login, sin permiso recibe
  una página 403 que dice qué permiso falta.
- **API de usuarios**: listar roles y permisos exige sesión; crearlos exige
  `usuarios.crear` (administrador).

## Rutas MVT

| Método | Ruta | Vista |
|---|---|---|
| GET | `/` | Listado de ediciones |
| GET | `/ediciones/<id>/` | Categorías y votaciones de la edición |
| GET | `/votaciones/<id>/` | Tarjetón |
| POST | `/votaciones/<id>/votar/` | Registrar voto (**solo rol Votante**) |
| GET | `/votaciones/<id>/resultados/` | Conteo y porcentajes: público al cierre; antes, solo `resultados.ver` |
| GET | `/comprobante/<hash>/` | Comprobante de voto; sin la opción, solo el dueño |
| GET | `/mis-votos/` | Historial del votante con sus comprobantes |
| GET | `/resultados/` | Índice de ediciones (requiere sesión) |
| GET | `/resultados/edicion/<id>/` | Consolidado por edición; conteos de votaciones abiertas solo con `resultados.ver` |
| GET | `/auditoria/ediciones/` | Verificación por edición (`discrepancias.ver`) |
| GET | `/auditoria/discrepancias/` | Bandeja de discrepancias (`discrepancias.ver`) |
| GET | `/accounts/login/` | Inicio de sesión (correo, usuario o documento) |
| POST | `/accounts/logout/` | Cierre de sesión (por POST, con CSRF) |
| GET | `/registro/` | Crear cuenta de votante |
| GET | `/cuenta/password/` | Cambiar contraseña (requiere sesión) |
| GET | `/auditoria/` | Registro de auditoría (`auditoria.ver`) |
| GET | `/gestion/ediciones/` | Gestión de ediciones (`ediciones.ver`) |
| POST | `/gestion/ediciones/nueva/` | Crear edición (`ediciones.crear`) |
| POST | `/gestion/ediciones/<id>/editar/` | Editar edición (`ediciones.editar`) |
| POST | `/gestion/ediciones/<id>/eliminar/` | Eliminar con confirmación (`ediciones.eliminar`) |
| POST | `/gestion/ediciones/<id>/programar/` | Programar (BORRADOR → PROGRAMADA, con validación) |
| POST | `/gestion/ediciones/<id>/desprogramar/` | Volver a borrador (PROGRAMADA → BORRADOR) |
| GET/POST | `/gestion/ediciones/<id>/cerrar/` | Cierre anticipado con motivo (ACTIVA → CERRANDO) |
| POST | `/gestion/ediciones/<id>/escrutar/` | Generar actas de las votaciones CERRADAS |
| POST | `/gestion/categorias/<id>/archivar/` | Archivar / reactivar categoría |
| GET/POST | `/gestion/ediciones/<id>/inscritos/` | Inscritos de la edición y carga por documentos (`inscripciones.gestionar`) |
| GET/POST | `/gestion/votaciones/<id>/ronda-siguiente/` | Configurar la ronda siguiente (edición en borrador) |
| POST | `/gestion/votaciones/<id>/ronda/preparar/` | Ronda tras repetición: con candidatos nuevos → LISTA |
| GET/POST | `/gestion/votaciones/<id>/empate/` | Resolver un empate en el punto de corte |
| GET | `/gestion/votaciones/<id>/normativas/` | Normativas de la votación (se muestran en el tarjetón) |
| POST | `/ediciones/<id>/inscribirme/` | El votante se inscribe a la edición |
| GET | `/gestion/categorias/` | Gestión de categorías (`categorias.ver`) |
| POST | `/gestion/categorias/nueva/` | Crear categoría (`categorias.crear`) |
| POST | `/gestion/categorias/<id>/editar/` | Editar categoría (`categorias.editar`) |
| POST | `/gestion/categorias/<id>/eliminar/` | Eliminar con confirmación (`categorias.eliminar`) |
| GET | `/gestion/votaciones/` | Gestión de votaciones, filtrable por edición y categoría (`votaciones.ver`) |
| POST | `/gestion/votaciones/nueva/` | Crear votación (`votaciones.crear`) |
| POST | `/gestion/votaciones/<id>/editar/` | Editar votación (`votaciones.editar`) |
| POST | `/gestion/votaciones/<id>/abrir/` | Abrir antes de su fecha (LISTA → ABIERTA, edición ACTIVA) |
| POST | `/gestion/votaciones/<id>/cerrar/` | Cerrar (ABIERTA → CERRADA; conserva votos) |
| GET | `/gestion/votaciones/<id>/opciones/` | Opciones de la votación por casilla (`opciones.ver`) |
| POST | `/gestion/votaciones/<id>/opciones/nueva/` | Crear opción (`opciones.crear`) |
| POST | `/gestion/votaciones/<id>/opciones/<oid>/editar/` | Editar opción (`opciones.editar`) |
| POST | `/gestion/votaciones/<id>/opciones/<oid>/eliminar/` | Eliminar opción, bloqueada si tiene votos (`opciones.eliminar`) |
| — | `/admin/` | Panel de administración |

## Usuarios de prueba

Credenciales idénticas a las del prototipo del front
(`front/src/lib/data.js`). Se cargan con
`python manage.py cargar_usuarios_demo` (idempotente) y las claves se
restablecen con `--reset-passwords`.

| Rol | Nombre | Documento | Correo | Clave |
|---|---|---|---|---|
| Administrador | Laura Restrepo | `100200300` | laura.restrepo@uni.edu.co | `admin123` |
| Organizador | Andrés Catalán | `100200301` | andres.catalan@uni.edu.co | `org123` |
| Votante | Cardina Rentería | `1015487962` | cardi.renteria@uni.edu.co | `voto123` |
| Auditor | Martha Lucumí | `100200302` | martha.lucumi@uni.edu.co | `aud123` |
| Votante | Sofía Márquez | `1015987412` | sofia.marquez@uni.edu.co | `voto123` |
| Votante suspendido | Julián Ospina | `1023654789` | julian.ospina@uni.edu.co | `voto123` |

Además, `simular_votacion` (incluido en `preparar`) crea **120 votantes de
demo** con documentos `90XXXXXXXX` y clave `voto123`, y les emite votos en
todas las votaciones abiertas (y en las cerradas pendientes de escrutinio,
fechados dentro de su horario), respetando un voto por categoría y ronda.
En votaciones "solo inscritos" los inscribe antes de la apertura.

Escenario de demo (`cargar_leyenda`, en una base nueva): Festival de la
Leyenda Vallenata 2026 activo, 2025 finalizado (con actas) y 2027
programado con una **preselección libre** donde clasifican 2 y una **gran
final solo para inscritos**.

## Registro de auditoría (logs)

Cada acción relevante queda en la tabla de auditoría
(`logs_auditoria_eventos`), visible en **Django Admin → Auditoría** y en
la pantalla web **/auditoria/** (rol Auditor o Administrador). Cada fila
guarda:

- **Quién**: usuario de la acción (o `sistema` para eventos automáticos,
  como los cambios de estado por fecha). El voto emitido se registra **sin
  usuario ni IP**.
- **Qué**: módulo y acción (`usuarios/login`, `usuarios/login_fallido`,
  `votacion/voto_emitido`, `edicion_programada`, `edicion_activada`,
  `edicion_cerrada(_anticipadamente)`, `votacion_escrutada`,
  `resultado_aplicado`, `inscripcion`, `discrepancia_*`, y
  `creada/actualizada/eliminada` en cada módulo de gestión).
- **Detalles**: por ejemplo la votación donde se emitió el voto. El
  secreto del voto se respeta: el evento **nunca** incluye la opción
  elegida ni quién votó.
- **IP** de origen y fecha/hora.
- **Hash de trazabilidad**: SHA-256 que encadena cada evento con el anterior
  (el primero de la tabla arranca con `GENESIS`). Si alguien altera o
  borra filas, la cadena deja de verificar y queda en evidencia.

Para repetir la simulación tras un `reset_demo`: ejecuta de nuevo
`python manage.py simular_votacion`.

Qué debe ver cada rol al entrar:

- **Administrador**: todo el panel y la gestión completa.
- **Organizador**: gestiona ediciones, categorías, votaciones y opciones.
- **Votante**: el proceso electoral, sus comprobantes y el tarjetón.
- **Auditor**: verifica el proceso y la urna (resultados en vivo,
  verificaciones, discrepancias); en el registro no ve la actividad de
  cada votante; **no emite voto**.

Regla electoral: solo el rol **Votante** emite voto. Las autoridades del
proceso (Administrador, Organizador y Auditor) conservan la consulta de
resultados y padrón pero no emiten voto: el tarjetón se lo indica y el
registro del voto lo rechaza.
- **Julián Ospina** está `SUSPENDIDO`: su intento de sesión se rechaza con
  mensaje claro.

Para repetir el flujo de votación sin recargar todo:
`python manage.py reset_demo --confirmar` borra votos y padrones conservando
ediciones, categorías, votaciones y opciones.

## Autenticación

- Una sola lógica de acceso para el sitio y la API, en
  `back/apps/usuarios/auth.py`, conectada como backend de Django.
- Se puede iniciar sesión con **correo, nombre de usuario o documento**, en
  ese orden; coincide con las cuentas de prueba del prototipo.
- **Destino por rol al entrar (V6)**: Administrador → `/admin/`,
  Organizador → `/gestion/ediciones/`, Votante → inicio, Auditor →
  `/resultados/`. El parámetro `next` seguro tiene prioridad.
- Bloqueo por intentos fallidos: 5 fallos bloquean la cuenta 15 minutos
  (usa `intentos_fallidos` y `bloqueado_hasta` del perfil).
- Solo entra quien esté `ACTIVO`: un perfil `SUSPENDIDO` o `INACTIVO` queda
  rechazado en la API y en la web.
- El registro ya sea web o por API aplica la política de contraseñas de Django
  (`back/apps/usuarios/services.py`) y rechaza correos o documentos duplicados.
- **Sesión (A8)**: muere al cerrar el navegador o tras 30 minutos de
  inactividad; la casilla "Recordarme" del login la extiende a 7 días.
- **Cambio de contraseña (A9)**: `/cuenta/password/` pide la clave actual,
  aplica la misma política y conservar la sesión abierta.
- **Cookies (A10)**: `HttpOnly` y `SameSite=Lax`; en producción
  (`DEBUG=False`) se activan `Secure`, HSTS y redirección a HTTPS.
- **Throttling (A11)**: `POST /api/usuarios/login/` acepta 5 intentos por
  minuto y por IP; el excedente responde 429 sin bloquear otras cuentas.

Reglas del flujo de voto:

1. La votación debe estar `ABIERTA` y dentro de sus fechas, y su edición
   `ACTIVA` y dentro de su periodo.
2. Si la votación es "solo inscritos", el votante debe haberse inscrito a
   la edición antes de su apertura.
3. La opción debe pertenecer a esa votación.
4. Cada usuario emite un solo voto por **categoría y ronda en cada
   edición** (aunque la categoría tenga varios subeventos paralelos).
5. El voto se guarda de forma anónima, con la hora redondeada, y se firma
   con SHA-256; el votante recibe un comprobante aleatorio.

## API REST (existente)

Se mantiene bajo `/api/` para la futura integración con Vue:

| Módulo | Ruta base |
|---|---|
| Categorías públicas | `GET /api/categorias/` (categorías con votaciones y opciones anidadas en JSON; pública sin token, filtrable con `?edicion=<id>`) |
| Usuarios | `/api/usuarios/` (`register`, `login`, `me`, `roles`, `permisos`, `health`) |
| Elecciones | `/api/elecciones/` (`ediciones`, `categorias`, `votaciones`, `opciones`, `normativas`, `multimedia`, `health`) |
| Votación | `/api/votacion/` (`votaciones/<id>/opciones/`, `health`) |
| Auditoría | `/api/auditoria/` (`health`) |

La autenticación de la API es JWT; las vistas MVT usan sesión de Django.

## Pruebas

```bash
python manage.py test back                                   # todo (~3 min en MySQL)
python manage.py test back.apps.elecciones.tests_rondas     # un módulo
```

Crean y borran su propia base de pruebas. Cubren, además de autenticación,
permisos y gestión MVT: ciclo de vida y cambios por fecha
(`elecciones/tests_ciclo.py`), rondas, empates, repetición por voto en
blanco y fotos (`elecciones/tests_rondas.py`), inscripciones y modos de
participación (`votacion/tests_inscripciones.py`), secreto del voto
(comprobante, hora redondeada, registro sin identidad), visibilidad de
resultados en web y API, y verificación y discrepancias del auditor
(`auditoria/tests.py`).

## Migraciones

Las migraciones están versionadas, así que un clon limpio se levanta con
`python manage.py migrate` (que además sincroniza los permisos).

- `elecciones/0004_modelo_mvp.py`: añade `Votacion.nombre`, convierte `Opcion`
  en tabla hija de `Votacion` y elimina la tabla puente `OpcionVotacion`.
- `votacion/0004_urna_simplificada.py`: reemplaza `VotoUrna` por `Voto` y
  apunta `PadronVotante` a `auth.User`.
- `elecciones/0005_ciclo_de_vida_edicion.py`: periodo de la edición y
  estados propios de la votación (traslada los datos existentes).
- `elecciones/0006_rondas_reglas_y_fotos.py`: modo de participación, regla
  de resultado, rondas y foto de la opción.
- `votacion/0006`–`0009`: padrón con edición, categoría y ronda
  obligatorias, inscripciones, y **secreto del voto sobre los datos
  existentes** (comprobantes nuevos, horas redondeadas, sellos de acta
  recalculados; es irreversible a propósito).
- `usuarios/0003_votante_sin_resultados_en_vivo.py`: quita `resultados.ver`
  al votante en bases existentes.

## Fuera de alcance del MVP

- Certificados con QR: el modelo existe pero no se generan.
- El acta de escrutinio se genera con totales y sello, pero sin PDF.
- Un solo voto por persona y votación: no hay voto múltiple ni preferencial.
