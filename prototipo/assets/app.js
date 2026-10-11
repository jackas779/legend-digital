/* app.js — Layout, router y arranque del prototipo */

const Vistas = {}; // key -> { titulo, sub, render }

function RegistrarVista(key, def) { Vistas[key] = def; }

const MENUS = {
  ADMIN: [
    { seccion: 'General' },
    { ruta: 'admin',            label: 'Dashboard',            icono: Icons.layout(17) },
    { seccion: 'Módulo 1 · Usuarios y seguridad' },
    { ruta: 'admin/usuarios',   label: 'Usuarios (CU-02)',     icono: Icons.users(17) },
    { ruta: 'admin/carga',      label: 'Registro / Carga (CU-01)', icono: Icons.userPlus(17) },
    { ruta: 'admin/permisos',   label: 'Permisos RBAC (CU-03)', icono: Icons.key(17) },
  ],
  ORGANIZADOR: [
    { seccion: 'General' },
    { ruta: 'org',              label: 'Dashboard',            icono: Icons.layout(17) },
    { seccion: 'Módulo 2 · Configuración' },
    { ruta: 'org/categorias',   label: 'Categorías (CU-04)',   icono: Icons.calendar(17) },
    { ruta: 'org/normativas',   label: 'Normativas (CU-05)',   icono: Icons.fileText(17) },
    { ruta: 'org/multimedia',   label: 'Multimedia (CU-06)',   icono: Icons.image(17) },
    { ruta: 'org/tarjeton',     label: 'Tarjetón (CU-10)',     icono: Icons.checkSquare(17) },
    { seccion: 'Módulo 3 · Proceso' },
    { ruta: 'org/cierre',       label: 'Cerrar elección (CU-11)', icono: Icons.award(17) },
  ],
  VOTANTE: [
    { seccion: 'Proceso electoral' },
    { ruta: 'votante',          label: 'Inicio',               icono: Icons.layout(17) },
    { ruta: 'votante/tarjeton', label: 'Emitir voto (CU-07)',  icono: Icons.vote(17) },
    { ruta: 'votante/resultados', label: 'Resultados (CU-08)', icono: Icons.chart(17) },
    { seccion: 'Personal' },
    { ruta: 'votante/certificados', label: 'Mis certificados (CU-12)', icono: Icons.award(17) },
  ],
  AUDITOR: [
    { seccion: 'Supervisión' },
    { ruta: 'auditor',          label: 'Resultados (CU-08)',   icono: Icons.chart(17) },
    { ruta: 'auditor/logs',     label: 'Auditoría (CU-09)',    icono: Icons.scroll(17) },
  ],
};

const HOME = { ADMIN: 'admin', ORGANIZADOR: 'org', VOTANTE: 'votante', AUDITOR: 'auditor' };

/* ================= Render principal ================= */
function Render() {
  const app = document.getElementById('app');
  if (!State.user) { VistaLogin(); return; }
  renderLayout(app);
}

