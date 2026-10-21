# Contexto del Proyecto: Sistema Web de Votaciones - Festival de la Leyenda Vallenata 2027

---

## 1. Informacion General del Proyecto

- **Nombre del Proyecto:** Sistema Web de Votaciones - Festival de la Leyenda Vallenata 2027
- **Institución:** Fundación Universitaria del Área Andina
- **Programa / Asignatura:** Departamento de Ingeniería - Desarrollo Web (202660-6A-62)
- **Autores:**
  - Diego Bolaños Castillo
  - Omar Leonardo Manosalva Sánchez
  - Nicolas Ardila Ochoa
  - Hernan Pineda Nieto
- **Profesor:** Deivys Morales Uribe
- **Ubicación y Fecha:** Bogotá y Soacha, Cundinamarca – 10 de octubre de 2026

---

## 2. Antecedentes y Contexto de Negocio

### 2.1 El Festival de la Leyenda Vallenata
El Festival de la Leyenda Vallenata es el evento folclórico y cultural más emblemático del departamento del Cesar (Valledupar, Colombia). Su propósito es preservar la música vallenata, sus mitos, costumbres y tradición oral.

#### Concursos y Categorías Tradicionales:
1. **Conjunto Típico de Música Vallenata** (Acordeón, caja y guacharaca):
   - Categorías: Profesional, Aficionado, Juvenil e Infantil.
   - Aires tradicionales: Paseo, Merengue, Son y Puya.
2. **Canción Vallenata Inédita:**
   - Categoría única (para canciones no grabadas en cualquiera de los cuatro aires).
3. **Piquería:**
   - Categorías: Mayor e Infantil.
4. **Desfile de Piloneras:**
   - Categorías: Infantil, Juvenil y Mayores.

### 2.2 Antecedentes Digitales
- **Situación histórica:** La elección de ganadores es realizada tradicionalmente por un jurado calificador sin mecanismo de votación pública oficial.
- **Experiencia Virtual 2020 ($53^\circ$ Festival):** Transmisión en vivo por sitio web/redes sociales debido a la pandemia de Covid-19, alcanzando +22k espectadores en la final y +200k reproducciones en YouTube.
- **Sitio Web Actual (`festivalvallenato.com`):** Portal estrictamente institucional/informativo (noticias, reglamentos downloadable, programación, histórico de ganadores). **Oportunidades de mejora:** Falta de inscripción directa, ausencia de módulo de votaciones en línea, enlaces inactivos e imágenes caídas.

---

## 3. Benchmarking de Plataformas de Votación

| Aspecto | Feria de Cali (Afiche Oficial) | Premios India Catalina | Yo Me Llamo (Caracol TV) |
| :--- | :--- | :--- | :--- |
| **Propósito** | Elección ciudadana entre 2 afiches finalistas de jurado. | Premio del público (votación directa en 5 categorías o ponderada con jurado). | Selección del imitador ganador en la gran final. |
| **Registro** | Formulario de inscripción en plataforma. | Usuario con nombre y correo; activación por e-mail. | Voto inicial por dispositivo + registro completo con código enviado al correo. |
| **Navegación** | Sitio oficial de la Feria de Cali. | Sección "Selección Ganadores Público General" en web oficial. | Link oficial difundido en televisión y medios aliados. |
| **Votación** | Voto único entre 2 opciones en ventana corta de tiempo. | Un voto por categoría por usuario registrado. | Límite por navegador/dispositivo/usuario dentro del plazo del programa. |
| **Seguridad** | Registro previo en plataforma. | Verificación de correo, límite de 1 voto/categoría y peso relativo frente al jurado. | Límite multi-capa, código al correo, auditoría externa por Deloitte. |
| **Lección Aprendida** | Selección previa por jurado + votación abierta corta. | Ponderación jurado/público con validación estricta por correo. | Verificación robusta mediante OTP/código, auditoría de terceros. |

---

## 4. Definición del Problema, Objetivos y Alcance

### 4.1 Problema Identificado
El Festival no cuenta con un canal digital oficial para votaciones del público. La recopilación informal de opiniones en redes sociales genera riesgos de **votos duplicados, fraude, bots e imprevisibilidad**, impidiendo entregar reconocimientos como *Piloneras favoritas*, *Mejor comparsa*, *Mejor vestuario* o *Artista preferido del público*.

