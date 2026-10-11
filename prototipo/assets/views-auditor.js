/* views-auditor.js — Módulo 4: Supervisión y auditoría */

/* ---------- CU-08: Dashboard de resultados ---------- */
RegistrarVista('auditor', {
  titulo: 'Panel de resultados',
  sub: 'CU-08 · Visualizar resultados en tiempo real',
  render() {
    const c = catActiva();
    const total = c.resultados.reduce((a, b) => a + b, 0);
    const pct = Math.round((c.participantes / c.padron) * 100);
    return {
      html: `
      <div class="flex items-center justify-between mb-20" style="flex-wrap:wrap;gap:12px">
        <div>
          <div class="section-title">${esc(c.titulo)}</div>
          <div class="section-sub" style="margin-bottom:0">Solo lectura · actualización automática vía WebSocket</div>
        </div>
        <div class="flex items-center gap-10">
          ${switchToggle('rt-toggle')}
          <span class="text-sm fw-600">Tiempo real</span>
          <span class="badge ${State.enVivo ? 'badge-success' : 'badge-muted'}" id="rt-estado">${State.enVivo ? 'CONECTADO' : 'PAUSADO'}</span>
        </div>
      </div>

      <div class="kpi-grid">
        ${kpi({ label: 'Padrón habilitado', valor: fmtNum(c.padron), icono: Icons.users(16), tendencia: '<span class="text-muted">registrados en el sistema</span>' })}
        ${kpi({ label: 'Participantes', valor: fmtNum(c.participantes), icono: Icons.vote(16), tendencia: `<span style="color:hsl(var(--success))">${Icons.activity(13)} en curso</span>`, tendCls: 'up' })}
        ${kpi({ label: 'Votos en urna', valor: fmtNum(total), icono: Icons.checkSquare(16), tendencia: `<span class="text-muted">${c.candidatos.length} casillas</span>` })}
        ${kpi({ label: 'Abstenciones', valor: fmtNum(c.padron - c.participantes), icono: Icons.clock(16), tendencia: `<span class="text-muted">sin participación</span>` })}
      </div>

      <div class="grid-2" style="grid-template-columns: 1.5fr 1fr">
        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.chart(16)} Conteo por casilla</div>
          <div class="card-desc">Votos registrados en la urna digital (anónimos)</div></div>
          <div class="card-body" id="au-barras">${barras(c.candidatos.map((cand, i) => ({ nombre: cand.nombre, valor: c.resultados[i], cls: cand.esBlanco ? 'blanco' : '' })))}</div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.activity(16)} Participación</div>
          <div class="card-desc">Padrón vs. asistencia electoral</div></div>
          <div class="card-body" style="display:grid;place-items:center;padding:26px">
            ${donut(c.participantes, c.padron, 'participación')}
          </div>
          <div class="card-footer" style="justify-content:center">
            <span class="text-sm text-muted">Actualizado: <span id="au-hora">${new Date().toLocaleTimeString('es-CO')}</span></span>
          </div>
        </div>
      </div>`,
      mount(root) {
        root.querySelector('#rt-toggle').checked = State.enVivo;
        root.querySelector('#rt-toggle').addEventListener('change', e => {
          State.enVivo = e.target.checked;
          root.querySelector('#rt-estado').textContent = State.enVivo ? 'CONECTADO' : 'PAUSADO';
          root.querySelector('#rt-estado').className = `badge ${State.enVivo ? 'badge-success' : 'badge-muted'}`;
          if (!State.enVivo && State.intervaloRT) { clearInterval(State.intervaloRT); State.intervaloRT = null; }
          else arrancarRT(root);
        });
        function arrancarRT(rt) {
          if (State.intervaloRT) clearInterval(State.intervaloRT);
          State.intervaloRT = setInterval(() => {
            const i = Math.floor(Math.random() * c.candidatos.length);
            c.resultados[i] += Math.floor(Math.random() * 4) + 1;
            rt.querySelector('#au-barras').innerHTML = barras(c.candidatos.map((cand, j) => ({ nombre: cand.nombre, valor: c.resultados[j], cls: cand.esBlanco ? 'blanco' : '' })));
            const h = rt.querySelector('#au-hora'); if (h) h.textContent = new Date().toLocaleTimeString('es-CO');
          }, 2000);
        }
        if (State.enVivo) arrancarRT(root);
      },
    };
  },
});

