/* views-admin.js — Módulo 1: Usuarios, autenticación y seguridad */

/* ---------- Dashboard ADMIN ---------- */
RegistrarVista('admin', {
  titulo: 'Dashboard',
  sub: 'Resumen general del sistema',
  render() {
    const votantes = DB.usuarios.filter(u => u.rol === 'VOTANTE');
    const activos = votantes.filter(u => u.estado === 'ACTIVO').length;
    const suspendidos = votantes.filter(u => u.estado === 'SUSPENDIDO').length;
    const html = `
      <div class="kpi-grid">
        ${kpi({ label: 'Usuarios del sistema', valor: fmtNum(DB.usuarios.length), icono: Icons.users(16), tendencia: `<span class="text-muted">${votantes.length} votantes · ${DB.usuarios.length - votantes.length} staff</span>`, tendCls: 'neutral' })}
        ${kpi({ label: 'Elecciones activas', valor: '1', icono: Icons.calendar(16), tendencia: `<span class="text-muted">2 programadas/finalizadas</span>`, tendCls: 'neutral' })}
        ${kpi({ label: 'Participación global', valor: '41%', icono: Icons.vote(16), tendencia: `<span class="text-muted">${fmtNum(DB.categorias[0].participantes)} de ${fmtNum(DB.categorias[0].padron)} habilitados</span>`, tendCls: 'neutral' })}
        ${kpi({ label: 'Cuentas bloqueadas', valor: String(suspendidos), icono: Icons.lock(16), tendencia: `<span class="text-muted">${activos} cuentas activas</span>`, tendCls: 'neutral' })}
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.scroll(16)} Actividad reciente</div>
          <div class="card-desc">Últimos eventos registrados en la bitácora de auditoría</div></div>
          <div class="card-body" style="padding-top:14px">
            ${DB.logs.slice(0, 5).map(l => `
              <div class="fila">
                <div style="width:8px;height:8px;border-radius:50%;background:hsl(var(--primary));flex-shrink:0"></div>
                <div style="flex:1;min-width:0">
                  <div style="font-size:13px;font-weight:600">${esc(l.accion)}</div>
                  <div class="text-sm text-muted">${esc(l.usuario)} · ${esc(l.modulo)} · IP ${esc(l.ip)}</div>
                </div>
                <div class="text-sm text-muted" style="white-space:nowrap">${esc(l.ts.slice(11))}</div>
              </div>`).join('')}
          </div>
          <div class="card-footer"><a class="btn btn-outline btn-sm" href="#/auditor/logs">Ver bitácora completa</a></div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.key(16)} Estado de seguridad</div>
          <div class="card-desc">Indicadores del módulo de autenticación</div></div>
          <div class="card-body">
            <div class="fila">
              <div><div class="fw-600" style="font-size:13.5px">Sesiones JWT activas</div><div class="text-sm text-muted">Access token 60 min · Refresh rotativo</div></div>
              <span class="badge badge-success">7 activas</span>
            </div>
            <div class="fila">
              <div><div class="fw-600" style="font-size:13.5px">Intentos fallidos (24 h)</div><div class="text-sm text-muted">Bloqueo automático a los 5 intentos</div></div>
              <span class="badge badge-warning">3 eventos</span>
            </div>
            <div class="fila">
              <div><div class="fw-600" style="font-size:13.5px">Consistencia de la urna</div><div class="text-sm text-muted">Padrón = votos + abstenciones</div></div>
              <span class="badge badge-success">${Icons.check(12)} OK</span>
            </div>
          </div>
          <div class="card-footer">
            <a class="btn btn-outline btn-sm" href="#/admin/permisos">Matriz de permisos</a>
            <a class="btn btn-primary btn-sm" href="#/admin/carga">Cargar votantes</a>
          </div>
        </div>
      </div>`;
    return { html };
  },
});

/* ---------- CU-02: Administrar cuentas ---------- */
let usuariosFiltro = { q: '', estado: 'TODOS' };