function renderLayout(app) {
  const rol = State.user.rol;
  const menu = MENUS[rol];
  const hash = location.hash.replace(/^#\//, '') || HOME[rol];
  const rutaActiva = Vistas[hash] ? hash : HOME[rol];

  const itemsHtml = menu.map(m => {
    if (m.seccion) return `<div class="nav-section">${esc(m.seccion)}</div>`;
    const activo = m.ruta === rutaActiva;
    return `<a class="nav-item ${activo ? 'active' : ''}" href="#/${m.ruta}">
      ${m.icono}<span>${esc(m.label)}</span>
    </a>`;
  }).join('');

  app.innerHTML = `
  <div class="sidebar-overlay" id="sb-overlay"></div>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">${Icons.vote(19)}</div>
        <div><h1>Votación Segura</h1><span>Universidad 2026</span></div>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section" style="padding-top:2px">${esc(rol)}</div>
        ${itemsHtml}
      </nav>
      <div class="sidebar-footer">
        <div class="user-chip">
          ${avatar(State.user.nombre, 34)}
          <div class="uc-info">
            <div class="uc-name">${esc(State.user.nombre)}</div>
            <div class="uc-rol">${esc(State.user.rol)}</div>
          </div>
          <button class="icon-btn" style="width:32px;height:32px" id="btn-logout" title="Cerrar sesión">${Icons.logout(15)}</button>
        </div>
      </div>
    </aside>
    <div class="main">
      <header class="topbar">
        <button class="icon-btn" id="btn-menu" title="Menú">${Icons.grip(16)}</button>
        <div>
          <div class="page-title" id="topbar-titulo">—</div>
          <div class="page-sub" id="topbar-sub"></div>
        </div>
        <div class="topbar-actions">
          <div class="search-box">${Icons.search(15)}<input placeholder="Buscar…"></div>
          ${State.enVivo ? `<span class="badge badge-success en-vivo" style="gap:6px"><span style="width:7px;height:7px;border-radius:50%;background:hsl(var(--success));animation:pulse 1.4s infinite"></span>EN VIVO</span>` : ''}
          <button class="icon-btn" id="btn-tema" title="Cambiar tema">${document.documentElement.classList.contains('dark') ? Icons.sun(16) : Icons.moon(16)}</button>
          <button class="icon-btn bell" title="Notificaciones">${Icons.bell(16)}<span class="dot"></span></button>
          ${avatar(State.user.nombre, 34)}
        </div>
        <div class="sim-wrap" title="Simulador de estado de la elección (prototipo)">
          <span class="text-sm text-muted fw-600 sim-label" style="white-space:nowrap">Estado:</span>
          <select class="select" style="width:auto;padding:6px 30px 6px 10px;font-size:12.5px" id="sim-estado">
            ${Object.keys(ESTADOS).map(e => `<option value="${e}" ${State.estadoEleccion === e ? 'selected' : ''}>${ESTADOS[e].label}</option>`).join('')}
          </select>
        </div>
      </header>
      <main class="content" id="vista-contenido"></main>
    </div>
  </div>`;

  // Eventos globales del layout
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sb-overlay');
  const cerrarDrawer = () => { sidebar.classList.remove('open'); overlay.classList.remove('show'); };

  document.getElementById('btn-menu').addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
  });
  overlay.addEventListener('click', cerrarDrawer);
  document.querySelectorAll('.nav-item').forEach(a => a.addEventListener('click', cerrarDrawer));

  document.getElementById('btn-logout').addEventListener('click', () => {
    State.user = null; State.votoEmitido = false; State.seleccionVoto = null;
    if (State.intervaloRT) { clearInterval(State.intervaloRT); State.intervaloRT = null; }
    location.hash = '#/login';
  });
  document.getElementById('btn-tema').addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    State.tema = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    try { localStorage.setItem('vs-tema', State.tema); } catch (e) {}
    Render();
  });
  document.getElementById('sim-estado').addEventListener('change', e => {
    State.estadoEleccion = e.target.value;
    Render();
    toast(`Elección en estado: ${ESTADOS[State.estadoEleccion].label}`, 'info');
  });

  renderVista(rutaActiva);
}

function renderVista(key) {
  const cont = document.getElementById('vista-contenido');
  const vista = Vistas[key];
  const titulo = document.getElementById('topbar-titulo');
  const sub = document.getElementById('topbar-sub');
  // Cierra el drawer móvil al navegar (botón atrás, hash directo, etc.)
  document.querySelector('.sidebar')?.classList.remove('open');
  document.querySelector('.sidebar-overlay')?.classList.remove('show');
  if (!vista) { cont.innerHTML = `<div class="card card-body">Vista no encontrada</div>`; return; }
  titulo.textContent = vista.titulo;
  sub.textContent = vista.sub || '';
  const { html, mount } = vista.render();
  cont.innerHTML = html;
  if (mount) mount(cont);
}

/* ================= Router ================= */
function Router() {
  if (!State.user) {
    if (location.hash && location.hash !== '#/login') location.hash = '#/login';
    VistaLogin();
    return;
  }
  if (!location.hash || location.hash === '#/login' || location.hash === '#/') {
    location.hash = '#/' + HOME[State.user.rol];
    return;
  }
  const key = location.hash.replace(/^#\//, '');
  if (!Vistas[key]) { location.hash = '#/' + HOME[State.user.rol]; return; }
  if (!State.user) { location.hash = '#/login'; return; }
  renderLayout(document.getElementById('app'));
}

window.addEventListener('hashchange', Router);

/* ================= Arranque ================= */
function init() {
  try {
    const t = localStorage.getItem('vs-tema');
    if (t === 'light') document.documentElement.classList.remove('dark');
  } catch (e) {}
  Router();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

/* estilo pulse para indicador en vivo */
const _st = document.createElement('style');
_st.textContent = '@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}';
document.head.appendChild(_st);
