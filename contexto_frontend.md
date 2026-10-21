# CONTEXTO DEL PROYECTO: Sistema de Votación Web Seguro (Frontend)

## 1. Objetivo Principal
El objetivo es diseñar y desarrollar la **interfaz gráfica (Frontend) utilizando Vue.js** para un sistema de votación web seguro y auditable (backend en Django REST Framework). La IA debe enfocarse en crear componentes reutilizables, vistas, gestión del estado (Vuex/Pinia) y manejo de rutas (Vue Router) respetando estrictamente la lógica de negocio, el control de acceso (RBAC) y la experiencia de usuario (UX/UI).

## 2. Roles de Usuario y Experiencia Visual (RBAC)
La interfaz se adapta dinámicamente según el perfil autenticado:
*   **Administrador del Sistema:** Gestión completa de usuarios (CRUD individual y masivo por CSV/Excel), configuración de permisos y acciones críticas (ej. borrado lógico, nunca físico si ya votaron).
*   **Organizador / Gestor Electoral:** Configura categorías, fechas de apertura/cierre, sube material multimedia (con interfaz de recorte visual), define normativas (PDF/Markdown) y gestiona la boleta (ordenando candidatos con drag & drop). No tiene acceso a código ni seguridad.
*   **Votante:** Interfaz limpia, responsiva (Mobile-first) y guiada. Accede a normativas, visualiza el tarjetón interactivo, emite voto anónimo (con modales de seguridad) y descarga certificados PDF con código QR y Hash.
*   **Auditor / Juez Electoral:** Vista de solo lectura. Accede a dashboards con gráficos en tiempo real, audita logs inalterables y visualiza alertas de consistencia matemática.

## 3. Estados de la Votación y Reglas Visuales (Bloqueos de Interfaz)
El frontend debe reaccionar a los estados de la categoría electoral:
*   **Borrador / Programada:** Se permite a organizadores editar todo (fechas, candidatos, normativas).
*   **Activa:** El sistema deshabilita (disabled/readonly) todos los formularios de edición para organizadores. Solo se permite votar.
*   **Cerrando:** Se bloquea el botón de "Emitir Voto" inmediatamente.
*   **Finalizada:** Se oculta el tarjetón, se muestran los resultados finales públicos y se habilita la descarga del "Acta de Escrutinio" en PDF.

## 4. Flujo Crítico de Votación (Módulo del Votante)
1. **Tarjetón Digital:** Interfaz neutral, fotos de candidatos estandarizadas. Debe existir siempre la opción "Voto en Blanco".
2. **Selección:** Al hacer clic en una opción, se resalta visualmente y se habilita el botón "Emitir Voto".
3. **Confirmación:** Modal estricto: "¿Confirma su voto por [X]? Esta acción no se puede deshacer".
4. **Prevención de Errores:** Al confirmar, el botón muestra un *spinner* de carga y se bloquea para evitar doble envío. 
5. **Éxito:** Pantalla final mostrando el código Hash SHA-256 generado.

## 5. Requisitos Técnicos del Frontend a tener en cuenta
*   **Autenticación JWT:** El frontend debe manejar un *Access Token* (expira en 60 min) y un *Refresh Token*. Se requiere configurar interceptores HTTP (Axios/Fetch) para renovar el token transparentemente sin sacar al usuario de la pantalla.
*   **Manejo de Archivos:** Interfaz para arrastrar y soltar (Drag & Drop) archivos CSV para carga de votantes, y validación visual de peso/formato (< 10MB, PDF/DOCX) para normativas.
*   **Tiempo Real:** Los gráficos del Dashboard (Auditor/Votante) deben estar preparados para consumir datos vía WebSockets o polling continuo si la opción "Resultados en tiempo real" está activa.
*   **Seguridad Visual:** Manejo de estado para intentos fallidos de login (mostrar alerta de bloqueo temporal por 15 min después de 5 intentos).