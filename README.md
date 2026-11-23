# Sistema de Votación Web Seguro

Plataforma de votación digital para procesos electorales de cualquier tipo:
desde un festival (Leyenda Vallenata) hasta elecciones con segunda vuelta.
Gestiona ediciones, categorías, votaciones con rondas, candidatos con foto,
inscripción de votantes, escrutinio con actas y auditoría, con el voto
siempre secreto.

## Conceptos

```text
Edición  (Festival de la Leyenda Vallenata 2026)   ← periodo y ciclo de vida
 └─ Votación  (Rey Vallenato 2026)                 ← une una edición con una categoría
     ├─ Opción  (candidatos con foto + voto en blanco)
     │   └─ Voto  (anónimo)
     ├─ Padrón  (quién votó, nunca por quién)
     └─ Acta de escrutinio

Categoría  (Rey Vallenato, Piqueria…)  ← catálogo global, se reutiliza entre ediciones
```

- **Edición:** el contenedor. Tiene un periodo y un ciclo de vida
  (Borrador → Programada → Activa → En escrutinio → Finalizada) que avanza
  solo por fechas; cuando termina, todo lo de adentro termina con ella.
- **Votación:** puede ser **libre** o **solo para inscritos**, y decidirse
  por **mayoría simple**, **mayoría absoluta (50 % + 1, con segunda vuelta)**
  o **clasificatoria** (los N primeros pasan a la siguiente ronda).
- **Resultados:** públicos al cierre de cada votación; mientras está
  abierta solo los ve el equipo interno, para no influir en el voto.
- **Auditoría:** verificaciones automáticas (padrón contra urna, firmas,
  horarios, actas, inscritos) y flujo de discrepancias.

El detalle de reglas, rutas y permisos está en [back/README.md](back/README.md).

## Stack

- Backend: Django 6.1 (vistas MVT) + Django REST Framework (API con JWT)
- Base de datos: MySQL 8 en Docker, o SQLite si no se configura MySQL
- Conector MySQL: PyMySQL (no requiere compilar en Windows)
- Imágenes: Pillow (fotos de candidatos)
- Frontend de referencia: prototipo en Vue (`front/`), no es la app final

## Estructura

```text
.
├── back/                  # aplicación Django (ver back/README.md)
├── front/                 # prototipo visual / referencia UX
├── manage.py
├── requirements.txt       # copia de back/requirements.txt
├── docker-compose.yml     # MySQL
├── .env.example           # variables de entorno (copiar a .env)
├── preparar_windows.bat   # instalación en un paso (Windows)
└── preparar_linux.sh      # instalación en un paso (Linux/macOS)
```

## Cómo ejecutar

1. Entorno virtual e instalación (desde la raíz):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
python -m pip install -r back\requirements.txt
```

2. Base de datos: copia `.env.example` a `.env` **en la raíz**. Con
   `DB_PASSWORD` definido se usa MySQL (levántalo con `docker compose up -d`);
   sin él, SQLite.

3. Preparar y arrancar:

```powershell
python manage.py preparar     # migraciones, permisos, datos de demo y cuentas de prueba
python manage.py runserver
```

Abre http://127.0.0.1:8000. Cuentas de prueba: Administrador `100200300 /
admin123`, Organizador `100200301 / org123`, Auditor `100200302 / aud123`,
Votante `1015487962 / voto123`.

`preparar_windows.bat` (o `preparar_linux.sh`) hace los pasos 1 y 3 de una vez.

## Pruebas

```powershell
python manage.py test back
```

Crean y borran su propia base (`test_<nombre>`); no tocan tus datos.

## Mantenimiento

- `python manage.py migrate` aplica migraciones **y sincroniza los
  permisos nuevos** con los roles existentes.
- `python manage.py sincronizar_estados` aplica los cambios de estado por
  fecha; conviene programarlo en un cron cada pocos minutos (el servidor
  también los aplica en cada petición).
- Las fotos subidas se guardan en `media/` (fuera de git). En producción
  debe servirlas el servidor web.
