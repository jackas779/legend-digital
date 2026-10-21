# Plan de Desarrollo Backend — Votación Web

## 1. Objetivo
Crear la base del backend en Django para soportar la lógica de negocio del proyecto, manteniendo una separación clara con el prototipo front-end ya desarrollado en `prototipo/`.

## 2. División propuesta

### Frontend
- Carpeta: `prototipo/`
- Tecnología base: HTML, CSS y JavaScript
- Función: maquetación, UX, flujo visual, estados y simulación de negocio.

### Backend
- Carpeta: `back/`
- Tecnología: Python + Django + Django REST Framework
- Función: autenticación, administración, votación, auditoría, persistence y lógica crítica.

## 3. Fases

### Fase 1 — Base y autenticación
- Crear proyecto Django y apps iniciales.
- Configurar entorno, settings, DRF y JWT.
- Definir modelos base de usuarios, roles y permisos.
- Implementar login, logout y sesión.

### Fase 2 — Gestión electoral
- Categorías electorales, fechas y estados.
- Normativas y recursos multimedia.
- Gestión de candidatos y tarjetones.

### Fase 3 — Votación y certificados
- Registro de participación por usuario y categoría.
- Emisión de votos anónimos en urna digital.
- Generación de comprobantes, certificados QR y hash.

### Fase 4 — Auditoría y cierre
- Logs inalterables.
- Cierre de elección, actas y resultado final.
- Dashboards de auditoría y consistencia.

## 4. Alineación con el contexto

Esta base se apoya en:
- `contexto_del_proyecto.md`
- `gemini-code-1791741321976.sql`
- `prototipo/README.md`

La idea es que el backend respete la lógica de roles, estados de la votación y el flujo observable en el prototipo.

## 5. Recomendación de evolución

No se debe terminar todo de una vez. Lo prudente es:
1. dejar la base estructural funcionando,
2. conectar la autenticación,
3. construir los módulos de negocio por orden de prioridad,
4. integrarlos con el frontend tras validar cada fase.
