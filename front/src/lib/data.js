/* Datos mock y catálogos del prototipo.
   Más adelante se reemplazan por las respuestas reales de la API Django. */
import { reactive } from 'vue'

export const db = reactive({
  usuarios: [
    { id: 1, documento: '100200300',  nombres: 'Laura',    apellidos: 'Restrepo',  correo: 'laura.restrepo@uni.edu.co',   rol: 'ADMIN',       estado: 'ACTIVO',     intentos: 0 },
    { id: 2, documento: '100200301',  nombres: 'Andrés',   apellidos: 'Catalán',  correo: 'andres.catalan@uni.edu.co',   rol: 'ORGANIZADOR', estado: 'ACTIVO',     intentos: 0 },
    { id: 3, documento: '100200302',  nombres: 'Martha',   apellidos: 'Lucumí',   correo: 'martha.lucumi@uni.edu.co',    rol: 'AUDITOR',    estado: 'ACTIVO',     intentos: 0 },
    { id: 4, documento: '1015487962', nombres: 'Cardina',  apellidos: 'Rentería', correo: 'cardi.renteria@uni.edu.co',   rol: 'VOTANTE',    estado: 'ACTIVO',     intentos: 0 },
    { id: 5, documento: '1015987412', nombres: 'Sofía',    apellidos: 'Márquez',  correo: 'sofia.marquez@uni.edu.co',    rol: 'VOTANTE',    estado: 'ACTIVO',     intentos: 1 },
    { id: 6, documento: '1023654789', nombres: 'Julián',   apellidos: 'Ospina',   correo: 'julian.ospina@uni.edu.co',    rol: 'VOTANTE',    estado: 'SUSPENDIDO', intentos: 5 },
    { id: 7, documento: '1025898741', nombres: 'Valeria',  apellidos: 'Caicedo',  correo: 'valeria.caicedo@uni.edu.co',  rol: 'VOTANTE',    estado: 'ACTIVO',     intentos: 0 },
    { id: 8, documento: '1033458965', nombres: 'Camilo',   apellidos: 'Angulo',   correo: 'camilo.angulo@uni.edu.co',    rol: 'VOTANTE',    estado: 'INACTIVO',   intentos: 0 },
    { id: 9, documento: '1036985214', nombres: 'Daniela',  apellidos: 'Mosquera', correo: 'daniela.mosquera@uni.edu.co', rol: 'VOTANTE',    estado: 'ACTIVO',     intentos: 0 },
    { id: 10, documento: '1045238965', nombres: 'Sebastián',apellidos: 'Bonilla', correo: 'sebastian.bonilla@uni.edu.co',rol: 'VOTANTE',    estado: 'ACTIVO',     intentos: 0 },
  ],

  roles: ['ADMIN', 'ORGANIZADOR', 'VOTANTE', 'AUDITOR'],

  modulos: [
    { key: 'usuarios',   label: 'Usuarios' },
    { key: 'elecciones', label: 'Elecciones' },
    { key: 'candidatos', label: 'Candidatos' },
    { key: 'normativas', label: 'Normativas' },
    { key: 'multimedia', label: 'Multimedia' },
    { key: 'voto',       label: 'Emitir voto' },
    { key: 'resultados', label: 'Resultados' },
    { key: 'auditoria',  label: 'Auditoría' },
  ],

  permisos: {
    ADMIN: {
      usuarios: [true, true, true], elecciones: [true, true, true], candidatos: [true, true, true], normativas: [true, true, true],
      multimedia: [true, true, true], voto: [true, true, true], resultados: [true, true, true], auditoria: [true, true, true],
    },
    ORGANIZADOR: {
      usuarios: [false, false, false], elecciones: [true, true, false], candidatos: [true, true, false], normativas: [true, true, false],
      multimedia: [true, true, false], voto: [false, false, false], resultados: [true, false, false], auditoria: [false, false, false],
    },
    VOTANTE: {
      usuarios: [false, false, false], elecciones: [true, false, false], candidatos: [true, false, false], normativas: [true, false, false],
      multimedia: [false, false, false], voto: [true, true, false], resultados: [true, false, false], auditoria: [false, false, false],
    },
    AUDITOR: {
      usuarios: [true, false, false], elecciones: [true, false, false], candidatos: [true, false, false], normativas: [true, false, false],
      multimedia: [false, false, false], voto: [false, false, false], resultados: [true, false, false], auditoria: [true, false, false],
    },
  },

  categorias: [
    {
      id: 1,
      titulo: 'Elecciones Estudiantiles 2026',
      descripcion: 'Elección del Consejo Estudiantil, representantes de facultad y contralor estudiantil.',
      apertura: '2026-10-11T07:00',
      cierre: '2026-10-12T20:00',
      estado: 'ACTIVA',
      enVivo: true,
      candidatos: [
        { id: 1, nombre: 'Martín Idárraga',  lista: 'Lista 1 · Progreso Universitario', orden: 1, esBlanco: false },
        { id: 2, nombre: 'Sara Valencia',    lista: 'Lista 2 · Unidad Estudiantil',     orden: 2, esBlanco: false },
        { id: 3, nombre: 'Kevin Armijo',     lista: 'Lista 3 · Cambio Ya',              orden: 3, esBlanco: false },
        { id: 4, nombre: 'Natalia Quintero', lista: 'Lista 4 · Voz Campus',             orden: 4, esBlanco: false },
        { id: 5, nombre: 'Voto en Blanco',   lista: 'Ninguna de las anteriores',        orden: 5, esBlanco: true },
      ],
      resultados: [312, 268, 187, 143, 96],
      padron: 2450,
      participantes: 1006,
    },
    {
      id: 2,
      titulo: 'Consejo de Facultad de Ingeniería',
      descripcion: 'Elección de representantes estudiantiles al consejo de facultad.',
      apertura: '2026-11-02T06:00',
      cierre: '2026-11-03T18:00',
      estado: 'PROGRAMADA',
      enVivo: false,
      candidatos: [],
      resultados: [0, 0],
      padron: 890,
      participantes: 0,
    },
    {
      id: 3,
      titulo: 'Elecciones de Personería 2025',
      descripcion: 'Proceso finalizado. Acta de escrutinio disponible.',
      apertura: '2025-09-15T07:00',
      cierre: '2025-09-16T16:00',
      estado: 'FINALIZADA',
      enVivo: false,
      candidatos: [
        { id: 10, nombre: 'Laura Vélez', lista: 'Lista A', orden: 1, esBlanco: false },
        { id: 11, nombre: 'Tomás Gil',   lista: 'Lista B', orden: 2, esBlanco: false },
      ],
      resultados: [1204, 863],
      padron: 3100,
      participantes: 2102,
    },
  ],

  normativas: [
    { id: 1, categoriaId: 1, titulo: 'Reglamento Electoral Estudiantil', pdf: 'reglamento-electoral.pdf', peso: '2.4 MB', fecha: '2026-09-28' },
    { id: 2, categoriaId: 1, titulo: 'Acuerdo 004 de 2026 — Cronograma', pdf: 'acuerdo-004.pdf', peso: '880 KB', fecha: '2026-09-30' },
  ],

  multimedia: [
    { id: 1, nombre: 'foto-candidato-01.jpg', tipo: 'image/jpeg', peso: '240 KB', etiqueta: 'Lista 1' },
    { id: 2, nombre: 'foto-candidato-02.jpg', tipo: 'image/jpeg', peso: '210 KB', etiqueta: 'Lista 2' },
    { id: 3, nombre: 'banner-principal.png',  tipo: 'image/png',  peso: '1.1 MB', etiqueta: 'Banner' },
    { id: 4, nombre: 'logo-consejo.svg',      tipo: 'image/svg+xml', peso: '18 KB', etiqueta: 'Logo' },
  ],

  certificados: [
    { id: 1, categoriaId: 3, titulo: 'Elecciones de Personería 2025', fecha: '2025-09-16', codigo: 'CERT-2025-9F3A2B', hash: 'a3f5c2d9e1b8476093f5c2d9e1b8476093f5c2d9e1b8476093f5c2d9e1b847609' },
  ],

  logs: [
    { id: 91, usuario: 'Sistema',   modulo: 'voto',       accion: 'voto.registrado',     ip: '10.0.3.21',    hash: '9f2c…71ab', ts: '2026-10-11 09:41:12' },
    { id: 90, usuario: 'laura.r',   modulo: 'usuarios',   accion: 'usuario.suspendido',  ip: '192.168.1.14', hash: '4b8e…0c3d', ts: '2026-10-11 09:12:45' },
    { id: 89, usuario: 'Sistema',   modulo: 'sesiones',   accion: 'token.refresh',       ip: '10.0.3.9',     hash: '77a1…9e22', ts: '2026-10-11 09:02:03' },
    { id: 88, usuario: 'andres.c',  modulo: 'elecciones', accion: 'categoria.activada',  ip: '192.168.1.33', hash: '1d9f…44b7', ts: '2026-10-11 06:58:30' },
    { id: 87, usuario: 'andres.c',  modulo: 'candidatos', accion: 'tarjeton.reordenado', ip: '192.168.1.33', hash: 'c204…8fa1', ts: '2026-10-11 06:55:11' },
    { id: 86, usuario: 'Sistema',   modulo: 'auditoria',  accion: 'consistencia.ok',     ip: '127.0.0.1',    hash: 'e5b3…2d60', ts: '2026-10-11 06:00:00' },
    { id: 85, usuario: 'julian.o',  modulo: 'auth',       accion: 'login.bloqueado',     ip: '192.168.1.77', hash: '8cc7…1f09', ts: '2026-10-10 22:14:52' },
    { id: 84, usuario: 'laura.r',   modulo: 'usuarios',   accion: 'carga.masiva.csv',    ip: '192.168.1.14', hash: '2ae9…77c4', ts: '2026-10-10 18:40:19' },
  ],

  consistencia: { padron: 2450, participantes: 1006, votosUrna: 1006, blancos: 96, abstencion: 1444 },
})

