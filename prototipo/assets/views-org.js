/* views-org.js — Módulo 2: Configuración electoral + Módulo 3: Cierre */

const catActiva = () => DB.categorias.find(c => c.id === 1);
const editable = () => ['BORRADOR', 'PROGRAMADA'].includes(State.estadoEleccion);

function bannerBloqueo() {
  if (editable()) return '';
  return `<div class="locked-banner">
    <span style="flex-shrink:0">${Icons.lock(16)}</span>
    <span>La elección está en estado <b>${ESTADOS[State.estadoEleccion].label.toUpperCase()}</b>: los formularios de configuración están bloqueados (solo lectura). Vuelve a <b>Borrador</b> o <b>Programada</b> con el simulador del panel superior para editar.</span>
  </div>`;
}

/* ---------- Dashboard ORGANIZADOR ---------- */
RegistrarVista('org', {
  titulo: 'Dashboard',
  sub: 'Resumen de la elección a tu cargo',
  render() {
    const c = catActiva();
    return {
      html: `
      <div class="kpi-grid">
        ${kpi({ label: 'Elección actual', valor: badgeEstado(State.estadoEleccion), icono: Icons.calendar(16), tendencia: `<span class="text-muted">${esc(c.titulo)}</span>`, tendCls: 'neutral' })}
        ${kpi({ label: 'Candidatos en tarjetón', valor: String(c.candidatos.length), icono: Icons.checkSquare(16), tendencia: `<span class="text-muted">incluye voto en blanco</span>`, tendCls: 'neutral' })}
        ${kpi({ label: 'Normativas publicadas', valor: String(DB.normativas.length), icono: Icons.fileText(16), tendencia: `<span class="text-muted">2 PDF + reglamento</span>`, tendCls: 'neutral' })}
        ${kpi({ label: 'Recursos multimedia', valor: String(DB.multimedia.length), icono: Icons.image(16), tendencia: `<span class="text-muted">fotos y banners</span>`, tendCls: 'neutral' })}
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.calendar(16)} Cronograma</div>
          <div class="card-desc">Fechas de apertura y cierre programadas</div></div>
          <div class="card-body">
            <div class="flex justify-between items-center mb-16">
              <div><div class="fw-600" style="font-size:13.5px">Apertura</div><div class="text-sm text-muted">${fmtFecha(c.apertura)} · 07:00</div></div>
              <span class="badge badge-success">${Icons.check(12)} Cumplida</span>
            </div>
            <div class="flex justify-between items-center">
              <div><div class="fw-600" style="font-size:13.5px">Cierre</div><div class="text-sm text-muted">${fmtFecha(c.cierre)} · 20:00</div></div>
              <span class="badge badge-info">Pendiente</span>
            </div>
            <div style="margin-top:18px" class="progress"><div class="progress-bar" style="width:64%"></div></div>
            <div class="text-sm text-muted" style="margin-top:6px">64% del tiempo electoral transcurrido</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.checkSquare(16)} Pendientes</div>
          <div class="card-desc">Tareas sugeridas antes del cierre</div></div>
          <div class="card-body">
            ${[
              { t: 'Revisar biografías de candidatos', ok: true },
              { t: 'Publicar acuerdo de cronograma', ok: true },
              { t: 'Estandarizar fotos de la Lista 4', ok: false },
              { t: 'Configurar resultados en vivo', ok: !c.enVivo },
            ].map(p => `
              <div class="flex items-center gap-10" style="padding:8px 0;border-bottom:1px solid hsl(var(--border))">
                <span style="color:${p.ok ? 'hsl(var(--success))' : 'hsl(var(--warning))'}">${p.ok ? Icons.check(16) : Icons.clock(16)}</span>
                <span style="flex:1;font-size:13.5px;${p.ok ? 'text-decoration:line-through;color:hsl(var(--muted-foreground))' : ''}">${p.t}</span>
                ${p.ok ? '' : '<span class="badge badge-warning">Pendiente</span>'}
              </div>`).join('')}
          </div>
          <div class="card-footer"><a class="btn btn-primary btn-sm" href="#/org/tarjeton">Ir al tarjetón</a></div>
        </div>
      </div>`,
    };
  },
});