RegistrarVista('admin/usuarios', {
  titulo: 'Gestión de usuarios',
  sub: 'CU-02 · Administrar cuentas de usuario',
  render() {
    return {
      html: `
      <div class="card">
        <div class="card-header flex items-center gap-14" style="padding-bottom:18px">
          <div style="flex:1">
            <div class="card-title">${Icons.users(16)} Cuentas registradas</div>
            <div class="card-desc">CRUD de usuarios del sistema y del padrón electoral</div>
          </div>
          <div class="search-box" style="width:210px">${Icons.search(15)}<input id="u-buscar" placeholder="Documento, nombre o correo…" value="${esc(usuariosFiltro.q)}"></div>
          <select class="select" style="width:auto" id="u-estado">
            ${['TODOS', 'ACTIVO', 'SUSPENDIDO', 'INACTIVO'].map(e => `<option ${usuariosFiltro.estado === e ? 'selected' : ''}>${e}</option>`).join('')}
          </select>
          <button class="btn btn-primary" id="u-nuevo">${Icons.plus(16)} Nuevo usuario</button>
        </div>
        <div style="padding:0 22px 22px">
          <div class="table-wrap stack" id="u-tabla"></div>
          <div class="text-sm text-muted" style="margin-top:12px" id="u-conteo"></div>
        </div>
      </div>`,
      mount(root) {
        function pintarTabla() {
          const q = usuariosFiltro.q.toLowerCase();
          const rows = DB.usuarios.filter(u =>
            (usuariosFiltro.estado === 'TODOS' || u.estado === usuariosFiltro.estado) &&
            (!q || (u.documento + u.nombres + u.apellidos + u.correo).toLowerCase().includes(q))
          );
          root.querySelector('#u-tabla').innerHTML = `
            <table class="table">
              <thead><tr>
                <th>Documento</th><th>Usuario</th><th>Rol</th><th>Estado</th><th>Intentos</th><th></th>
              </tr></thead>
              <tbody>
                ${rows.map(u => `
                  <tr>
                    <td data-th="Documento" class="font-mono">${esc(u.documento)}</td>
                    <td data-th="Usuario">
                      <div class="flex items-center gap-10">
                        ${avatar(u.nombres + ' ' + u.apellidos, 32)}
                        <div><div class="fw-600">${esc(u.nombres)} ${esc(u.apellidos)}</div>
                        <div class="text-sm text-muted">${esc(u.correo)}</div></div>
                      </div>
                    </td>
                    <td data-th="Rol"><span class="badge badge-secondary">${esc(u.rol)}</span></td>
                    <td data-th="Estado">${badgeUsuario(u.estado)}</td>
                    <td data-th="Intentos" class="text-muted">${u.intentos}/5</td>
                    <td data-th="Acciones">
                      <div class="actions">
                        <button class="btn btn-ghost btn-sm btn-icon" data-edit="${u.id}" title="Editar">${Icons.edit(15)}</button>
                        <button class="btn btn-ghost btn-sm btn-icon" data-susp="${u.id}" title="${u.estado === 'SUSPENDIDO' ? 'Reactivar' : 'Suspender'}">${Icons.lock(15)}</button>
                        <button class="btn btn-ghost btn-sm btn-icon" style="color:hsl(var(--destructive))" data-del="${u.id}" title="Eliminar">${Icons.trash(15)}</button>
                      </div>
                    </td>
                  </tr>`).join('') || `<tr><td colspan="6" class="text-muted" style="text-align:center;padding:28px">Sin resultados</td></tr>`}
              </tbody>
            </table>`;
          root.querySelector('#u-conteo').textContent = `${rows.length} de ${DB.usuarios.length} usuarios`;

          root.querySelectorAll('[data-edit]').forEach(b => b.addEventListener('click', () => modalUsuario(+b.dataset.edit, pintarTabla)));
          root.querySelectorAll('[data-susp]').forEach(b => b.addEventListener('click', () => {
            const u = DB.usuarios.find(x => x.id === +b.dataset.susp);
            const ahora = u.estado !== 'SUSPENDIDO';
            confirmar({
              titulo: ahora ? `¿Suspender a ${u.nombres}?` : `¿Reactivar a ${u.nombres}?`,
              desc: ahora ? 'El usuario perderá el acceso temporalmente. Si ya emitió voto, sus datos se conservan (borrado lógico).' : 'El usuario podrá volver a iniciar sesión inmediatamente.',
              textoBtn: ahora ? 'Sí, suspender' : 'Sí, reactivar',
              onOk() { u.estado = ahora ? 'SUSPENDIDO' : 'ACTIVO'; toast(`Usuario ${ahora ? 'suspendido' : 'reactivado'}`); pintarTabla(); },
            });
          }));
          root.querySelectorAll('[data-del]').forEach(b => b.addEventListener('click', () => {
            const u = DB.usuarios.find(x => x.id === +b.dataset.del);
            confirmar({
              titulo: `¿Eliminar a ${u.nombres} ${u.apellidos}?`,
              desc: 'Se aplicará borrado lógico: la cuenta queda INACTIVA y se conserva el historial. <b>Nunca</b> se elimina físicamente un usuario que ya votó.',
              textoBtn: 'Desactivar cuenta',
              onOk() { u.estado = 'INACTIVO'; toast('Cuenta desactivada (borrado lógico)'); pintarTabla(); },
            });
          }));
        }
        pintarTabla();
        root.querySelector('#u-buscar').addEventListener('input', e => { usuariosFiltro.q = e.target.value; pintarTabla(); });
        root.querySelector('#u-estado').addEventListener('change', e => { usuariosFiltro.estado = e.target.value; pintarTabla(); });
        root.querySelector('#u-nuevo').addEventListener('click', () => modalUsuario(null, pintarTabla));
      },
    };
  },
});