export const state = reactive({
  estadoEleccion: 'ACTIVA',
  enVivo: true,
  seleccionVoto: null,
  votoEmitido: false,
  hashVoto: null,
})

export const ESTADOS = {
  BORRADOR:   { label: 'Borrador',   cls: 'badge-muted' },
  PROGRAMADA: { label: 'Programada', cls: 'badge-info' },
  ACTIVA:     { label: 'Activa',     cls: 'badge-success' },
  CERRANDO:   { label: 'Cerrando',   cls: 'badge-warning' },
  FINALIZADA: { label: 'Finalizada', cls: 'badge-secondary' },
}

export const ESTADO_USUARIO = {
  ACTIVO:     { label: 'Activo',     cls: 'badge-success' },
  SUSPENDIDO: { label: 'Suspendido', cls: 'badge-destructive' },
  INACTIVO:   { label: 'Inactivo',   cls: 'badge-muted' },
}

export const CUENTAS_DEMO = [
  { rol: 'ADMIN',       nombre: 'Laura Restrepo',   doc: '100200300',  pass: 'admin123' },
  { rol: 'ORGANIZADOR', nombre: 'Andrés Catalán',   doc: '100200301',  pass: 'org123' },
  { rol: 'VOTANTE',     nombre: 'Cardina Rentería', doc: '1015487962', pass: 'voto123' },
  { rol: 'AUDITOR',     nombre: 'Martha Lucumí',    doc: '100200302',  pass: 'aud123' },
]

