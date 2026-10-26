import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '../stores/session'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true, title: 'Iniciar sesión' },
  },
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    children: [
      {
        path: 'admin',
        name: 'admin',
        component: () => import('../views/admin/AdminDashboard.vue'),
        meta: { title: 'Dashboard', sub: 'Resumen general del sistema', roles: ['ADMIN'] },
      },
      {
        path: 'admin/usuarios',
        name: 'admin-usuarios',
        component: () => import('../views/admin/AdminUsuarios.vue'),
        meta: { title: 'Usuarios', sub: 'CU-02 · Gestión de cuentas y estados', roles: ['ADMIN'] },
      },
      {
        path: 'admin/carga',
        name: 'admin-carga',
        component: () => import('../views/admin/AdminCarga.vue'),
        meta: { title: 'Registro / Carga', sub: 'CU-01 · Alta individual y carga masiva de votantes', roles: ['ADMIN'] },
      },
      {
        path: 'admin/permisos',
        name: 'admin-permisos',
        component: () => import('../views/admin/AdminPermisos.vue'),
        meta: { title: 'Permisos RBAC', sub: 'CU-03 · Matriz de roles y módulos', roles: ['ADMIN'] },
      },
      {
        path: 'org',
        name: 'org',
        component: () => import('../views/org/OrgDashboard.vue'),
        meta: { title: 'Dashboard', sub: 'Resumen de la elección a tu cargo', roles: ['ORGANIZADOR'] },
      },
      {
        path: 'org/categorias',
        name: 'org-categorias',
        component: () => import('../views/org/OrgCategorias.vue'),
        meta: { title: 'Categorías', sub: 'CU-04 · Configuración de la elección', roles: ['ORGANIZADOR'] },
      },
      {
        path: 'org/normativas',
        name: 'org-normativas',
        component: () => import('../views/org/OrgNormativas.vue'),
        meta: { title: 'Normativas', sub: 'CU-05 · Reglamento y documentos', roles: ['ORGANIZADOR'] },
      },
      {
        path: 'org/multimedia',
        name: 'org-multimedia',
        component: () => import('../views/org/OrgMultimedia.vue'),
        meta: { title: 'Multimedia', sub: 'CU-06 · Fotos y recursos de candidatos', roles: ['ORGANIZADOR'] },
      },
      {
        path: 'org/tarjeton',
        name: 'org-tarjeton',
        component: () => import('../views/org/OrgTarjeton.vue'),
        meta: { title: 'Tarjetón', sub: 'CU-10 · Orden de casillas y vista previa', roles: ['ORGANIZADOR'] },
      },
      {
        path: 'org/cierre',
        name: 'org-cierre',
        component: () => import('../views/org/OrgCierre.vue'),
        meta: { title: 'Cerrar elección', sub: 'CU-11 · Escrutinio y acta final', roles: ['ORGANIZADOR'] },
      },
      {
        path: 'votante',
        name: 'votante',
        component: () => import('../views/votante/VotanteInicio.vue'),
        meta: { title: 'Inicio', sub: 'Proceso electoral del votante', roles: ['VOTANTE'] },
      },
      {
        path: 'votante/tarjeton',
        name: 'votante-tarjeton',
        component: () => import('../views/votante/VotanteTarjeton.vue'),
        meta: { title: 'Emitir voto', sub: 'CU-07 · Tarjetón electoral', roles: ['VOTANTE'] },
      },
      {
        path: 'votante/comprobante',
        name: 'votante-comprobante',
        component: () => import('../views/votante/VotanteComprobante.vue'),
        meta: { title: 'Comprobante', sub: 'Constancia anónima de participación', roles: ['VOTANTE'] },
      },
      {
        path: 'votante/resultados',
        name: 'votante-resultados',
        component: () => import('../views/votante/VotanteResultados.vue'),
        meta: { title: 'Resultados', sub: 'CU-08 · Avance y resultados finales', roles: ['VOTANTE'] },
      },
      {
        path: 'votante/certificados',
        name: 'votante-certificados',
        component: () => import('../views/votante/VotanteCertificados.vue'),
        meta: { title: 'Mis certificados', sub: 'CU-12 · Historial de participación', roles: ['VOTANTE'] },
      },
      {
        path: 'auditor',
        name: 'auditor',
        component: () => import('../views/auditor/AuditorResultados.vue'),
        meta: {
          title: 'Panel de resultados',
          sub: 'CU-08 · Visualizar resultados en tiempo real',
          roles: ['AUDITOR', 'ADMIN'],
        },
      },
      {
        path: 'auditor/logs',
        name: 'auditor-logs',
        component: () => import('../views/auditor/AuditorLogs.vue'),
        meta: {
          title: 'Auditoría del proceso',
          sub: 'CU-09 · Auditar proceso de votación (solo lectura)',
          roles: ['AUDITOR', 'ADMIN'],
        },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const session = useSessionStore()

  if (to.meta.public) {
    return session.isAuthenticated ? session.home : true
  }

  if (!session.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const roles = to.meta.roles
  if (Array.isArray(roles) && roles.length && !roles.includes(session.role)) {
    return session.home
  }

  return true
})

export default router
