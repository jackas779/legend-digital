-- =========================================================
-- MODELO DE DATOS NORMALIZADO — VOTACIÓN WEB
-- Módulos: seguridad/RBAC, configuración electoral,
-- urna digital/certificación y auditoría.
--
-- Nota sobre autenticación:
-- Django gestiona la contraseña en la tabla auth_user (campo password).
-- La tabla usuarios de este modelo es el perfil electoral asociado
-- (OneToOne con auth_user) y conserva la llave documento/correo/rol.
-- =========================================================

-- =========================================================
-- MÓDULO 1: SEGURIDAD, AUTENTICACIÓN Y RBAC (CU-00 a CU-03)
-- =========================================================

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE permisos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(100) NOT NULL UNIQUE, -- Ej: 'categorias.crear', 'voto.emitir'
    modulo VARCHAR(50) NOT NULL,
    descripcion TEXT
);

CREATE TABLE rol_permisos (
    rol_id INT NOT NULL,
    permiso_id INT NOT NULL,
    PRIMARY KEY (rol_id, permiso_id),
    CONSTRAINT fk_rp_rol FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_rp_permiso FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    documento VARCHAR(20) NOT NULL UNIQUE,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    -- password_hash: gestionado por auth_user.password en Django.
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'ACTIVO',
    intentos_fallidos INT DEFAULT 0,
    bloqueado_hasta TIMESTAMP NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_rol FOREIGN KEY (rol_id) REFERENCES roles(id)
);

CREATE TABLE sesiones_tokens (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    token_hash VARCHAR(256) NOT NULL UNIQUE,
    ip_origen VARCHAR(45) NOT NULL,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP NOT NULL,
    revocado BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_sesion_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- =========================================================
-- MÓDULO 2: JERARQUÍA ELECTORAL NORMALIZADA (CU-04 a CU-06, CU-10)
-- =========================================================

-- Edición: agrupa un proceso electoral completo (Ej: Elecciones 2026)
CREATE TABLE ediciones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    anio INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'BORRADOR',
    creador_usuario_id INT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_edicion_creador FOREIGN KEY (creador_usuario_id)
        REFERENCES usuarios(id) ON DELETE PROTECT
);

-- Categoría: temática reutilizable (Ej: Alcaldía, Consejo Estudiantil)
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    descripcion TEXT
);

-- Votación concreta de una categoría dentro de una edición
CREATE TABLE votaciones (
    id SERIAL PRIMARY KEY,
    edicion_id INT NOT NULL,
    categoria_id INT NOT NULL,
    fecha_apertura TIMESTAMP NOT NULL,
    fecha_cierre TIMESTAMP NOT NULL,
    estado VARCHAR(20) DEFAULT 'BORRADOR',
    mostrar_resultados_en_vivo BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_votacion_edicion FOREIGN KEY (edicion_id)
        REFERENCES ediciones(id) ON DELETE CASCADE,
    CONSTRAINT fk_votacion_categoria FOREIGN KEY (categoria_id)
        REFERENCES categorias(id) ON DELETE PROTECT
);

-- Opción: persona, lista o alternativa reutilizable entre votaciones
CREATE TABLE recursos_multimedia (
    id SERIAL PRIMARY KEY,
    nombre_archivo VARCHAR(150) NOT NULL,
    url_publica VARCHAR(255) NOT NULL,
    tipo_mime VARCHAR(50) NOT NULL,
    peso_bytes INT NOT NULL,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE opciones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    identificador_unico VARCHAR(100) NOT NULL UNIQUE,
    biografia TEXT,
    foto_recurso_id INT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_opcion_foto FOREIGN KEY (foto_recurso_id)
        REFERENCES recursos_multimedia(id) ON DELETE SET NULL
);

