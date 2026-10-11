/* views-votante.js — Módulo 3: Proceso electoral del votante */

function qrMock(seed, size = 150) {
  let h = 0; for (const c of seed) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const rnd = () => { h = (h * 1103515245 + 12345) >>> 0; return h / 4294967296; };
  const n = 21, cell = size / n;
  let rects = '';
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const esquina = (x < 7 && y < 7) || (x > n - 8 && y < 7) || (x < 7 && y > n - 8);
    if (esquina) continue;
    if (rnd() > .52) rects += `<rect x="${x * cell}" y="${y * cell}" width="${cell}" height="${cell}"/>`;
  }
  const finder = (fx, fy) => `<rect x="${fx * cell}" y="${fy * cell}" width="${7 * cell}" height="${7 * cell}" fill="none" stroke="currentColor" stroke-width="${cell}"/>`;
  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" fill="currentColor">
    <rect width="${size}" height="${size}" fill="#fff"/>${rects}${finder(0, 0)}${finder(n - 7, 0)}${finder(0, n - 7)}</svg>`;
}

/* ---------- Inicio VOTANTE ---------- */
RegistrarVista('votante', {
  titulo: 'Inicio',
  sub: 'Procesos electorales disponibles para ti',
  render() {
    return {
      html: `
      <div class="alert alert-info">
        <span style="flex-shrink:0;margin-top:1px">${Icons.shield(17)}</span>
        <div><div class="alert-title">Tu voto es secreto</div>
        <div class="alert-body">El sistema guarda tu voto sin asociarlo a tu identidad. Solo recibirás un comprobante con Hash SHA-256 que certifica <b>que votaste</b>, nunca <b>por quién</b>.</div></div>
      </div>

      <div class="section-title">Elecciones disponibles</div>
      <div class="section-sub">Selecciona una elección activa para emitir tu voto</div>
      <div class="grid-auto">
        ${DB.categorias.map(c => {
          const habilitada = c.estado === 'ACTIVA' || c.estado === 'CERRANDO';
          const yaVoto = c.id === 1 && State.votoEmitido;
          return `
          <div class="card">
            <div class="card-body">
              <div class="flex items-center justify-between mb-16">
                ${badgeEstado(c.estado)}
                <span class="text-sm text-muted">${fmtFecha(c.apertura)} → ${fmtFecha(c.cierre)}</span>
              </div>
              <div class="fw-600" style="font-size:16px;letter-spacing:-0.01em">${esc(c.titulo)}</div>
              <div class="text-sm text-muted" style="margin:6px 0 16px;line-height:1.55">${esc(c.descripcion)}</div>
              ${c.estado === 'ACTIVA' && !yaVoto && State.estadoEleccion !== 'CERRANDO'
                ? `<a class="btn btn-primary btn-block" href="#/votante/tarjeton">${Icons.vote(16)} Votar ahora</a>`
                : yaVoto
                  ? `<a class="btn btn-success btn-block" href="#/votante/comprobante">${Icons.check(16)} Voto registrado</a>`
                  : c.estado === 'CERRANDO'
                    ? `<button class="btn btn-secondary btn-block" disabled>${Icons.lock(15)} Cerrando…</button>`
                    : c.estado === 'FINALIZADA'
                      ? `<a class="btn btn-outline btn-block" href="#/votante/resultados">${Icons.chart(15)} Ver resultados</a>`
                      : `<button class="btn btn-secondary btn-block" disabled>${Icons.clock(15)} ${c.estado === 'PROGRAMADA' ? 'Aún no inicia' : 'No disponible'}</button>`}
            </div>
          </div>`;
        }).join('')}
      </div>

      <div class="card mt-28">
        <div class="card-header"><div class="card-title">${Icons.scroll(16)} Normativas vigentes</div>
        <div class="card-desc">Documentos que rigen el proceso electoral</div></div>
        <div class="card-body" style="padding-top:14px">
          ${DB.normativas.map(n => `
            <div class="flex items-center gap-14" style="padding:11px 0;border-bottom:1px solid hsl(var(--border))">
              <div class="fi-icon" style="background:hsl(var(--destructive) / .12);color:hsl(var(--destructive));width:36px;height:36px;border-radius:9px;display:grid;place-items:center;font-size:10px;font-weight:800">PDF</div>
              <div style="flex:1;min-width:0">
                <div class="fw-600" style="font-size:13.5px">${esc(n.titulo)}</div>
                <div class="text-sm text-muted">Publicado el ${fmtFecha(n.fecha)}</div>
              </div>
              <button class="btn btn-outline btn-sm">${Icons.download(14)} Descargar</button>
            </div>`).join('')}
        </div>
      </div>`,
    };
  },
});

/* ---------- CU-07: Emitir voto ---------- */
RegistrarVista('votante/tarjeton', {
  titulo: 'Tarjetón electoral',
  sub: 'CU-07 · Emitir voto · Elecciones Estudiantiles 2026',
  render() {
    const c = catActiva();
    if (State.votoEmitido) { location.hash = '#/votante/comprobante'; return { html: '' }; }
    return {
      html: `
      <div class="flex items-center justify-between mb-20" style="flex-wrap:wrap;gap:12px">
        <div>
          <div class="section-title">${esc(c.titulo)}</div>
          <div class="section-sub" style="margin-bottom:0">Selecciona una casilla. Podrás revisar tu elección antes de confirmar.</div>
        </div>
        ${badgeEstado(State.estadoEleccion)}
      </div>

      <div class="tarjeton-grid" id="tarjeton">
        ${c.candidatos.map((cand, i) => `
          <div class="tarjeton-option ${cand.esBlanco ? 'blanco' : ''}" data-id="${cand.id}">
            <div class="check">${Icons.check(14)}</div>
            <div class="foto" style="${cand.esBlanco ? '' : `background:linear-gradient(135deg,hsl(${243 + i * 8} 70% 60%),hsl(${271 + i * 6} 70% 55%))`}">
              ${cand.esBlanco ? Icons.checkSquare(30) : cand.nombre.split(' ').map(p => p[0]).slice(0, 2).join('')}
            </div>
            <div class="cand-nombre">${esc(cand.nombre)}</div>
            <div class="cand-lista">${esc(cand.lista)}</div>
          </div>`).join('')}
      </div>

      <div class="sticky-vote-bar">
        <div style="flex:1;min-width:0">
          <div class="text-sm text-muted">Tu selección</div>
          <div class="fw-600" id="sel-label" style="font-size:14.5px">Ninguna — selecciona una casilla</div>
        </div>
        <button class="btn btn-primary btn-lg" id="btn-emitir" disabled>${Icons.vote(17)} Emitir voto</button>
      </div>`,
      mount(root) {
        const c2 = catActiva();
        root.querySelectorAll('.tarjeton-option').forEach(opt => {
          opt.addEventListener('click', () => {
            root.querySelectorAll('.tarjeton-option').forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            const cand = c2.candidatos.find(x => x.id === +opt.dataset.id);
            State.seleccionVoto = cand;
            const btn = root.querySelector('#btn-emitir');
            btn.disabled = false;
            root.querySelector('#sel-label').textContent = `${cand.nombre} · ${cand.lista}`;
          });
        });

        root.querySelector('#btn-emitir').addEventListener('click', () => {
          if (!State.seleccionVoto) return;
          const cand = State.seleccionVoto;
          modal({
            icon: 'warning', iconSvg: Icons.alert(22),
            titulo: '¿Confirma su voto?',
            desc: `Está a punto de votar por <b>${esc(cand.nombre)}</b> (${esc(cand.lista)}).<br><br><b>Esta acción no se puede deshacer.</b> Su voto es anónimo y no podrá modificarse ni consultarse por quién votó.`,
            body: `<div class="flex items-center gap-10" style="padding:12px 14px;background:hsl(var(--muted) / .5);border:1px solid hsl(var(--border));border-radius:10px">
              <div class="check" style="all:unset;width:22px;height:22px;border-radius:50%;background:hsl(var(--primary));color:#fff;display:grid;place-items:center">${Icons.check(13)}</div>
              <div><div class="fw-600" style="font-size:13.5px">${esc(cand.nombre)}</div>
              <div class="text-sm text-muted">${esc(cand.lista)}</div></div>
            </div>`,
            footer: `<button class="btn btn-secondary" data-close>Revisar</button>
                     <button class="btn btn-primary btn-lg" id="btn-confirmar">${Icons.check(17)} Sí, emitir mi voto</button>`,
          });

          document.getElementById('btn-confirmar').addEventListener('click', function () {
            const btn = this;
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner"></span> Procesando voto…`;
            modalAbierto.querySelector('[data-close]').disabled = true;
            setTimeout(() => {
              cerrarModal();
              State.hashVoto = sha256Mock();
              State.votoEmitido = true;
              const idx = c2.candidatos.findIndex(x => x.id === cand.id);
              if (idx >= 0) c2.resultados[idx]++;
              c2.participantes++;
              location.hash = '#/votante/comprobante';
            }, 2200);
          });
        });
      },
    };
  },
});