function modalUsuario(id, despues) {
  const u = id ? DB.usuarios.find(x => x.id === id) : { nombres: '', apellidos: '', documento: '', correo: '', rol: 'VOTANTE', estado: 'ACTIVO' };
  modal({
    icon: 'primary', iconSvg: Icons.userPlus(20),
    titulo: id ? 'Editar usuario' : 'Registrar usuario',
    desc: id ? `Modifica los datos de ${u.nombres}. Los cambios quedan en la bitácora.` : 'Crea una cuenta individual en el padrón electoral.',
    body: `
      <div class="field-row">
        <div class="field"><label>Nombres</label><input class="input" id="m-nom" value="${esc(u.nombres)}"></div>
        <div class="field"><label>Apellidos</label><input class="input" id="m-ape" value="${esc(u.apellidos)}"></div>
      </div>
      <div class="field"><label>Documento</label><input class="input" id="m-doc" value="${esc(u.documento)}" placeholder="1015487962"></div>
      <div class="field"><label>Correo institucional</label><input class="input" id="m-correo" type="email" value="${esc(u.correo)}" placeholder="usuario@uni.edu.co"></div>
      <div class="field-row">
        <div class="field"><label>Rol</label><select class="select" id="m-rol">${DB.roles.map(r => `<option ${u.rol === r ? 'selected' : ''}>${r}</option>`).join('')}</select></div>
        <div class="field"><label>Estado</label><select class="select" id="m-estado">${['ACTIVO', 'SUSPENDIDO', 'INACTIVO'].map(e => `<option ${u.estado === e ? 'selected' : ''}>${e}</option>`).join('')}</select></div>
      </div>
      <div class="field"><label>Contraseña ${id ? '' : '<span class="text-muted">(mín. 8 caracteres)</span>'}</label>
      <input class="input" type="password" id="m-pass" placeholder="${id ? 'Dejar en blanco para no cambiar' : '••••••••'}"></div>`,
    footer: `<button class="btn btn-secondary" data-close>Cancelar</button>
             <button class="btn btn-primary" id="m-guardar">${Icons.check(16)} Guardar</button>`,
  });
  document.getElementById('m-guardar').addEventListener('click', () => {
    const nom = document.getElementById('m-nom').value.trim();
    const ape = document.getElementById('m-ape').value.trim();
    const doc = document.getElementById('m-doc').value.trim();
    const correo = document.getElementById('m-correo').value.trim();
    if (!nom || !ape || !doc || !correo) { toast('Completa los campos obligatorios', 'destructive'); return; }
    if (id) {
      Object.assign(u, { nombres: nom, apellidos: ape, documento: doc, correo, rol: document.getElementById('m-rol').value, estado: document.getElementById('m-estado').value });
      toast('Usuario actualizado correctamente');
    } else {
      DB.usuarios.push({ id: Date.now(), nombres: nom, apellidos: ape, documento: doc, correo, rol: document.getElementById('m-rol').value, estado: document.getElementById('m-estado').value, intentos: 0 });
      toast('Usuario registrado en el padrón');
    }
    cerrarModal();
    despues && despues();
  });
}

