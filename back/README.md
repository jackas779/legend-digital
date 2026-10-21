# Backend Django — Sistema de Votación

Este directorio contiene la base del backend de la aplicación, separada del prototipo frontend que vive en `prototipo/`.

## Estructura base

- `back/` : proyecto Django principal
- `back/apps/` : aplicaciones modulares por dominio
  - `usuarios/`
  - `elecciones/`
  - `votacion/`
  - `auditoria/`
- `requirements.txt` : dependencias del backend

## Pasos iniciales

```bash
cd "proyecto universidad"
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Objetivo de esta base

- Separar claramente frontend y backend.
- Alinear el backend con el modelo de datos del SQL de `gemini-code-1791741321976.sql`.
- Dejar una estructura modular que permita crecer por fases sin mezclar responsabilidades.

## Fases sugeridas

1. Fase 1: autenticación y usuarios (RBAC).
2. Fase 2: elecciones, normativas y candidatos.
3. Fase 3: votación y certificados.
4. Fase 4: auditoría, resultados y actas.