/* ---------- CU-04: Categorías ---------- */
RegistrarVista('org/categorias', {
  titulo: 'Categorías electorales',
  sub: 'CU-04 · Crear y configurar categorías',
  render() {
    const c = catActiva();
    return {
      html: `
      ${bannerBloqueo()}
      <div class="grid-2" style="grid-template-columns: 1fr 1.3fr">
        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.calendar(16)} Configuración</div>
          <div class="card-desc">Parámetros de la categoría seleccionada</div></div>
          <div class="card-body">
            <div class="field"><label>Título de la elección</label>
              <input class="input" id="c-titulo" value="${esc(c.titulo)}" ${editable() ? '' : 'disabled'}></div>
            <div class="field"><label>Descripción</label>
              <textarea class="textarea" id="c-desc" ${editable() ? '' : 'disabled'}>${esc(c.descripcion)}</textarea></div>
            <div class="field-row">
              <div class="field"><label>Apertura</label>
                <input class="input" type="datetime-local" id="c-aper" value="${c.apertura}" ${editable() ? '' : 'disabled'}></div>
              <div class="field"><label>Cierre</label>
                <input class="input" type="datetime-local" id="c-cierre" value="${c.cierre}" ${editable() ? '' : 'disabled'}></div>
            </div>
            <div class="flex items-center gap-10 mb-16">
              ${switchToggle('c-vivo')}
              <div><div class="fw-600" style="font-size:13px">Resultados en tiempo real</div>
              <div class="text-sm text-muted">Visibles para el auditor y (si se activa) para los votantes</div></div>
            </div>
            <button class="btn btn-primary btn-block" id="c-guardar" ${editable() ? '' : 'disabled'}>${Icons.check(16)} Guardar configuración</button>
            ${!editable() ? '<div class="hint" style="margin-top:8px">Campos bloqueados por el estado de la elección</div>' : ''}
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.layout(16)} Categorías del sistema</div>
          <div class="card-desc">Todas las elecciones y sus estados actuales</div></div>
          <div class="card-body" style="padding:0 22px 22px">
            ${DB.categorias.map(cat => `
              <div class="flex items-center gap-14" style="padding:14px 0;border-bottom:1px solid hsl(var(--border))">
                <div style="flex:1;min-width:0">
                  <div class="fw-600" style="font-size:14px">${esc(cat.titulo)}</div>
                  <div class="text-sm text-muted">${fmtFecha(cat.apertura)} → ${fmtFecha(cat.cierre)}</div>
                </div>
                ${badgeEstado(cat.estado)}
                <button class="btn btn-ghost btn-sm btn-icon" title="Ver">${Icons.chevronRight(15)}</button>
              </div>`).join('')}
            <button class="btn btn-outline btn-block" style="margin-top:16px" ${editable() ? '' : 'disabled'}>${Icons.plus(15)} Nueva categoría</button>
          </div>
        </div>
      </div>`,
      mount(root) {
        root.querySelector('#c-vivo')?.addEventListener('change', e => { State.enVivo = e.target.checked; toast(e.target.checked ? 'Resultados en vivo activados' : 'Resultados en vivo desactivados'); });
        root.querySelector('#c-guardar')?.addEventListener('click', () => toast('Configuración de categoría guardada'));
      },
    };
  },
});