/* ---------- CU-01: Registro individual + carga masiva ---------- */
RegistrarVista('admin/carga', {
  titulo: 'Registro y carga masiva',
  sub: 'CU-01 · Registrar votantes / usuarios',
  render() {
    return {
      html: `
      <div class="grid-2" style="grid-template-columns: 1fr 1.4fr">
        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.userPlus(16)} Registro individual</div>
          <div class="card-desc">Alta manual de un votante en el padrón</div></div>
          <div class="card-body">
            <div class="field-row">
              <div class="field"><label>Nombres *</label><input class="input" id="r-nom" placeholder="Ana"></div>
              <div class="field"><label>Apellidos *</label><input class="input" id="r-ape" placeholder="Torres"></div>
            </div>
            <div class="field"><label>Documento *</label><input class="input" id="r-doc" placeholder="1055987412"></div>
            <div class="field"><label>Correo *</label><input class="input" id="r-correo" placeholder="ana.torres@uni.edu.co"></div>
            <div class="field"><label>Facultad</label>
              <select class="select" id="r-fac"><option>Ingeniería</option><option>Ciencias de la Salud</option><option>Humanidades</option><option>Ciencias Económicas</option></select></div>
            <button class="btn btn-primary btn-block" id="r-guardar">${Icons.check(16)} Registrar votante</button>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.upload(16)} Carga masiva (CSV / Excel)</div>
          <div class="card-desc">Importa hasta 5.000 votantes por archivo · Formatos .csv, .xlsx · máx. 10 MB</div></div>
          <div class="card-body">
            <div class="dropzone" id="dz">
              <div class="dz-icon">${Icons.upload(22)}</div>
              <div class="dz-title">Arrastra tu archivo aquí</div>
              <div class="dz-hint">o haz clic para seleccionar · peso máximo 10 MB</div>
              <input type="file" id="dz-input" accept=".csv,.xlsx,.xls" hidden>
            </div>
            <div id="dz-lista"></div>
            <div id="dz-resumen"></div>
            <div class="alert alert-info" style="margin-top:18px">
              <span style="flex-shrink:0;margin-top:1px">${Icons.info(17)}</span>
              <div><div class="alert-title">Columnas esperadas</div>
              <div class="alert-body font-mono" style="font-size:11.5px">documento, nombres, apellidos, correo, facultad, jornada</div></div>
            </div>
          </div>
        </div>
      </div>`,
      mount(root) {
        root.querySelector('#r-guardar').addEventListener('click', () => {
          const nom = root.querySelector('#r-nom').value.trim();
          const ape = root.querySelector('#r-ape').value.trim();
          const doc = root.querySelector('#r-doc').value.trim();
          const correo = root.querySelector('#r-correo').value.trim();
          if (!nom || !ape || !doc || !correo) { toast('Completa los campos obligatorios', 'destructive'); return; }
          DB.usuarios.push({ id: Date.now(), nombres: nom, apellidos: ape, documento: doc, correo, rol: 'VOTANTE', estado: 'ACTIVO', intentos: 0 });
          toast('Votante registrado individualmente');
          root.querySelector('#r-nom').value = root.querySelector('#r-ape').value = root.querySelector('#r-doc').value = root.querySelector('#r-correo').value = '';
        });

        const dz = root.querySelector('#dz');
        const input = root.querySelector('#dz-input');
        dz.addEventListener('click', () => input.click());
        ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add('dragover'); }));
        ['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove('dragover'); }));
        dz.addEventListener('drop', e => { if (e.dataTransfer.files.length) procesarArchivo(e.dataTransfer.files[0], root); });
        input.addEventListener('change', e => { if (e.target.files.length) procesarArchivo(e.target.files[0], root); });
      },
    };
  },
});

