/* ui.js — Helpers de interfaz reutilizables */

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function fmtFecha(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
}

function fmtNum(n) { return n.toLocaleString('es-CO'); }

/* ---------- Toasts ---------- */
function toast(mensaje, tipo = 'success') {
  let cont = document.querySelector('.toast-container');
  if (!cont) { cont = document.createElement('div'); cont.className = 'toast-container'; document.body.appendChild(cont); }
  const iconos = { success: Icons.check, destructive: Icons.alert, warning: Icons.alert, info: Icons.info };
  const el = document.createElement('div');
  el.className = `toast ${tipo}`;
  el.innerHTML = `<span class="t-icon">${iconos[tipo] || Icons.info(18)}</span><span>${esc(mensaje)}</span>`;
  cont.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(30px)'; el.style.transition = 'all .3s'; setTimeout(() => el.remove(), 300); }, 3400);
}

/* ---------- Modal ---------- */
let modalAbierto = null;

function modal({ icon = 'primary', iconSvg = Icons.info(20), titulo, desc = '', body = '', footer = null, onClose = null, ancho = 470 }) {
  cerrarModal();
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal" style="max-width:${ancho}px" role="dialog">
      <div class="modal-header">
        <div class="mh-icon ${icon}">${iconSvg}</div>
        <div style="flex:1">
          <div class="modal-title">${esc(titulo)}</div>
          ${desc ? `<div class="modal-desc">${desc}</div>` : ''}
        </div>
      </div>
      <div class="modal-body">${body}</div>
      <div class="modal-footer"></div>
    </div>`;
  document.body.appendChild(overlay);
  modalAbierto = overlay;
  const f = overlay.querySelector('.modal-footer');
  if (footer) f.innerHTML = footer;
  else f.innerHTML = `<button class="btn btn-secondary" data-close>Cerrar</button>`;
  overlay.addEventListener('click', e => { if (e.target === overlay || e.target.closest('[data-close]')) cerrarModal(); });
  overlay.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', cerrarModal));
  if (onClose) overlay._onClose = onClose;
  return overlay;
}

function cerrarModal() {
  if (modalAbierto) { if (modalAbierto._onClose) modalAbierto._onClose(); modalAbierto.remove(); modalAbierto = null; }
}

function confirmar({ titulo, desc, textoBtn = 'Confirmar', clase = 'btn-destructive', iconSvg = Icons.alert(20), onOk }) {
  modal({
    icon: 'destructive', iconSvg, titulo, desc,
    footer: `<button class="btn btn-secondary" data-close>Cancelar</button>
              <button class="btn ${clase}" id="__ok">${esc(textoBtn)}</button>`,
  });
  document.getElementById('__ok').addEventListener('click', () => { cerrarModal(); onOk && onOk(); });
}

/* ---------- Badges ---------- */
function badgeEstado(estado) { const e = ESTADOS[estado] || ESTADOS.BORRADOR; return `<span class="badge ${e.cls}">${e.label}</span>`; }
function badgeUsuario(estado) { const e = ESTADO_USUARIO[estado] || ESTADO_USUARIO.INACTIVO; return `<span class="badge ${e.cls}">${e.label}</span>`; }

/* ---------- Switch ---------- */
function switchToggle(id, checked, onChange) {
  return `<label class="switch"><input type="checkbox" id="${id}" ${checked ? 'checked' : ''}><span class="slider"></span></label>`;
}

/* ---------- Tabs ---------- */
function tabsHTML(tabs, activo) {
  return `<div class="tabs">${tabs.map(t => `<button class="tab ${t.id === activo ? 'active' : ''}" data-tab="${t.id}">${esc(t.label)}</button>`).join('')}</div>`;
}

/* ---------- KPI ---------- */
function kpi({ label, valor, icono, tendencia, tendCls = 'neutral', sub }) {
  return `<div class="card kpi">
    <div class="kpi-label">${icono || ''}${esc(label)}</div>
    <div class="kpi-value">${valor}</div>
    ${tendencia ? `<div class="kpi-trend ${tendCls}">${tendencia}</div>` : sub ? `<div class="kpi-trend neutral">${sub}</div>` : ''}
  </div>`;
}

/* ---------- Donut SVG ---------- */
function donut(participios, total, label) {
  const pct = total ? Math.round((participios / total) * 100) : 0;
  const r = 58, C = 2 * Math.PI * r;
  return `<div class="donut-wrap">
    <div class="donut">
      <svg width="150" height="150">
        <circle cx="75" cy="75" r="${r}" fill="none" stroke="hsl(var(--muted))" stroke-width="14"/>
        <circle cx="75" cy="75" r="${r}" fill="none" stroke="hsl(var(--primary))" stroke-width="14"
          stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C - (C * pct) / 100}" style="transition:stroke-dashoffset 1s"/>
      </svg>
      <div class="donut-center"><div><div class="pct">${pct}%</div><div class="lbl">${esc(label)}</div></div></div>
    </div>
    <div class="legend" id="donut-legend"></div>
  </div>`;
}

/* ---------- Barras ---------- */
function barras(items, total) {
  const max = Math.max(...items.map(i => i.valor), 1);
  return items.map(it => `
    <div class="bar-row">
      <div class="bar-label" title="${esc(it.nombre)}">${esc(it.nombre)}</div>
      <div class="bar-track"><div class="bar-fill ${it.cls || ''}" style="width:${(it.valor / max) * 100}%"></div></div>
      <div class="bar-val">${fmtNum(it.valor)}</div>
    </div>`).join('');
}