export const HOME = { ADMIN: '/admin', ORGANIZADOR: '/org', VOTANTE: '/votante', AUDITOR: '/auditor' }

export const MENUS = {
  ADMIN: [
    { seccion: 'General' },
    { to: '/admin',           label: 'Dashboard',                  icon: 'layout' },
    { seccion: 'Módulo 1 · Usuarios y seguridad' },
    { to: '/admin/usuarios',  label: 'Usuarios (CU-02)',           icon: 'users' },
    { to: '/admin/carga',     label: 'Registro / Carga (CU-01)',   icon: 'userPlus' },
    { to: '/admin/permisos',  label: 'Permisos RBAC (CU-03)',      icon: 'key' },
  ],
  ORGANIZADOR: [
    { seccion: 'General' },
    { to: '/org',             label: 'Dashboard',                  icon: 'layout' },
    { seccion: 'Módulo 2 · Configuración' },
    { to: '/org/categorias',  label: 'Categorías (CU-04)',         icon: 'calendar' },
    { to: '/org/normativas',  label: 'Normativas (CU-05)',         icon: 'fileText' },
    { to: '/org/multimedia',  label: 'Multimedia (CU-06)',         icon: 'image' },
    { to: '/org/tarjeton',    label: 'Tarjetón (CU-10)',           icon: 'checkSquare' },
    { seccion: 'Módulo 3 · Proceso' },
    { to: '/org/cierre',      label: 'Cerrar elección (CU-11)',    icon: 'award' },
  ],
  VOTANTE: [
    { seccion: 'Proceso electoral' },
    { to: '/votante',              label: 'Inicio',               icon: 'layout' },
    { to: '/votante/tarjeton',     label: 'Emitir voto (CU-07)',  icon: 'vote' },
    { to: '/votante/resultados',   label: 'Resultados (CU-08)',   icon: 'chart' },
    { seccion: 'Personal' },
    { to: '/votante/certificados', label: 'Mis certificados (CU-12)', icon: 'award' },
  ],
  AUDITOR: [
    { seccion: 'Supervisión' },
    { to: '/auditor',       label: 'Resultados (CU-08)', icon: 'chart' },
    { to: '/auditor/logs',  label: 'Auditoría (CU-09)',  icon: 'scroll' },
  ],
}

export function fmtFecha(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function fmtNum(n) {
  return Number(n || 0).toLocaleString('es-CO')
}

export function sha256Mock() {
  const hex = '0123456789abcdef'
  let out = ''
  for (let i = 0; i < 64; i++) out += hex[Math.floor(Math.random() * 16)]
  return out
}

export function iniciales(nombre) {
  return String(nombre || '')
    .split(' ')
    .filter(Boolean)
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

const AVATAR_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4']

export function avatarColor(nombre) {
  let h = 0
  for (const c of String(nombre || '')) h = (h * 31 + c.charCodeAt(0)) % AVATAR_COLORS.length
  return AVATAR_COLORS[h]
}
