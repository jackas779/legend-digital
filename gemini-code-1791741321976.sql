-- =========================================================
-- MÓDULO 1: SEGURIDAD, AUTENTICACIÓN Y RBAC (CU-00, CU-01, CU-02, CU-03)
-- =========================================================

-- Roles del sistema (Administrador, Organizador, Votante, Auditor)
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

-- Permisos atómicos del sistema (CU-03)
CREATE TABLE permisos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(100) NOT NULL UNIQUE, -- Ej: 'categorias.crear', 'voto.emitir'
    modulo VARCHAR(50) NOT NULL,
    descripcion TEXT
);

-- Tabla intermedia para relación M:N de Roles y Permisos (RBAC - CU-03)
CREATE TABLE rol_permisos (
    rol_id INT NOT NULL,
    permiso_id INT NOT NULL,
    PRIMARY KEY (rol_id, permiso_id),
    CONSTRAINT fk_rp_rol FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_rp_permiso FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
);

-- Usuarios y Padrón Electoral (CU-00, CU-01, CU-02)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    documento VARCHAR(20) NOT NULL UNIQUE, -- Llave de unicidad electoral
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'ACTIVO', -- ACTIVO, SUSPENDIDO, INACTIVO
    intentos_fallidos INT DEFAULT 0, -- Para bloqueo de seguridad (CU-00)
    bloqueado_hasta TIMESTAMP NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_rol FOREIGN KEY (rol_id) REFERENCES roles(id)
);

-- Sesiones y Tokens JWT / Refresh (CU-00)
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
-- MÓDULO 2: CONFIGURACIÓN ELECTORAL Y CONTENIDOS (CU-04, CU-05, CU-06, CU-10)
-- =========================================================

-- Categorías o Elecciones (CU-04)
CREATE TABLE categorias_electorales (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    fecha_apertura TIMESTAMP NOT NULL,
    fecha_cierre TIMESTAMP NOT NULL,
    estado VARCHAR(20) DEFAULT 'BORRADOR', -- BORRADOR, PROGRAMADA, ACTIVA, CERRANDO, FINALIZADA
    mostrar_resultados_en_vivo BOOLEAN DEFAULT FALSE,
    creador_usuario_id INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_categoria_creador FOREIGN KEY (creador_usuario_id) REFERENCES usuarios(id)
);

-- Normativas y Reglamentos (CU-05)
CREATE TABLE normativas (
    id SERIAL PRIMARY KEY,
    categoria_id INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    contenido_html TEXT,
    archivo_pdf_url VARCHAR(255),
    fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_normativa_categoria FOREIGN KEY (categoria_id) REFERENCES categorias_electorales(id) ON DELETE CASCADE
);

-- Gestión de Archivos e Imágenes (CU-06)
CREATE TABLE recursos_multimedia (
    id SERIAL PRIMARY KEY,
    nombre_archivo VARCHAR(150) NOT NULL,
    url_publica VARCHAR(255) NOT NULL,
    tipo_mime VARCHAR(50) NOT NULL, -- image/png, image/jpeg, etc.
    peso_bytes INT NOT NULL,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Candidatos u Opciones de Voto (CU-10)
CREATE TABLE candidatos_opciones (
    id SERIAL PRIMARY KEY,
    categoria_id INT NOT NULL,
    nombre_candidato VARCHAR(120) NOT NULL,
    partido_lista VARCHAR(120),
    biografia TEXT,
    orden_casilla INT NOT NULL,
    es_voto_blanco BOOLEAN DEFAULT FALSE,
    foto_recurso_id INT NULL,
    CONSTRAINT fk_candidato_categoria FOREIGN KEY (categoria_id) REFERENCES categorias_electorales(id) ON DELETE CASCADE,
    CONSTRAINT fk_candidato_foto FOREIGN KEY (foto_recurso_id) REFERENCES recursos_multimedia(id) ON DELETE SET NULL,
    CONSTRAINT uq_categoria_casilla UNIQUE (categoria_id, orden_casilla) -- Evita choque de casillas
);

-- =========================================================
-- MÓDULO 3: URNA DIGITAL Y CERTIFICACIÓN (CU-07, CU-08, CU-11, CU-12)
-- =========================================================

-- Padrón de Asistencia / Marca de Participación (CU-07)
CREATE TABLE participacion_votantes (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    categoria_id INT NOT NULL,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hash_comprobante VARCHAR(256) NOT NULL UNIQUE, -- SHA-256
    CONSTRAINT fk_part_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_part_categoria FOREIGN KEY (categoria_id) REFERENCES categorias_electorales(id) ON DELETE CASCADE,
    CONSTRAINT uq_usuario_categoria UNIQUE (usuario_id, categoria_id) -- 🚨 Evita el doble voto
);

-- Urna Digital de Votos Anónimos (CU-07)
CREATE TABLE urna_digital_votos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- ID no secuencial
    categoria_id INT NOT NULL,
    candidato_id INT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    firma_criptografica VARCHAR(256) NOT NULL, -- Sello del voto
    CONSTRAINT fk_urna_categoria FOREIGN KEY (categoria_id) REFERENCES categorias_electorales(id) ON DELETE CASCADE,
    CONSTRAINT fk_urna_candidato FOREIGN KEY (candidato_id) REFERENCES candidatos_opciones(id) ON DELETE CASCADE
    -- 🚨 NOTA DE SEGURIDAD: Sin FK hacia 'usuarios'. Voto 100% anónimo.
);

-- Certificados Digitales de Participación (CU-12)
CREATE TABLE certificados_votacion (
    id SERIAL PRIMARY KEY,
    participacion_id INT NOT NULL UNIQUE,
    codigo_certificado VARCHAR(100) NOT NULL UNIQUE,
    qr_verificacion_url TEXT NOT NULL,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cert_participacion FOREIGN KEY (participacion_id) REFERENCES participacion_votantes(id) ON DELETE CASCADE
);

-- Acta Oficial de Escrutinio y Cierre (CU-11)
CREATE TABLE actas_escrutinio (
    id SERIAL PRIMARY KEY,
    categoria_id INT NOT NULL UNIQUE,
    fecha_cierre TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_padron_habilitado INT NOT NULL,
    total_participantes INT NOT NULL,
    total_votos_urna INT NOT NULL,
    archivo_pdf_url VARCHAR(255) NOT NULL,
    hash_sello_bd VARCHAR(256) NOT NULL,
    CONSTRAINT fk_acta_categoria FOREIGN KEY (categoria_id) REFERENCES categorias_electorales(id) ON DELETE CASCADE
);

-- =========================================================
-- MÓDULO 4: AUDITORÍA Y TRAZABILIDAD (CU-09)
-- =========================================================

-- Logs de Auditoría Inalterables (CU-09)
CREATE TABLE logs_auditoria_eventos (
    id SERIAL PRIMARY KEY,
    usuario_id INT NULL, -- Nulo si es un evento automático del servidor
    modulo VARCHAR(50) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    detalles_json JSONB NULL, -- Guarda estados anteriores/posteriores o IPs
    ip_origen VARCHAR(45) NOT NULL,
    hash_trazabilidad VARCHAR(256) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_log_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);