function procesarArchivo(file, root) {
  const lista = root.querySelector('#dz-lista');
  const resumen = root.querySelector('#dz-resumen');
  const ext = file.name.split('.').pop().toLowerCase();
  const pesoMB = file.size / (1024 * 1024);

  if (!['csv', 'xlsx', 'xls'].includes(ext)) {
    toast('Formato no permitido. Usa CSV o Excel.', 'destructive');
    lista.innerHTML = `<div class="alert alert-destructive" style="margin-top:12px">${Icons.alert(15)} Formato <b>.${esc(ext)}</b> rechazado</div>`;
    return;
  }
  if (pesoMB > 10) {
    toast('El archivo supera los 10 MB', 'destructive');
    lista.innerHTML = `<div class="alert alert-destructive" style="margin-top:12px">${Icons.alert(15)} El archivo pesa ${pesoMB.toFixed(1)} MB (máx. 10 MB)</div>`;
    return;
  }

  lista.innerHTML = `
    <div class="file-item">
      <div class="fi-icon">${Icons.fileText(17)}</div>
      <div style="flex:1;min-width:0">
        <div class="fi-name">${esc(file.name)}</div>
        <div class="fi-meta">${(file.size / 1024).toFixed(0)} KB · válido</div>
      </div>
      <span class="badge badge-success">${Icons.check(12)} Aceptado</span>
    </div>
    <div style="margin-top:10px" class="progress"><div class="progress-bar" style="width:0%"></div></div>`;
  resumen.innerHTML = '';

  const barra = lista.querySelector('.progress-bar');
  let p = 0;
  const t = setInterval(() => {
    p += Math.random() * 18 + 6;
    if (p >= 100) {
      clearInterval(t);
      barra.style.width = '100%';
      const validos = 284 + Math.floor(Math.random() * 40);
      const errores = Math.floor(Math.random() * 6);
      resumen.innerHTML = `
        <div class="alert alert-success" style="margin-top:14px">
          <span style="flex-shrink:0;margin-top:1px">${Icons.check(17)}</span>
          <div><div class="alert-title">Importación completada</div>
          <div class="alert-body">${validos} registros importados al padrón${errores ? ` · ${errores} filas con error (correo duplicado o documento inválido)` : ''}.</div></div>
        </div>
        ${errores ? `<button class="btn btn-outline btn-sm">${Icons.download(14)} Descargar reporte de errores</button>` : ''}`;
      toast(`Carga masiva: ${validos} votantes importados`);
    } else barra.style.width = p + '%';
  }, 180);
}

/* ---------- CU-03: Matriz de permisos ---------- */
RegistrarVista('admin/permisos', {
  titulo: 'Matriz de permisos',
  sub: 'CU-03 · Gestionar permisos y accesos (RBAC)',
  render() {
    const nivelSel = v => v === undefined ? '—' : (v[0] ? (v[2] ? 'Administrar' : v[1] ? 'Lectura/Escritura' : 'Lectura') : '—');
    return {
      html: `
      <div class="card">
        <div class="card-header flex items-center" style="padding-bottom:18px">
          <div style="flex:1">
            <div class="card-title">${Icons.key(16)} Roles × Módulos</div>
            <div class="card-desc">Define qué puede hacer cada rol. Los cambios se aplican al guardar.</div>
          </div>
          <button class="btn btn-primary" id="p-guardar">${Icons.check(16)} Guardar cambios</button>
        </div>
        <div class="card-body" style="padding:0 22px 22px">
          <div class="table-wrap">
            <table class="table matriz">
              <thead><tr><th>Rol</th>${DB.modulos.map(m => `<th>${esc(m.label)}</th>`).join('')}</tr></thead>
              <tbody>
                ${DB.roles.map(r => `
                  <tr data-rol="${r}">
                    <td><span class="badge badge-secondary">${esc(r)}</span></td>
                    ${DB.modulos.map(m => {
                      const v = DB.permisos[r][m.key];
                      return `<td><select class="select" style="width:118px;padding:5px 26px 5px 8px;font-size:12px" data-rol="${r}" data-mod="${m.key}">
                        ${['—', 'Lectura', 'Lectura/Escritura', 'Administrar'].map(o => `<option ${nivelSel(v) === o ? 'selected' : ''}>${o}</option>`).join('')}
                      </select></td>`;
                    }).join('')}
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>
          <div class="alert alert-warning" style="margin-top:16px">
            <span style="flex-shrink:0;margin-top:1px">${Icons.alert(17)}</span>
            <div><div class="alert-title">Restricción del sistema</div>
            <div class="alert-body">El rol <b>VOTANTE</b> nunca puede obtener permisos de escritura sobre usuarios ni auditoría, y el rol <b>AUDITOR</b> es siempre de solo lectura.</div></div>
          </div>
        </div>
      </div>`,
      mount(root) {
        root.querySelectorAll('select[data-mod]').forEach(s => s.addEventListener('change', () => {
          s.closest('tr').style.background = 'hsl(var(--warning) / .07)';
          root.querySelector('#p-guardar').classList.add('btn-warning');
        }));
        root.querySelector('#p-guardar').addEventListener('click', () => {
          root.querySelectorAll('select[data-mod]').forEach(s => {
            const val = s.value;
            DB.permisos[s.dataset.rol][s.dataset.mod] = val === '—' ? [false, false, false] : val === 'Lectura' ? [true, false, false] : val === 'Lectura/Escritura' ? [true, true, false] : [true, true, true];
            s.closest('tr').style.background = '';
          });
          root.querySelector('#p-guardar').classList.remove('btn-warning');
          toast('Matriz de permisos actualizada');
        });
      },
    };
  },
});