/* ---------- CU-05: Normativas ---------- */
RegistrarVista('org/normativas', {
  titulo: 'Normativas',
  sub: 'CU-05 · Establecer normativas y reglamentos',
  render() {
    return {
      html: `
      ${bannerBloqueo()}
      <div class="grid-2" style="grid-template-columns: 1.3fr 1fr">
        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.fileText(16)} Editor de normativa</div>
          <div class="card-desc">Redacta en HTML/Markdown. Se publica tal cual a los votantes.</div></div>
          <div class="card-body">
            <div class="field"><label>Título</label><input class="input" value="Reglamento Electoral Estudiantil 2026" ${editable() ? '' : 'disabled'}></div>
            <div class="tabs" style="margin-bottom:12px">
              <button class="tab active">Redactar</button><button class="tab">Vista previa</button>
            </div>
            <div class="field">
              <textarea class="textarea" style="min-height:190px" ${editable() ? '' : 'disabled'}>## Artículo 1. Del sufragio
Todo estudiante activo podrá emitir su voto de forma secreta...

## Artículo 2. Del tarjetón
El tarjetón incluirá la opción "Voto en Blanco" como última casilla.</textarea>
            </div>
            <button class="btn btn-primary" ${editable() ? '' : 'disabled'}>${Icons.check(16)} Publicar normativa</button>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.upload(16)} Documentos PDF</div>
          <div class="card-desc">Archivos adjuntos · válidos PDF/DOCX · máx. 10 MB</div></div>
          <div class="card-body">
            <div class="dropzone" id="nz">
              <div class="dz-icon">${Icons.upload(22)}</div>
              <div class="dz-title">Arrastra el PDF aquí</div>
              <div class="dz-hint">pdf o docx · hasta 10 MB</div>
            </div>
            <div style="margin-top:16px">
              ${DB.normativas.map(n => `
                <div class="file-item" style="margin-top:0;margin-bottom:10px">
                  <div class="fi-icon" style="background:hsl(var(--destructive) / .12);color:hsl(var(--destructive))">PDF</div>
                  <div style="flex:1;min-width:0">
                    <div class="fi-name">${esc(n.titulo)}</div>
                    <div class="fi-meta">${esc(n.pdf)} · ${esc(n.peso)} · ${fmtFecha(n.fecha)}</div>
                  </div>
                  <button class="btn btn-ghost btn-sm btn-icon" title="Descargar">${Icons.download(15)}</button>
                  <button class="btn btn-ghost btn-sm btn-icon" style="color:hsl(var(--destructive))" title="Eliminar" ${editable() ? '' : 'disabled'}>${Icons.trash(15)}</button>
                </div>`).join('')}
            </div>
          </div>
        </div>
      </div>`,
      mount(root) {
        const nz = root.querySelector('#nz');
        ['dragover', 'dragenter'].forEach(ev => nz.addEventListener(ev, e => { e.preventDefault(); nz.classList.add('dragover'); }));
        ['dragleave', 'drop'].forEach(ev => nz.addEventListener(ev, e => { e.preventDefault(); nz.classList.remove('dragover'); }));
        nz.addEventListener('drop', e => {
          const f = e.dataTransfer.files[0];
          if (!f) return;
          const mb = f.size / 1048576;
          if (mb > 10) { toast('El archivo supera los 10 MB', 'destructive'); return; }
          toast(`"${f.name}" validado (${mb.toFixed(1)} MB)`, 'success');
        });
      },
    };
  },
});

/* ---------- CU-06: Multimedia ---------- */
RegistrarVista('org/multimedia', {
  titulo: 'Recursos multimedia',
  sub: 'CU-06 · Cargar recursos multimedia',
  render() {
    return {
      html: `
      ${bannerBloqueo()}
      <div class="grid-2" style="grid-template-columns: 1fr 1.6fr">
        <div>
          <div class="card">
            <div class="card-header"><div class="card-title">${Icons.image(16)} Subir recurso</div>
            <div class="card-desc">JPG, PNG o WebP · máx. 5 MB</div></div>
            <div class="card-body">
              <div class="dropzone" id="mz">
                <div class="dz-icon">${Icons.image(22)}</div>
                <div class="dz-title">Arrastra una imagen</div>
                <div class="dz-hint">se estandarizará a 400×400 px</div>
              </div>
              <button class="btn btn-primary btn-block" style="margin-top:14px" ${editable() ? '' : 'disabled'}>${Icons.crop(15)} Recortar y estandarizar</button>
            </div>
          </div>
          <div class="card mt-20">
            <div class="card-header"><div class="card-title">${Icons.info(16)} Estandarización</div></div>
            <div class="card-body text-sm text-muted">
              Las fotos de candidatos se recortan a <b>cuadrado 1:1</b> y se comprimen a máx. 300 KB para que el tarjetón seavisualmente neutro.
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.layout(16)} Biblioteca (${DB.multimedia.length})</div>
          <div class="card-desc">Recursos disponibles para las categorías</div></div>
          <div class="card-body">
            <div class="grid-3 galeria">
              ${DB.multimedia.map(m => `
                <div class="card" style="box-shadow:none">
                  <div style="aspect-ratio:1;background:linear-gradient(135deg,hsl(243 60% 45%),hsl(271 60% 35%));border-radius:var(--radius) var(--radius) 0 0;display:grid;place-items:center;color:#fff">${Icons.image(28)}</div>
                  <div style="padding:11px 13px">
                    <div class="fw-600" style="font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(m.nombre)}</div>
                    <div class="text-sm text-muted">${esc(m.etiqueta)} · ${esc(m.peso)}</div>
                  </div>
                </div>`).join('')}
            </div>
          </div>
        </div>
      </div>`,
      mount(root) {
        const mz = root.querySelector('#mz');
        ['dragover', 'dragenter'].forEach(ev => mz.addEventListener(ev, e => { e.preventDefault(); mz.classList.add('dragover'); }));
        ['dragleave', 'drop'].forEach(ev => mz.addEventListener(ev, e => { e.preventDefault(); mz.classList.remove('dragover'); }));
        mz.addEventListener('drop', e => {
          const f = e.dataTransfer.files[0];
          if (!f) return;
          if (!f.type.startsWith('image/')) { toast('Solo se permiten imágenes', 'destructive'); return; }
          if (f.size > 5 * 1048576) { toast('La imagen supera los 5 MB', 'destructive'); return; }
          modalRecorte(f.name);
        });
      },
    };
  },
});