/* ---------- CU-09: Auditoría ---------- */
RegistrarVista('auditor/logs', {
  titulo: 'Auditoría del proceso',
  sub: 'CU-09 · Auditar proceso de votación (solo lectura)',
  render() {
    const k = DB.consistencia;
    return {
      html: `
      <div class="card mb-20">
        <div class="card-header"><div class="card-title">${Icons.checkSquare(16)} Ecuación de consistencia matemática</div>
        <div class="card-desc">Verificación automática: el padrón debe cuadrar con la urna</div></div>
        <div class="card-body">
          <div class="equacion">
            <span class="eq-num">${fmtNum(k.padron)}</span><span class="eq-sign">padrón</span>
            <span class="eq-sign">=</span>
            <span class="eq-num">${fmtNum(k.votosUrna)}</span><span class="eq-sign">votos urna</span>
            <span class="eq-sign">+</span>
            <span class="eq-num">${fmtNum(k.padron - k.votosUrna)}</span><span class="eq-sign">abstenciones</span>
            <span class="eq-ok">${Icons.check(20)}</span>
          </div>
          <div class="grid-3 mt-20">
            ${kpi({ label: 'Votos en urna', valor: fmtNum(k.votosUrna), icono: Icons.checkSquare(16), tendencia: '<span style="color:hsl(var(--success))">coincide con participantes</span>', tendCls: 'up' })}
            ${kpi({ label: 'Doble voto detectado', valor: '0', icono: Icons.shield(16), tendencia: '<span class="text-muted">restricción UNIQUE usuario-categoría</span>' })}
            ${kpi({ label: 'Alertas de integridad', valor: '0', icono: Icons.alert(16), tendencia: '<span style="color:hsl(var(--success))">sin anomalías</span>', tendCls: 'up' })}
          </div>
          <div class="alert alert-info" style="margin-top:16px;margin-bottom:0">
            <span style="flex-shrink:0;margin-top:1px">${Icons.info(17)}</span>
            <div><div class="alert-title">Anonimato preservado</div>
            <div class="alert-body">La urna digital no almacena identidad de votantes. La auditoría valida totales y trazabilidad, nunca preferencias individuales.</div></div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header flex items-center" style="padding-bottom:16px">
          <div style="flex:1"><div class="card-title">${Icons.scroll(16)} Bitácora de eventos</div>
          <div class="card-desc">Registro inalterable con hash de trazabilidad · solo lectura</div></div>
          <button class="btn btn-outline" id="log-exportar">${Icons.download(15)} Exportar CSV</button>
        </div>
        <div style="padding:0 22px 22px">
          <div class="table-wrap stack">
            <table class="table">
              <thead><tr><th>#</th><th>Timestamp</th><th>Usuario</th><th>Módulo</th><th>Acción</th><th>IP</th><th>Hash</th></tr></thead>
              <tbody>
                ${DB.logs.map(l => `
                  <tr>
                    <td data-th="#" class="text-muted">${l.id}</td>
                    <td data-th="Timestamp" class="font-mono" style="font-size:11.5px">${esc(l.ts)}</td>
                    <td data-th="Usuario">${esc(l.usuario)}</td>
                    <td data-th="Módulo">${esc(l.modulo)}</td>
                    <td data-th="Acción" class="fw-600">${esc(l.accion)}</td>
                    <td data-th="IP" class="font-mono" style="font-size:11.5px">${esc(l.ip)}</td>
                    <td data-th="Hash" class="font-mono" style="font-size:11.5px;color:hsl(var(--muted-foreground))">${esc(l.hash)}</td>
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>
          <div class="flex items-center gap-10 text-sm text-muted" style="margin-top:12px">
            ${Icons.lock(14)} Los registros son append-only: no se pueden editar ni eliminar.
          </div>
        </div>
      </div>`,
      mount(root) {
        root.querySelector('#log-exportar').addEventListener('click', () => toast('Exportando bitácora a CSV…', 'info'));
      },
    };
  },
});