-- Casilla del tarjetón: una opción participando en una votación
CREATE TABLE opciones_votacion (
    id SERIAL PRIMARY KEY,
    votacion_id INT NOT NULL,
    opcion_id INT NOT NULL,
    numero_casilla INT NOT NULL,
    es_voto_blanco BOOLEAN DEFAULT FALSE,
    -- Dato de presentación de la candidatura (extensión para el tarjetón).
    partido_lista VARCHAR(120),
    CONSTRAINT fk_ov_votacion FOREIGN KEY (votacion_id)
        REFERENCES votaciones(id) ON DELETE CASCADE,
    CONSTRAINT fk_ov_opcion FOREIGN KEY (opcion_id)
        REFERENCES opciones(id) ON DELETE CASCADE,
    CONSTRAINT uq_votacion_casilla UNIQUE (votacion_id, numero_casilla),
    CONSTRAINT uq_votacion_opcion UNIQUE (votacion_id, opcion_id)
);

CREATE TABLE normativas (
    id SERIAL PRIMARY KEY,
    votacion_id INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    contenido_html TEXT,
    archivo_pdf_url VARCHAR(255),
    fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_normativa_votacion FOREIGN KEY (votacion_id)
        REFERENCES votaciones(id) ON DELETE CASCADE
);

-- =========================================================
-- MÓDULO 3: PADRÓN, URNA DIGITAL Y CERTIFICACIÓN (CU-07, CU-08, CU-11, CU-12)
-- =========================================================

-- Padrón: habilitación y marca de participación por usuario y votación
CREATE TABLE padron_votantes (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    votacion_id INT NOT NULL,
    ha_votado BOOLEAN DEFAULT FALSE,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hash_comprobante VARCHAR(256) NULL UNIQUE,
    CONSTRAINT fk_padron_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_padron_votacion FOREIGN KEY (votacion_id)
        REFERENCES votaciones(id) ON DELETE CASCADE,
    CONSTRAINT uq_usuario_votacion UNIQUE (usuario_id, votacion_id)
);

-- Certificado de participación (uno por registro de padrón)
CREATE TABLE certificados_votacion (
    id SERIAL PRIMARY KEY,
    padron_id INT NOT NULL UNIQUE,
    codigo_certificado VARCHAR(100) NOT NULL UNIQUE,
    qr_verificacion_url TEXT NOT NULL,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cert_padron FOREIGN KEY (padron_id)
        REFERENCES padron_votantes(id) ON DELETE CASCADE
);

-- Urna digital: voto anónimo, sin FK hacia usuarios
CREATE TABLE votos_urna (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    votacion_id INT NOT NULL,
    opcion_votacion_id INT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    firma_criptografica VARCHAR(256) NOT NULL,
    CONSTRAINT fk_voto_votacion FOREIGN KEY (votacion_id)
        REFERENCES votaciones(id) ON DELETE CASCADE,
    CONSTRAINT fk_voto_opcion FOREIGN KEY (opcion_votacion_id)
        REFERENCES opciones_votacion(id) ON DELETE CASCADE
    -- NOTA DE SEGURIDAD: sin FK hacia usuarios; el voto es 100% anónimo.
);

-- Acta oficial de escrutinio (una por votación cerrada)
CREATE TABLE actas_escrutinio (
    id SERIAL PRIMARY KEY,
    votacion_id INT NOT NULL UNIQUE,
    fecha_cierre TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_padron_habilitado INT NOT NULL,
    total_participantes INT NOT NULL,
    total_votos_urna INT NOT NULL,
    archivo_pdf_url VARCHAR(255) NOT NULL,
    hash_sello_bd VARCHAR(256) NOT NULL,
    CONSTRAINT fk_acta_votacion FOREIGN KEY (votacion_id)
        REFERENCES votaciones(id) ON DELETE CASCADE
);

-- =========================================================
-- MÓDULO 4: AUDITORÍA Y TRAZABILIDAD (CU-09)
-- =========================================================

CREATE TABLE logs_auditoria_eventos (
    id SERIAL PRIMARY KEY,
    usuario_id INT NULL,
    modulo VARCHAR(50) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    detalles_json JSONB NULL,
    ip_origen VARCHAR(45) NOT NULL,
    hash_trazabilidad VARCHAR(256) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_log_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id) ON DELETE SET NULL
);