function modalRecorte(nombre) {
  modal({
    icon: 'primary', iconSvg: Icons.crop(20),
    titulo: 'Recortar imagen',
    desc: `Encuadre estandarizado 1:1 para <b>${esc(nombre)}</b>. Arrastra el marco y ajusta el zoom.`,
    ancho: 520,
    body: `
      <div class="crop-stage"><div class="crop-frame"></div></div>
      <div class="flex items-center gap-14" style="margin-top:16px">
        <span class="text-sm text-muted fw-600">Zoom</span>
        <input type="range" min="1" max="3" step="0.1" value="1.4" style="flex:1;accent-color:hsl(var(--primary))">
        <span class="badge badge-muted">400 × 400</span>
      </div>`,
    footer: `<button class="btn btn-secondary" data-close>Cancelar</button>
             <button class="btn btn-primary" id="crop-ok">${Icons.check(16)} Aplicar recorte</button>`,
  });
  document.getElementById('crop-ok').addEventListener('click', () => { cerrarModal(); toast('Imagen recortada y estandarizada'); });
}

/* ---------- CU-10: Tarjetón (drag & drop) ---------- */
RegistrarVista('org/tarjeton', {
  titulo: 'Construcción del tarjetón',
  sub: 'CU-10 · Gestionar candidatos (orden y voto en blanco)',
  render() {
    const c = catActiva();
    const bloqueado = !editable();
    return {
      html: `
      ${bannerBloqueo()}
      <div class="grid-2" style="grid-template-columns: 1fr 1fr">
        <div class="card">
          <div class="card-header flex items-center" style="padding-bottom:14px">
            <div style="flex:1"><div class="card-title">${Icons.grip(16)} Orden de casillas</div>
            <div class="card-desc">Arrastra para reordenar · el voto en blanco siempre va al final</div></div>
            ${bloqueado ? '<span class="badge badge-warning">' + Icons.lock(12) + ' Bloqueado</span>' : ''}
          </div>
          <div class="card-body">
            <div class="drag-list" id="drag-list">
              ${c.candidatos.map((cand, i) => `
                <div class="drag-item" draggable="${bloqueado ? 'false' : 'true'}" data-id="${cand.id}">
                  <span class="grip">${Icons.grip(16)}</span>
                  <span class="orden">${i + 1}</span>
                  ${avatar(cand.nombre, 34)}
                  <div class="di-info">
                    <div class="di-nombre">${esc(cand.nombre)}</div>
                    <div class="di-lista">${esc(cand.lista)}</div>
                  </div>
                  ${cand.esBlanco ? '<span class="badge badge-muted">Obligatoria</span>' : ''}
                </div>`).join('')}
            </div>
            <div class="flex gap-10" style="margin-top:16px;flex-wrap:wrap">
              <button class="btn btn-primary" ${bloqueado ? 'disabled' : ''} id="t-guardar">${Icons.check(16)} Guardar orden</button>
              <button class="btn btn-outline" ${bloqueado ? 'disabled' : ''}>${Icons.plus(15)} Agregar candidato</button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.checkSquare(16)} Vista previa del tarjetón</div>
          <div class="card-desc">Así lo verá el votante</div></div>
          <div class="card-body">
            <div class="tarjeton-grid tarjeton-preview">
              ${c.candidatos.map(cand => `
                <div class="tarjeton-option ${cand.esBlanco ? 'blanco' : ''}" style="cursor:default">
                  <div class="foto" style="background:${cand.esBlanco ? '' : 'linear-gradient(135deg,hsl(243 70% 60%),hsl(271 70% 55%))'}">${cand.esBlanco ? Icons.checkSquare(28) : cand.nombre.split(' ').map(p => p[0]).slice(0, 2).join('')}</div>
                  <div class="cand-nombre">${esc(cand.nombre)}</div>
                  <div class="cand-lista">${esc(cand.lista)}</div>
                </div>`).join('')}
            </div>
          </div>
        </div>
      </div>`,
      mount(root) {
        if (bloqueado) return;
        const lista = root.querySelector('#drag-list');
        let arrastrado = null;
        lista.querySelectorAll('.drag-item').forEach(item => {
          item.addEventListener('dragstart', () => { arrastrado = item; item.classList.add('dragging'); });
          item.addEventListener('dragend', () => { item.classList.remove('dragging'); renumerar(); });
          item.addEventListener('dragover', e => e.preventDefault());
          item.addEventListener('drop', e => {
            e.preventDefault();
            if (!arrastrado || arrastrado === item) return;
            const items = [...lista.querySelectorAll('.drag-item')];
            const desde = items.indexOf(arrastrado), hacia = items.indexOf(item);
            if (desde < hacia) item.after(arrastrado); else item.before(arrastrado);
          });
        });
        function renumerar() { lista.querySelectorAll('.orden').forEach((n, i) => n.textContent = i + 1); }
        root.querySelector('#t-guardar').addEventListener('click', () => {
          const nuevo = [...lista.querySelectorAll('.drag-item')].map((el, i) => {
            const cand = catActiva().candidatos.find(x => x.id === +el.dataset.id);
            return { ...cand, orden: i + 1 };
          });
          catActiva().candidatos = nuevo;
          toast('Orden del tarjetón guardado');
        });
      },
    };
  },
});

