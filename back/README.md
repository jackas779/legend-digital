# Backend Django — Sistema de Votación (MVP)

Backend del sistema de votación. El MVP implementa la jerarquía mínima del
proceso electoral usando **Django puro con MVT** (Model–View–Template), sin
depender del frontend en Vue.

```
Edición → Categoría → Votación → Opción → Voto
Festival 2027 → Música → Canción favorita del público → Canción A / B / C → Voto
```

## Stack

- Python 3.12
- Django 6.1.2
- SQLite (desarrollo)
- Django Templates (MVT) + Django Admin
- Django REST Framework + JWT (API existente, en segundo plano)

## Estructura

```text
proyecto universidad/
├── manage.py
├── requirements.txt
├── modelo_datos.sql
└── back/
    ├── settings.py              # apps, plantillas, JWT, CORS, i18n
    ├── urls.py                  # router raíz: MVT, API y admin
    ├── wsgi.py / asgi.py
    ├── .env.example             # variables de entorno
    ├── templates/
    │   ├── base.html
    │   ├── registration/login.html
    │   └── votacion/
    │       ├── inicio.html
    │       ├── edicion.html
    │       ├── tarjeton.html
    │       └── resultados.html
    └── apps/
        ├── usuarios/            # roles, permisos, perfil
        ├── elecciones/          # Edición, Categoría, Votación, Opción
        ├── votacion/            # Padrón, Voto, certificados, acta
        └── auditoria/           # logs de eventos
```

Las apps se importan como `back.apps.<app>` porque `apps/` vive dentro del
paquete `back/`.

## Modelo de datos del MVP

| Nivel | Modelo | Campos clave |
|---|---|---|
| Edición | `elecciones.Edicion` | `nombre`, `anio`, `estado` (único por nombre+año) |
| Categoría | `elecciones.Categoria` | `nombre` (catálogo global reutilizable) |
| Votación | `elecciones.Votacion` | `edicion`, `categoria`, `nombre`, fechas, `estado` |
| Opción | `elecciones.Opcion` | `votacion`, `nombre`, `subtitulo`, `orden` (casilla única por votación) |
| Voto | `votacion.Voto` | `opcion`, `fecha_registro`, `firma_criptografica` (SHA-256) |

El voto apunta **solo a la opción**: la votación se deriva de ella, así que es
imposible registrar un voto con una opción de otra votación.

`votacion.PadronVotante` garantiza un voto por usuario y votación (único por
`usuario` + `votacion`). Se apoya en `auth.User` para que cualquier usuario de
Django pueda votar sin perfil adicional.

## Instalación

Desde la raíz del repositorio:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copia las variables de entorno (opcional en desarrollo):

```bash
copy back\.env.example .env
```

Variables soportadas: `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`.
La base de datos es SQLite (`db.sqlite3`) y no requiere configuración.

## Puesta en marcha

```bash
python manage.py migrate
python manage.py cargar_demo        # Festival 2027 → Música → Canción favorita
python manage.py createsuperuser    # si aún no tienes uno
python manage.py runserver
```

Luego abre:

- `http://localhost:8000/` — tarjetón público
- `http://localhost:8000/admin/` — panel de administración

`cargar_demo` es idempotente: puedes ejecutarlo varias veces sin duplicar datos.

## Rutas MVT

| Método | Ruta | Vista |
|---|---|---|
| GET | `/` | Listado de ediciones |
| GET | `/ediciones/<id>/` | Categorías y votaciones de la edición |
| GET | `/votaciones/<id>/` | Tarjetón |
| POST | `/votaciones/<id>/votar/` | Registrar voto (requiere sesión) |
| GET | `/votaciones/<id>/resultados/` | Conteo y porcentajes |
| GET | `/accounts/login/` | Inicio de sesión |
| GET | `/registro/` | Crear cuenta de votante |
| — | `/admin/` | Panel de administración |

## Autenticación

- Una sola lógica de acceso para el sitio y la API, en
  `back/apps/usuarios/auth.py`, conectada como backend de Django.
- Se puede iniciar sesión con **correo, nombre de usuario o documento**, en
  ese orden; coincide con las cuentas de prueba del prototipo.
- Bloqueo por intentos fallidos: 5 fallos bloquean la cuenta 15 minutos
  (usa `intentos_fallidos` y `bloqueado_hasta` del perfil).
- Solo entra quien esté `ACTIVO`: un perfil `SUSPENDIDO` o `INACTIVO` queda
  rechazado en la API y en la web.
- El registro ya sea web o por API aplica la política de contraseñas de Django
  (`back/apps/usuarios/services.py`) y rechaza correos o documentos duplicados.

Reglas del flujo de voto:

1. La votación debe estar `ACTIVA` y dentro de sus fechas.
2. La opción debe pertenecer a esa votación.
3. Cada usuario vota una sola vez por votación.
4. El voto se guarda de forma anónima y se firma con SHA-256.

## API REST (existente)

Se mantiene bajo `/api/` para la futura integración con Vue:

| Módulo | Ruta base |
|---|---|
| Usuarios | `/api/usuarios/` (`register`, `login`, `me`, `roles`, `permisos`, `health`) |
| Elecciones | `/api/elecciones/` (`ediciones`, `categorias`, `votaciones`, `opciones`, `normativas`, `multimedia`, `health`) |
| Votación | `/api/votacion/` (`votaciones/<id>/opciones/`, `health`) |
| Auditoría | `/api/auditoria/` (`health`) |

La autenticación de la API es JWT; las vistas MVT usan sesión de Django.

## Pruebas

```bash
python manage.py test
```

Cubren creación de ediciones/votaciones/opciones, tarjetón, registro de voto,
voto duplicado, opción de otra votación, votación cerrada, resultados,
autenticación (correo/usuario/documento, suspendidos y bloqueo por intentos) y
registro de cuentas.

## Migraciones

Las migraciones están versionadas y `db.sqlite3` está en `.gitignore`, así que
un clon limpio se levanta con `python manage.py migrate`.

- `elecciones/0004_modelo_mvp.py`: añade `Votacion.nombre`, convierte `Opcion`
  en tabla hija de `Votacion` y elimina la tabla puente `OpcionVotacion`.
- `votacion/0004_urna_simplificada.py`: reemplaza `VotoUrna` por `Voto` y
  apunta `PadronVotante` a `auth.User`.

## Fuera de alcance del MVP

Certificados QR, actas de escrutinio y normativas ya tienen modelo y panel,
pero su lógica de negocio queda para las siguientes fases.
