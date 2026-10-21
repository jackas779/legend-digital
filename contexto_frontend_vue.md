# CONTEXTO DEL PROYECTO: Sistema de Votación Web Seguro (Frontend Vue.js)

## 1. Objetivo Principal
Desarrollar la interfaz gráfica (Frontend) en Vue.js para un sistema de votación web seguro y auditable. El desarrollo debe estructurarse estrictamente en torno a los Casos de Uso (CU) definidos, creando componentes reutilizables, gestionando el estado (Vuex/Pinia) y las rutas (Vue Router) según el control de acceso basado en roles (RBAC)[cite: 1]. 

## 2. Roles de Usuario (RBAC)
*   **Administrador del Sistema:** Control total, gestión de usuarios y matriz de permisos[cite: 1].
*   **Organizador / Gestor Electoral:** Logística electoral, carga de candidatos, normativas y multimedia (sin acceso a seguridad)[cite: 1].
*   **Votante:** Interfaz guiada para emitir voto anónimo y descargar comprobantes[cite: 1].
*   **Auditor / Juez Electoral:** Vistas de solo lectura para fiscalización y métricas en tiempo real[cite: 1].

## 3. Especificación de Vistas por Casos de Uso (Componentes a Desarrollar)

### Módulo 1: Usuarios, Autenticación y Seguridad[cite: 1]
*   **CU-00 - Autenticar Usuario e Iniciar Sesión:** Formulario de login (documento/correo y contraseña)[cite: 1]. Manejo visual de tokens JWT, alertas de "Credenciales incorrectas" y bloqueo temporal tras 5 intentos fallidos[cite: 1].
*   **CU-01 - Registrar Votante / Usuario:** Formularios de registro individual y vista para carga masiva arrastrando archivos CSV/Excel[cite: 1].
*   **CU-02 - Administrar Cuentas de Usuario:** Tabla de gestión (CRUD) con opciones de edición y estados (Activo, Suspendido, Inactivo)[cite: 1].
*   **CU-03 - Gestionar Permisos y Accesos:** Tabla interactiva (filas = roles, columnas = módulos) para marcar/desmarcar permisos con validación visual[cite: 1].

### Módulo 2: Configuración de Elecciones y Contenidos[cite: 1]
*   **CU-04 - Crear y Configurar Categorías:** Formulario de parametrización con selectores de fecha/hora exacta de apertura y cierre[cite: 1].
*   **CU-05 - Establecer Normativas:** Editor de texto enriquecido (HTML/Markdown) y zona de carga de archivos PDF con validación de peso (<10 MB)[cite: 1].
*   **CU-06 - Cargar Recursos Multimedia:** Interfaz interactiva de subida con herramienta visual de encuadre y recorte (crop) para estandarizar fotos[cite: 1].
*   **CU-10 - Gestionar Candidatos (CRUD):** Vista de construcción del "Tarjetón". Incluye herramienta de "drag & drop" para ordenar casillas de candidatos y la opción obligatoria de "Voto en Blanco"[cite: 1].

### Módulo 3: Proceso Electoral y Certificación[cite: 1]
*   **CU-07 - Emitir Voto:** Interfaz central del Votante. Despliega el tarjetón interactivo[cite: 1]. Flujo visual: Seleccionar casilla -> Resaltar -> Botón "Emitir Voto" -> Modal estricto de confirmación ("Esta acción no se puede deshacer") -> Pantalla de éxito con Hash SHA-256[cite: 1].
*   **CU-11 - Cerrar Elección y Generar Acta:** Interfaz para organizadores que muestra el cambio de estado a "Finalizada" y habilita la descarga del Acta de Escrutinio en PDF[cite: 1].
*   **CU-12 - Descargar Certificado de Votación:** Panel personal del votante con el historial de participación y botón para descargar el PDF con código QR[cite: 1].
*   **CU-08 - Visualizar Resultados en Tiempo Real:** Dashboard con gráficos interactivos (pastel/barras) que se actualizan dinámicamente según las reglas de visibilidad de la categoría[cite: 1].

### Módulo 4: Supervisión y Auditoría[cite: 1]
*   **CU-09 - Auditar Proceso de Votación:** Panel de solo lectura para el Auditor[cite: 1]. Muestra la ecuación de consistencia matemática visual (Padrón vs. Votos) y una tabla de logs inalterables con opción a exportar[cite: 1].

## 4. Reglas de Negocio Visuales Clave
*   **Bloqueos por Estado:** Si una categoría pasa a estado "Activa", el frontend debe deshabilitar (disabled) todas las opciones de edición de los CU-04, CU-05 y CU-10[cite: 1].
*   **Prevención de Doble Acción:** En el CU-07, al confirmar el voto, el botón debe bloquearse inmediatamente y mostrar un estado de carga[cite: 1].
*   **Anonimato:** El diseño de la interfaz de auditoría y resultados (CU-08 y CU-09) nunca debe cruzar datos de identidad con opciones de voto[cite: 1].