/* ---------- Pantalla de éxito (comprobante) ---------- */
RegistrarVista('votante/comprobante', {
  titulo: '¡Voto registrado!',
  sub: 'CU-07 · Comprobante de emisión',
  render() {
    if (!State.votoEmitido) { location.hash = '#/votante/tarjeton'; return { html: '' }; }
    return {
      html: `
      <div style="max-width:560px;margin:24px auto 0">
        <div class="card" style="text-align:center;padding:36px 30px">
          <div style="width:72px;height:72px;border-radius:50%;background:hsl(var(--success) / .12);color:hsl(var(--success));display:grid;place-items:center;margin:0 auto 18px">${Icons.check(38)}</div>
          <div style="font-size:23px;font-weight:800;letter-spacing:-0.02em">Tu voto fue registrado</div>
          <div class="text-muted" style="margin-top:8px;line-height:1.6">Guarda este comprobante. Certifica que participaste en <b>Elecciones Estudiantiles 2026</b>.<br>No contiene información sobre tu elección.</div>

          <div style="text-align:left;margin-top:26px">
            <div class="text-sm text-muted fw-600" style="margin-bottom:7px">HASH SHA-256 DEL COMPROBANTE</div>
            <div class="hash-box">${State.hashVoto}</div>
          </div>

          <div class="flex gap-10" style="margin-top:22px">
            <button class="btn btn-outline" style="flex:1" id="copiar-hash">${Icons.copy(16)} Copiar hash</button>
            <button class="btn btn-primary" style="flex:1">${Icons.download(16)} Descargar comprobante</button>
          </div>

          <div class="flex gap-10" style="margin-top:12px">
            <a class="btn btn-ghost btn-block" href="#/votante/certificados">Ver mis certificados →</a>
          </div>
        </div>
        <div class="alert alert-success" style="margin-top:16px">
          <span style="flex-shrink:0;margin-top:1px">${Icons.shield(17)}</span>
          <div><div class="alert-title">Anonimato garantizado</div>
          <div class="alert-body">La urna digital almacena tu voto sin ninguna referencia a tu identidad. El hash solo prueba tu participación.</div></div>
        </div>
      </div>`,
      mount(root) {
        root.querySelector('#copiar-hash').addEventListener('click', () => {
          navigator.clipboard?.writeText(State.hashVoto).catch(() => {});
          toast('Hash copiado al portapapeles');
        });
      },
    };
  },
});