### 4.2 Objetivos
- **Objetivo General:** Diseñar una plataforma web de votación en línea segura, transparente e intuitiva para el Festival de la Leyenda Vallenata 2027.
- **Objetivos Específicos:**
  1. Identificar las categorías y participantes habilitados para la votación pública.
  2. Definir requerimientos funcionales y no funcionales adaptados a dispositivos móviles.
  3. Establecer el flujo electoral end-to-end (autenticación, emisión, anonimización, cierre y auditoría).
  4. Diseñar una interfaz escalar y fácil de mantener para futuras ediciones.

### 4.3 Matriz de Alcance

| Elemento | Estado | Justificación / Observación |
| :--- | :--- | :--- |
| **Gestión de categorías y candidatos** | **Incluido** | Panel administrativo CRUD para cargar fotos, bio y datos. |
| **Registro con correo electrónico** | **Incluido** | Identificación de usuarios mediante email y password. |
| **1 voto por persona/categoría** | **Incluido** | Regla estricta para garantizar la confiabilidad. |
| **Apertura/Cierre temporal y Resultados** | **Incluido** | Control cronológico y visualización post-cierre. |
| **Diseño Responsive (Mobile First)** | **Incluido** | Optimizado para el uso masivo desde teléfonos móviles. |
| **Reemplazo del jurado oficial** | **NO Incluido** | La plataforma es complementaria a los premios tradicionales. |
| **Cobro por voto** | **NO Incluido** | No contemplado en las necesidades de la Fundación. |
| **App Nativa (iOS/Android)** | **NO Incluido** | Reemplazada por PWA / Web Responsive en navegador. |
| **Validación por SMS (OTP)** | *Pendiente* | En evaluación de costos operacionales vs. seguridad. |
| **Manejo de datos de menores de edad** | *Pendiente* | Sujeto a la política de tratamiento de datos personales de la Fundación. |

---

## 5. Actores del Sistema (RBAC)

1. **Administrador del Sistema:** Control total del sistema, gestión de infraestructura, asignación de roles y permisos (Matriz RBAC), mantenimiento de cuentas y seguridad global.
2. **Organizador / Gestor Electoral:** Configuración de elecciones, apertura/cierre de votaciones, gestión de categorías, candidatos, tarjetones y carga de normativas/multimedia.
3. **Votante:** Usuario final autenticado. Consulta normativas, visualiza tarjetones, emite su voto de forma anónima y descarga comprobantes/certificados en PDF.
4. **Auditor / Juez Electoral:** Perfil de fiscalización en solo lectura. Revisa métricas en tiempo real, audita logs *append-only* y verifica la ecuación de consistencia matemática del padrón vs. urna.

---

## 6. Requerimientos del Sistema

### 6.1 Requerimientos Funcionales (RF)
- **RF-01:** Carga masiva de usuarios en el padrón mediante archivos CSV o Excel (Drag & Drop).
- **RF-02:** Matriz interactiva de permisos para la gestión cruzada de roles y módulos (RBAC).
- **RF-03:** Herramienta visual de previsualización y recorte (*crop*) de imágenes multimedia.
- **RF-04:** Constructor visual de tarjetones mediante interacción *Drag & Drop* para ordenar candidatos.
- **RF-05:** Modal de confirmación con *spinner* de carga y generación de hash de comprobante SHA-256 al votar.
- **RF-06:** Descarga de certificado de votación en PDF con código QR de verificación pública.
- **RF-07:** Panel de auditoría con ecuación visual de consistencia matemática y bitácora inalterable.

### 6.2 Requerimientos No Funcionales (RNF)
- **RNF-01:** Interfaz de usuario desarrollada en **Vue.js**, gestionando estado global (**Pinia/Vuex**) y rutas (**Vue Router**).
- **RNF-02:** Manejo de sesiones con **Tokens JWT** con renovación transparente mediante *interceptors*.
- **RNF-03:** Interfaz responsiva con bloqueo temporal de cuenta tras 5 intentos fallidos de inicio de sesión.
- **RNF-04:** Validación de peso máximo de archivos subidos ($\le 10\text{ MB}$).
- **RNF-05:** Actualización de dashboards en tiempo real mediante **WebSockets** o *Polling* optimizado.
- **RNF-06:** Soporte para modo oscuro (*Dark Mode*) conmuta en el panel superior.

---

## 7. Reglas de Negocio (RN)

