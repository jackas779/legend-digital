# Sistema de Votación Web Seguro

Este proyecto consiste en un sistema de votación digital con arquitectura modular, pensado para apoyar procesos electorales con control de acceso, roles, normas, candidatos y auditoría.

## Objetivo del proyecto

Desarrollar una base funcional robusta para una plataforma de votación que incluya:

- autenticación segura con JWT
- gestión de usuarios y roles
- control de permisos por módulo
- administración de categorías, normas y opciones/candidatos
- preparación para la fase de votación, certificados y auditoría

## Stack principal

- Backend: Django + Django REST Framework
- Autenticación: JWT
- Base de datos: SQLite para desarrollo local
- Frontend de referencia: prototipo visual en HTML/CSS/JS para UX/UI
- Frontend final previsto: Vue.js

## Estructura del repositorio

```text
.
├── back/                  # aplicación Django y API REST
├── front/                 # prototipo visual / referencia UX del frontend
├── manage.py              # entry point del proyecto Django
├── requirements.txt       # dependencias del backend
├── db.sqlite3             # base de datos local de desarrollo
├── PLAN_DESARROLLO_BACKEND.md
├── .gitignore
├── .venv/                 # entorno virtual local
└── README.md              # documentación general del proyecto
```

## Estado actual

La base funcional del backend ya quedó establecida y validada, con módulos principales para:

- usuarios
- autenticación y permisos
- elecciones, categorías y normativa
- candidatos/opciones

La carpeta [front](front) funciona como referencia visual y UX para la implementación final en Vue. No reemplaza la app final; sirve como guía para definir flujos, estados y componentes.

## Cómo ejecutar el proyecto

1. Crear y activar entorno virtual

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias

```bash
pip install -r requirements.txt
```

3. Ejecutar migraciones y levantar el backend

```bash
python manage.py migrate
python manage.py runserver
```

4. Acceder a la API en

```text
http://localhost:8000/
```

## Siguientes fases previstas

- votación y registro de participación
- certificados y QR
- auditoría y actas
- integración del frontend Vue con la API

## Nota

La documentación de contexto generada por herramientas externas quedó eliminada para mantener el repositorio limpio y centrado en la arquitectura real del proyecto.