/* ---------- CU-08 (votante): Resultados ---------- */
RegistrarVista('votante/resultados', {
  titulo: 'Resultados',
  sub: 'CU-08 · Visualización según reglas de visibilidad',
  render() {
    const c = catActiva();
    const visible = State.estadoEleccion === 'FINALIZADA' || c.enVivo;
    if (!visible) {
      return {
        html: `<div class="card card-body" style="text-align:center;padding:60px 30px">
          <div style="width:60px;height:60px;border-radius:50%;background:hsl(var(--muted));color:hsl(var(--muted-foreground));display:grid;place-items:center;margin:0 auto 16px">${Icons.lock(26)}</div>
          <div class="fw-600" style="font-size:16px">Resultados no disponibles</div>
          <div class="text-muted text-sm" style="margin-top:6px;max-width:380px;margin-inline:auto">Los resultados parciales no están habilitados para los votantes en esta elección. Podrás consultarlos cuando finalice el proceso.</div>
        </div>`,
      };
    }
    const total = c.resultados.reduce((a, b) => a + b, 0);
    return {
      html: `
      <div class="flex items-center justify-between mb-20">
        <div><div class="section-title">${esc(c.titulo)}</div>
        <div class="section-sub" style="margin-bottom:0">${State.estadoEleccion === 'FINALIZADA' ? 'Resultados finales' : 'Avance en tiempo real'}</div></div>
        <div class="flex items-center gap-10">
          <span class="badge ${State.enVivo ? 'badge-success' : 'badge-muted'}">${State.enVivo ? 'EN VIVO' : 'ESTÁTICO'}</span>
          ${badgeEstado(State.estadoEleccion)}
        </div>
      </div>
      <div class="kpi-grid">
        ${kpi({ label: 'Votos contabilizados', valor: fmtNum(total), icono: Icons.vote(16), tendencia: `<span class="text-muted">de ${fmtNum(c.padron)} habilitados</span>` })}
        ${kpi({ label: 'Participación', valor: Math.round((c.participantes / c.padron) * 100) + '%', icono: Icons.chart(16) })}
        ${kpi({ label: 'Votos en blanco', valor: fmtNum(c.resultados[c.resultados.length - 1]), icono: Icons.checkSquare(16) })}
        ${kpi({ label: 'Casillas', valor: String(c.candidatos.length), icono: Icons.layout(16) })}
      </div>
      <div class="card">
        <div class="card-header"><div class="card-title">${Icons.chart(16)} Conteo por casilla</div></div>
        <div class="card-body" id="res-barras">
          ${barras(c.candidatos.map((cand, i) => ({ nombre: cand.nombre, valor: c.resultados[i], cls: cand.esBlanco ? 'blanco' : '' })))}
        </div>
      </div>`,
      mount(root) {
        if (State.enVivo && State.estadoEleccion !== 'FINALIZADA') {
          State.intervaloRT = setInterval(() => {
            const i = Math.floor(Math.random() * c.candidatos.length);
            c.resultados[i] += Math.floor(Math.random() * 3);
            const tot = c.resultados.reduce((a, b) => a + b, 0);
            root.querySelector('#res-barras').innerHTML = barras(c.candidatos.map((cand, j) => ({ nombre: cand.nombre, valor: c.resultados[j], cls: cand.esBlanco ? 'blanco' : '' })));
          }, 2600);
        }
      },
    };
  },
});

