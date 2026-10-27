# Plan de Desarrollo Backend — Votación Web

## 1. Objetivo
Crear la base del backend en Django para soportar la lógica de negocio del proyecto, manteniendo una separación clara con el frontend que se desarrollará en Vue.

## 2. División propuesta

### Frontend
- Carpeta: `front/`
- Tecnología base: Vue.js
- Función: interfaz, UX, flujo visual y consumo de la API.

### Backend
- Carpeta: `back/`
- Tecnología: Python + Django + Django REST Framework
- Función: autenticación, administración, votación, auditoría, persistence y lógica crítica.

## 3. Estado actual

### Ya realizado
- Base del proyecto Django creada.
- Estructura modular por apps: usuarios, elecciones, votación y auditoría.
- Configuración inicial de DRF y JWT.
- Autenticación con registro y login.
- Modelo de usuarios, roles y permisos.
- RBAC base con acceso protegido en endpoints.
- Validación con pruebas del módulo de usuarios.
- Módulo de categorías electorales funcionando.
- Endpoints CRUD base para categorías, normativas y candidatos.
- Validación con pruebas del módulo de elecciones.

### En progreso
- Integración real con el frontend Vue.
- Generación de votación, certificados y actas.
- Módulo de auditoría y resultados.

## 4. Fases

### Fase 1 — Base y autenticación [COMPLETADA]
- Crear proyecto Django y apps iniciales.
- Configurar entorno, settings, DRF y JWT.
- Definir modelos base de usuarios, roles y permisos.
- Implementar registro, login y acceso protegido.

### Fase 2 — Gestión electoral [COMPLETADA EN BASE]
- Categorías electorales, fechas y estados.
- Normativas y recursos multimedia.
- Gestión de candidatos y tarjetones.

### Fase 3 — Votación y certificados [PENDIENTE]
- Registro de participación por usuario y categoría.
- Emisión de votos anónimos en urna digital.
- Generación de comprobantes, certificados QR y hash.

### Fase 4 — Auditoría y cierre [PENDIENTE]
- Logs inalterables.
- Cierre de elección, actas y resultado final.
- Dashboards de auditoría y consistencia.

## 5. Alineación con el contexto

Esta base se apoya en:
- `contexto_del_proyecto.md`
- `modelo_datos.sql`
- `front/README.md`

La idea es que el backend respete la lógica de roles, estados de la votación y el flujo observable en el prototipo visual, ahora transformado en referencia del frontend Vue.

## 6. Recomendación de evolución

La estrategia correcta es incremental:
1. dejar la base funcionando,
2. completar cada módulo por prioridad,
3. mantener pruebas de cada bloque,
4. conectar cada fase con el frontend Vue cuando esté validada.

## 7. Siguiente tarea

Implementar la Fase 3: votación, participación y certificados, manteniendo la base ya validada.