### Seguridad y Autenticación
- **RN-SEC-01:** Almacenamiento obligatorio de contraseñas mediante hashing seguro (Argon2 / PBKDF2).
- **RN-SEC-02:** Tiempo máximo de vida del Access Token JWT: 60 minutos.
- **RN-SEC-03:** Refresco automático y transparente de tokens expirados sin interrumpir al usuario.
- **RN-SEC-04:** Registro obligatorio de IP de origen y *timestamp* en cada intento fallido de autenticación.
- **RN-SEC-05:** Revocación inmediata de tokens activos ante cambios en la matriz RBAC que retiren permisos.
- **RN-SEC-06:** Bitácora de auditoría estricta de solo escritura (*Append-Only*), inalterable por cualquier usuario.
- **RN-SEC-07:** Inclusión de firma Hash del estado de la BD en reportes de auditoría para prevenir manipulación.

### Usuarios y Control de Acceso
- **RN-USR-01:** Documento / Identificador Nacional único como llave primaria electoral.
- **RN-USR-02:** Solo el Administrador puede modificar roles, permisos y datos sensibles.
- **RN-USR-03:** Imposibilidad de privar al rol Administrador de los permisos básicos de administración.
- **RN-USR-04:** Prohibición absoluta de borrado físico (*Hard Delete*) de usuarios con historial electoral.
- **RN-USR-05:** Inactivación o suspensión mediante borrado lógico (*Soft Delete* / Flag de estado).

### Categorías y Tarjetón Electoral
- **RN-CAT-01:** Rango cronológico explícito con fecha/hora exacta de inicio y cierre.
- **RN-CAT-02:** Requisito obligatorio de adjuntar documento o norma legal antes de activar una categoría.
- **RN-CAT-03:** Modificación de fechas de categorías activas con votos sólo mediante autorización de Auditoría.
- **RN-CAT-04:** Inclusión paramétrica obligatoria de la opción **"Voto en Blanco"** en cada categoría.
- **RN-CAT-05:** Prohibición de alterar, añadir o descalificar candidatos en categorías activas con votos emitidos.
- **RN-CAN-01 / RN-CAN-02:** Estandarización automática de fotos de candidatos ($400\times400\text{ px}$) para neutralidad visual.

### Emisión del Voto y Cierre
- **RN-VOT-01 (Regla de Oro):** Un (1) solo voto por usuario en cada categoría habilitada.
- **RN-VOT-02 (Anonimato Estricto):** Desacoplamiento técnico total entre la identidad del votante y el voto depositado en la urna.
- **RN-VOT-03:** Bloqueo de votos duplicados por usuario dentro de una misma categoría.
- **RN-VOT-04:** Inmutabilidad del voto una vez registrado.
- **RN-PRO-01:** Imposibilidad de reactivar una elección en estado *Finalizada*.
- **RN-PRO-02 / RN-PRO-03:** Acta de escrutinio sellada con la firma Hash de la suma de votos consolidados.
- **RN-CER-01 a RN-CER-04:** El certificado acredita participación sin revelar la opción elegida; su autenticidad se confirma mediante código QR con URL pública.

---

## 8. Especificación de Casos de Uso (CU)

| Código | Nombre del Caso de Uso | Actores Principales | Descripción Resumida |
| :--- | :--- | :--- | :--- |
| **CU-00** | Autenticar Usuario e Iniciar Sesión | Todos | Validación de credenciales contra Django Auth, entrega de par JWT y redirección a dashboard por rol. |
| **CU-01** | Registrar Votante / Usuario | Administrador, Organizador | Registro individual o carga masiva (CSV/Excel) de usuarios al padrón electoral. |
| **CU-02** | Administrar Cuentas de Usuario | Administrador | Modificación de perfiles, ajuste de datos, suspensión o cambio a borrado lógico. |
| **CU-03** | Gestionar Permisos y Accesos (RBAC) | Administrador | Configuración interactiva de permisos de endpoints (Backend) y rutas (Frontend). |
| **CU-04** | Crear y Configurar Categorías | Organizador, Administrador | Parametrización de elecciones, rango cronológico y visibilidad de resultados. |
| **CU-05** | Establecer Normativas y Requisitos | Organizador | Carga de reglamentos en HTML/Markdown y PDF adjuntos ($\le 10\text{ MB}$). |
| **CU-06** | Cargar Recursos y Multimedia | Organizador, Administrador | Subida, encuadre, recorte y optimización de imágenes gráficas. |
| **CU-07** | Emitir Voto | Votante | Transacción atómica de emisión anónima de voto con comprobante Hash SHA-256. |
| **CU-08** | Visualizar Resultados en Tiempo Real | Votante, Auditor, Administrador| Gráficos dinámicos e indicadores según políticas de visibilidad de la elección. |
| **CU-09** | Auditar Proceso de Votación | Auditor, Administrador | Verificación de consistencia matemática, lectura de logs *append-only* y reporte en PDF/Excel. |
| **CU-10** | Gestionar Candidatos y Opciones | Organizador, Administrador | CRUD y ordenamiento (*drag & drop*) de tarjetón electoral. |
| **CU-11** | Cerrar Elección y Generar Acta | Organizador, Administrador | Bloqueo de API, cómputo definitivo y emisión de Acta de Escrutinio firmada con Hash. |
| **CU-12** | Descargar Certificado de Votación | Votante | Generación de PDF firmado con QR para verificación pública sin revelar sentido de voto. |

