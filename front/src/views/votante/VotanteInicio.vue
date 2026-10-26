<script setup>
import { RouterLink } from 'vue-router'
import AppIcon from '../../components/AppIcon.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import { db, fmtFecha, state } from '../../lib/data'

function yaVoto(categoria) {
  return categoria.id === 1 && state.votoEmitido
}
</script>

<template>
  <div class="alert alert-info">
    <span style="flex-shrink: 0; margin-top: 1px"><AppIcon name="shield" :size="17" /></span>
    <div>
      <div class="alert-title">Tu voto es secreto</div>
      <div class="alert-body">
        El sistema guarda tu voto sin asociarlo a tu identidad. Solo recibirás un comprobante con Hash
        SHA-256 que certifica <b>que votaste</b>, nunca <b>por quién</b>.
      </div>
    </div>
  </div>

  <div class="section-title">Elecciones disponibles</div>
  <div class="section-sub">Selecciona una elección activa para emitir tu voto</div>

  <div class="grid-auto">
    <div v-for="categoria in db.categorias" :key="categoria.id" class="card">
      <div class="card-body">
        <div class="flex items-center justify-between mb-16">
          <EstadoBadge :estado="categoria.estado" />
          <span class="text-sm text-muted">{{ fmtFecha(categoria.apertura) }} → {{ fmtFecha(categoria.cierre) }}</span>
        </div>

        <div class="fw-600" style="font-size: 16px; letter-spacing: -0.01em">{{ categoria.titulo }}</div>
        <div class="text-sm text-muted" style="margin: 6px 0 16px; line-height: 1.55">
          {{ categoria.descripcion }}
        </div>

        <RouterLink
          v-if="categoria.estado === 'ACTIVA' && !yaVoto(categoria) && state.estadoEleccion !== 'CERRANDO'"
          class="btn btn-primary btn-block"
          to="/votante/tarjeton"
        >
          <AppIcon name="vote" :size="16" /> Votar ahora
        </RouterLink>

        <RouterLink
          v-else-if="yaVoto(categoria)"
          class="btn btn-success btn-block"
          to="/votante/comprobante"
        >
          <AppIcon name="check" :size="16" /> Voto registrado
        </RouterLink>

        <button
          v-else-if="categoria.estado === 'CERRANDO'"
          class="btn btn-secondary btn-block"
          disabled
        >
          <AppIcon name="lock" :size="15" /> Cerrando…
        </button>

        <RouterLink
          v-else-if="categoria.estado === 'FINALIZADA'"
          class="btn btn-outline btn-block"
          to="/votante/resultados"
        >
          <AppIcon name="chart" :size="15" /> Ver resultados
        </RouterLink>

        <button v-else class="btn btn-secondary btn-block" disabled>
          <AppIcon name="clock" :size="15" />
          {{ categoria.estado === 'PROGRAMADA' ? 'Aún no inicia' : 'No disponible' }}
        </button>
      </div>
    </div>
  </div>

  <div class="card mt-28">
    <div class="card-header">
      <div class="card-title"><AppIcon name="scroll" :size="16" /> Normativas vigentes</div>
      <div class="card-desc">Documentos que rigen el proceso electoral</div>
    </div>
    <div class="card-body" style="padding-top: 14px">
      <div v-for="normativa in db.normativas" :key="normativa.id" class="fila">
        <div class="pdf-icon">PDF</div>
        <div style="flex: 1; min-width: 0">
          <div class="fw-600" style="font-size: 13.5px">{{ normativa.titulo }}</div>
          <div class="text-sm text-muted">Publicado el {{ fmtFecha(normativa.fecha) }}</div>
        </div>
        <button class="btn btn-outline btn-sm"><AppIcon name="download" :size="14" /> Descargar</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pdf-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: hsl(var(--destructive) / 0.12);
  color: hsl(var(--destructive));
  font-size: 10px;
  font-weight: 800;
}
</style>