/* ---------- CU-12: Certificados ---------- */
RegistrarVista('votante/certificados', {
  titulo: 'Mis certificados',
  sub: 'CU-12 · Certificados digitales de participación',
  render() {
    return {
      html: `
      <div class="section-title">Historial de participación</div>
      <div class="section-sub">Descarga tu certificado en PDF con código QR verificable</div>
      <div class="grid-auto">
        ${DB.certificados.map(cert => `
          <div class="card">
            <div class="card-body">
              <div class="flex items-center justify-between mb-16">
                <span class="badge badge-success">${Icons.award(12)} Certificado válido</span>
                <span class="text-sm text-muted">${fmtFecha(cert.fecha)}</span>
              </div>
              <div class="fw-600" style="font-size:15px">${esc(cert.titulo)}</div>
              <div class="text-sm text-muted" style="margin:4px 0 16px">Código: <span class="font-mono">${esc(cert.codigo)}</span></div>
              <div class="flex justify-center" style="padding:14px;background:#fff;border-radius:12px;color:#000">${qrMock(cert.codigo, 130)}</div>
              <div class="text-sm text-muted" style="text-align:center;margin-top:8px">Escanea para verificar autenticidad</div>
              <button class="btn btn-primary btn-block" style="margin-top:16px">${Icons.download(15)} Descargar PDF</button>
            </div>
          </div>`).join('')}

        ${State.votoEmitido ? `
        <div class="card">
          <div class="card-body">
            <div class="flex items-center justify-between mb-16">
              <span class="badge badge-success">${Icons.award(12)} Disponible</span>
              <span class="text-sm text-muted">hoy</span>
            </div>
            <div class="fw-600" style="font-size:15px">Elecciones Estudiantiles 2026</div>
            <div class="text-sm text-muted" style="margin:4px 0 16px">Código: <span class="font-mono">CERT-2026-7D21E9</span></div>
            <div class="flex justify-center" style="padding:14px;background:#fff;border-radius:12px;color:#000">${qrMock(State.hashVoto || 'x', 130)}</div>
            <div class="text-sm text-muted" style="text-align:center;margin-top:8px">Escanea para verificar autenticidad</div>
            <button class="btn btn-primary btn-block" style="margin-top:16px">${Icons.download(15)} Descargar PDF</button>
          </div>
        </div>` : ''}
      </div>`,
    };
  },
});