---

## 9. Modelo de Datos Conceptual

Entities y relaciones representadas:
- `usuarios`: `id`, `documento` (UQ), `nombres`, `apellidos`, `correo` (UQ), `password_hash`, `estado`, `intentos_fallidos`, `bloqueado_hasta`.
- `roles`: `id`, `nombre` (UQ), `descripcion`.
- `permisos`: `id`, `codigo` (UQ), `descripcion`, `modulo`.
- `categorias_electorales`: `id`, `titulo`, `descripcion`, `fecha_hora_inicio`, `fecha_hora_cierre`, `estado`, `mostrar_resultados_tiempo_real`.
- `candidatos_opciones`: `id`, `categoria_id` (FK), `nombre_candidato`, `partido_lista`, `biografia`, `orden_casilla`, `foto_recurso_id` (FK).
- `participacion_votantes`: `id`, `usuario_id` (FK), `categoria_id` (FK), `fecha_emision`, `hash_comprobante` (UQ). *(Demuestra que el usuario votó, pero NO por quién).*
- `urna_digital`: `id`, `categoria_id` (FK), `candidato_id` (FK), `fecha_registro`, `firma_criptografica`. *(Desacoplado de la tabla `usuarios` para garantizar el anonimato).*
- `certificados_votacion`: `id`, `participacion_id` (FK), `codigo_certificado` (UQ), `qr_verificacion_url`, `fecha_generacion`.
- `actas_escrutinio`: `id`, `categoria_id` (FK), `fecha_cierre`, `total_padron_habilitado`, `total_participantes`, `total_votos_urna`, `hash_salida`, `archivo_pdf`.
- `logs_auditoria_eventos`: `id`, `usuario_id`, `accion`, `detalles_json`, `ip_origen`, `timestamp`.
- `recursos_multimedia`: `id`, `nombre_archivo`, `url_publica`, `tipo_mime`, `tamano_bytes`.
- `normativas`: `id`, `categoria_id` (FK), `titulo`, `contenido_html`, `archivo_pdf_url`, `fecha_publicacion`.

---

## 10. Arquitectura Tecnológica Propuesta

```
+-----------------------------------------------------------------------+
|                         CAPA DE PRESENTACIÓN                          |
|             Frontend Web Responsivo / PWA (Vue.js 3 + Pinia)          |
+-----------------------------------------------------------------------+
                                   |
                             HTTPS / TLS
                                   |
+-----------------------------------------------------------------------+
|                            CAPA DE NEGOCIO                            |
|                 Backend API (Django REST Framework)                   |
|                                                                       |
|  [ Autenticación JWT ]  [ Módulo Votación ]  [ Cierre & Escrutinio ]  |
|  [ Matriz RBAC ]        [ Módulo Auditoría ] [ Motor de PDF/QR ]      |
+-----------------------------------------------------------------------+
                                   |
                  ORMs y Conexiones Atómicas de BD
                                   |
+-----------------------------------------------------------------------+
|                         CAPA DE PERSISTENCIA                          |
|              Base de Datos Relacional (PostgreSQL / MySQL)            |
|                                                                       |
|  [ Padrón / Usuarios ]   [ Urna Digital (Anónima) ]  [ Logs Append ]  |
+-----------------------------------------------------------------------+
```

---

## 11. Recursos Externos
- **Prototipo UX/UI Navegable:** [Google Drive Folder](https://drive.google.com/drive/folders/1CiokUG7qxDmkjzf6Z8VbXtMcTPJUPePv?usp=sharing)
```

EOF

El archivo `context.md` ha sido generado con toda la estructura técnica, requerimientos, reglas de negocio, modelos de datos y flujos definidos en el documento original.