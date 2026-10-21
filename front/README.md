# Frontend base — Sistema de Votación Web Seguro

Este directorio representa la referencia visual y UX del frontend del sistema de votación.
Se mantiene como prototipo base para la implementación final en Vue.js.

Construido en HTML + CSS + JS puro (sin dependencias, sin instalación).

## Cómo abrirlo

**Opción 1 — Doble clic:** abre `prototipo/index.html` en cualquier navegador moderno.

**Opción 2 — Servidor local (recomendado):**

```bash
cd prototipo
python -m http.server 8080
# luego abre http://localhost:8080
```

## Cómo navegar

1. En el login, usa los **botones de demo** (parte inferior) para entrar con cada rol:
   - 🔑 **Administrador** — Laura Restrepo
   - 📋 **Organizador** — Andrés Catalán
   - 🗳️ **Votante** — Cardina Rentería
   - 🔍 **Auditor** — Martha Lucumí
2. También puedes probar el login real con `1015488962 / voto123` (votante) y ver el manejo de intentos fallidos (5 → bloqueo 15 min).
3. El **selector "Estado"** del panel superior es un **simulador**: cambia la elección entre Borrador / Programada / Activa / Cerrando / Finalizada y observa cómo se bloquean los formularios del organizador (regla de la sección 3 del contexto).

## Vistas implementadas

| Rol | Vistas |
|---|---|
| **Login** | CU-00 · login con intentos fallidos y bloqueo temporal |
| **Administrador** | Dashboard · CU-02 gestión de usuarios (CRUD, suspender, borrado lógico) · CU-01 registro individual + carga masiva CSV/Excel (drag & drop, validación 10 MB) · CU-03 matriz de permisos RBAC roles × módulos |
| **Organizador** | Dashboard · CU-04 categorías con fechas · CU-05 normativas (editor + PDF) · CU-06 multimedia con recorte simulado · CU-10 tarjetón con drag & drop y voto en blanco obligatorio · CU-11 cierre y acta de escrutinio |
| **Votante** | Inicio con elecciones disponibles · CU-07 tarjetón interactivo → modal de confirmación → spinner → comprobante con Hash SHA-256 · CU-08 resultados (respetando visibilidad) · CU-12 certificados con QR |
| **Auditor** | CU-08 dashboard en tiempo real (barras + donut) · CU-09 ecuación de consistencia + bitácora inalterable |

## Reglas visuales demostradas

- **Bloqueos por estado:** en estado ACTIVA/CERRANDO/FINALIZADA los formularios de configuración aparecen deshabilitados con banner explicativo.
- **Prevención de doble acción:** el botón "Emitir voto" muestra spinner y se bloquea al confirmar.
- **Botón de voto bloqueado en CERRANDO:** la tarjeta del votante lo muestra deshabilitado.
- **Voto en Blanco:** casilla obligatoria al final del tarjetón.
- **Dark mode:** botón de tema en el panel superior.

## Estructura

```
prototipo/
├── index.html
└── assets/
    ├── styles.css        # Sistema de diseño (tema claro/oscuro, componentes)
    ├── icons.js          # Iconos SVG inline
    ├── data.js           # Datos mock + estado global
    ├── ui.js             # Toasts, modales, badges, gráficos
    ├── views-login.js    # CU-00
    ├── views-admin.js    # CU-01, CU-02, CU-03
    ├── views-org.js      # CU-04, CU-05, CU-06, CU-10, CU-11
    ├── views-votante.js  # CU-07, CU-08, CU-12
    ├── views-auditor.js  # CU-08, CU-09
    └── app.js            # Layout, router por hash, control de acceso por rol
```

## Alcance

La carpeta `front/` funciona como referencia visual y flujo UX para la implementación real en Vue.js.
Los datos son simulados en el navegador para validar la experiencia, pero el desarrollo real se conecta con la API de Django REST:
- JWT
- endpoints por CU
- consumo de datos dinámicos
- WebSockets o polling para resultados en vivo

En resumen: el prototipo no reemplaza la app final, sino que sirve como guía visual para la versión en Vue.