/* ---------- CU-11: Cerrar elección ---------- */
RegistrarVista('org/cierre', {
  titulo: 'Cerrar elección y generar acta',
  sub: 'CU-11 · Cierre del proceso y Acta de Escrutinio',
  render() {
    const c = catActiva();
    const finalizada = State.estadoEleccion === 'FINALIZADA';
    return {
      html: `
      <div class="grid-2" style="grid-template-columns: 1.4fr 1fr">
        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.award(16)} Acta de Escrutinio</div>
          <div class="card-desc">${esc(c.titulo)} · cierre ${fmtFecha(c.cierre)}</div></div>
          <div class="card-body">
            <div class="equacion">
              <span class="eq-num">${fmtNum(c.padron)}</span><span class="eq-sign">padrón</span>
              <span class="eq-sign">=</span>
              <span class="eq-num">${fmtNum(c.participantes)}</span><span class="eq-sign">votos</span>
              <span class="eq-sign">+</span>
              <span class="eq-num">${fmtNum(c.padron - c.participantes)}</span><span class="eq-sign">abstenciones</span>
              <span class="eq-ok">${Icons.check(18)}</span>
            </div>
            <div class="mt-20">
              ${barras(c.candidatos.map((cand, i) => ({ nombre: cand.nombre, valor: c.resultados[i], cls: cand.esBlanco ? 'blanco' : '' })), 0)}
            </div>
            <div class="hash-box mt-20">hash_sello_bd: 7f3a9c1e5b8d2f604a7c3e9b1d5f8a2c604b7e9d1f3a5c8b2e6d9f1a4c7b3e8d205</div>
          </div>
          <div class="card-footer">
            <button class="btn btn-outline" ${finalizada ? '' : 'disabled'}>${Icons.download(15)} Descargar Acta (PDF)</button>
            <button class="btn btn-primary" ${finalizada ? 'disabled' : ''} id="cierre-btn">${Icons.award(15)} Finalizar elección</button>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">${Icons.alert(16)} Antes de cerrar</div></div>
          <div class="card-body">
            ${[
              'La urna queda sellada: no se aceptan más votos.',
              'Se genera el Acta de Escrutinio con hash de sellado.',
              'Los votantes podrán descargar sus certificados.',
              'Los resultados pasan a ser públicos.',
            ].map(t => `<div class="flex gap-10 items-center" style="padding:8px 0;border-bottom:1px solid hsl(var(--border));font-size:13.5px">
              <span style="color:hsl(var(--primary))">${Icons.check(15)}</span>${t}</div>`).join('')}
            <div class="alert alert-warning" style="margin-top:16px">
              <span style="flex-shrink:0;margin-top:1px">${Icons.alert(17)}</span>
              <div><div class="alert-title">Acción irreversible</div><div class="alert-body">Una vez finalizada la elección no podrás modificar candidatos ni normativas.</div></div>
            </div>
          </div>
        </div>
      </div>`,
      mount(root) {
        root.querySelector('#cierre-btn')?.addEventListener('click', () => {
          confirmar({
            titulo: '¿Finalizar la elección?',
            desc: 'La urna se sellará y se generará el Acta de Escrutinio. Esta acción no se puede deshacer.',
            textoBtn: 'Sí, finalizar',
            onOk() { State.estadoEleccion = 'FINALIZADA'; Render(); toast('Elección finalizada · Acta generada'); },
          });
        });
      },
    };
  },
});
