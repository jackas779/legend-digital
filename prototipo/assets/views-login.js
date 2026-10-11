/* views-login.js — CU-00: Autenticación */

function VistaLogin() {
  const app = document.getElementById('app');
  app.innerHTML = `
  <div class="login-page">
    <div class="login-left">
      <div class="ll-badge">${Icons.shield(14)} Sistema de Votación Seguro</div>
      <h2>Elecciones<br>transparentes y<br>auditables.</h2>
      <p>Plataforma de votación electrónica con trazabilidad criptográfica, anonimato del voto y verificación matemática en tiempo real para toda la comunidad universitaria.</p>
      <div class="login-features">
        <div class="login-feature">
          <div class="lf-icon">${Icons.lock(18)}</div>
          <div><div class="lf-title">Voto 100% anónimo</div><div class="lf-desc">La urna almacena el voto sin vincular identidad. Comprobante con Hash SHA-256.</div></div>
        </div>
        <div class="login-feature">
          <div class="lf-icon">${Icons.scroll(18)}</div>
          <div><div class="lf-title">Auditoría inalterable</div><div class="lf-desc">Registro de eventos con hash de trazabilidad y ecuación de consistencia.</div></div>
        </div>
        <div class="login-feature">
          <div class="lf-icon">${Icons.chart(18)}</div>
          <div><div class="lf-title">Resultados en tiempo real</div><div class="lf-desc">Dashboards dinámicos según las reglas de visibilidad de cada categoría.</div></div>
        </div>
      </div>
      <div class="ll-footer">Prototipo UX/UI · Universidad 2026</div>
    </div>
    <div class="login-right">
      <div class="login-card">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:22px">
          <div class="sidebar-brand" style="border:none;padding:0">
            <div class="brand-icon">${Icons.vote(20)}</div>
            <div><h1>Votación Segura</h1><span>Panel del sistema</span></div>
          </div>
        </div>
        <h3>Iniciar sesión</h3>
        <p class="lc-sub">Ingresa con tu documento o correo institucional</p>

        <div id="login-alerta"></div>

        <form id="login-form">
          <div class="field">
            <label>Documento o correo</label>
            <input class="input" id="login-doc" placeholder="1015487962" autocomplete="username">
          </div>
          <div class="field">
            <label>Contraseña</label>
            <input class="input" id="login-pass" type="password" placeholder="••••••••" autocomplete="current-password">
          </div>
          <button class="btn btn-primary btn-lg btn-block" type="submit" id="login-btn">
            ${Icons.key(17)} Ingresar
          </button>
        </form>

        <div class="demo-users">
          <div class="du-title">Entrar como demo (por rol)</div>
          ${CUENTAS_DEMO.map(c => `
            <button class="demo-user" data-rol="${c.rol}">
              ${avatar(c.nombre, 34)}
              <div style="flex:1;min-width:0">
                <div style="font-size:13px;font-weight:700">${c.nombre}</div>
                <div style="font-size:11.5px;color:hsl(var(--muted-foreground))">${c.rol}</div>
              </div>
              ${Icons.chevronRight(15)}
            </button>`).join('')}
        </div>
      </div>
    </div>
  </div>`;

  // --- Lógica ---
  const alerta = document.getElementById('login-alerta');

  function mostrarAlerta(titulo, texto) {
    alerta.innerHTML = `<div class="alert alert-destructive">
      <span style="flex-shrink:0;margin-top:1px">${Icons.alert(17)}</span>
      <div><div class="alert-title">${esc(titulo)}</div><div class="alert-body">${texto}</div></div>
    </div>`;
  }

  function entrar(usuario) {
    State.user = usuario;
    State.intentosFallidos = 0;
    location.hash = '#/' + ({ ADMIN: 'admin', ORGANIZADOR: 'org', VOTANTE: 'votante', AUDITOR: 'auditor' })[usuario.rol];
  }

  document.getElementById('login-form').addEventListener('submit', e => {
    e.preventDefault();
    const doc = document.getElementById('login-doc').value.trim();
    const pass = document.getElementById('login-pass').value;

    if (State.bloqueadoHasta && Date.now() < State.bloqueadoHasta) {
      const min = Math.ceil((State.bloqueadoHasta - Date.now()) / 60000);
      mostrarAlerta('Cuenta bloqueada temporalmente', `Demasiados intentos fallidos. Intenta de nuevo en ${min} minuto(s).`);
      return;
    }

    const cuenta = CUENTAS_DEMO.find(c => c.doc === doc || c.doc === doc) ;
    const user = DB.usuarios.find(u => u.documento === doc || u.correo === doc);

    if (user && cuenta && cuenta.doc === user.documento && cuenta.pass === pass) {
      toast(`Bienvenido, ${user.nombres}`, 'success');
      entrar({ nombre: `${user.nombres} ${user.apellidos}`, rol: user.rol, documento: user.documento, correo: user.correo });
    } else {
      State.intentosFallidos++;
      if (State.intentosFallidos >= 5) {
        State.bloqueadoHasta = Date.now() + 15 * 60 * 1000;
        State.intentosFallidos = 0;
        mostrarAlerta('⚠️ Bloqueo de seguridad', 'Ha superado 5 intentos fallidos. La cuenta permanecerá bloqueada por <b>15 minutos</b>.');
        toast('Cuenta bloqueada temporalmente (15 min)', 'destructive');
      } else {
        const restan = 5 - State.intentosFallidos;
        mostrarAlerta('Credenciales incorrectas', `Documento o contraseña inválidos. Intentos restantes antes del bloqueo: <b>${restan}</b>.`);
      }
    }
  });

  document.querySelectorAll('.demo-user').forEach(b => b.addEventListener('click', () => {
    const rol = b.dataset.rol;
    const c = CUENTAS_DEMO.find(x => x.rol === rol);
    const u = DB.usuarios.find(x => x.documento === c.doc);
    entrar({ nombre: `${u.nombres} ${u.apellidos}`, rol: u.rol, documento: u.documento, correo: u.correo });
  }));
}
