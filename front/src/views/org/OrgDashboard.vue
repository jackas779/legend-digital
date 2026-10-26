<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '../../components/AppIcon.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import KpiCard from '../../components/KpiCard.vue'
import { db, fmtFecha, state } from '../../lib/data'

const categoria = computed(() => db.categorias[0])

const pendientes = computed(() => [
  { t: 'Revisar biografías de candidatos', ok: true },
  { t: 'Publicar acuerdo de cronograma', ok: true },
  { t: 'Estandarizar fotos de la Lista 4', ok: false },
  { t: 'Configurar resultados en vivo', ok: !categoria.value.enVivo },
])
</script>

<template>
  <div class="kpi-grid">
    <KpiCard label="Elección actual" icon="calendar">
      <template #value><EstadoBadge :estado="state.estadoEleccion" /></template>
      <template #trend><span class="text-muted">{{ categoria.titulo }}</span></template>
    </KpiCard>

    <KpiCard
      label="Candidatos en tarjetón"
      :valor="String(categoria.candidatos.length)"
      icon="checkSquare"
    >
      <template #trend><span class="text-muted">incluye voto en blanco</span></template>
    </KpiCard>

    <KpiCard label="Normativas publicadas" :valor="String(db.normativas.length)" icon="fileText">
      <template #trend><span class="text-muted">2 PDF + reglamento</span></template>
    </KpiCard>

    <KpiCard label="Recursos multimedia" :valor="String(db.multimedia.length)" icon="image">
      <template #trend><span class="text-muted">fotos y banners</span></template>
    </KpiCard>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="calendar" :size="16" /> Cronograma</div>
        <div class="card-desc">Fechas de apertura y cierre programadas</div>
      </div>
      <div class="card-body">
        <div class="fila">
          <div>
            <div class="fw-600" style="font-size: 13.5px">Apertura</div>
            <div class="text-sm text-muted">{{ fmtFecha(categoria.apertura) }} · 07:00</div>
          </div>
          <span class="badge badge-success"><AppIcon name="check" :size="12" /> Cumplida</span>
        </div>
        <div class="fila">
          <div>
            <div class="fw-600" style="font-size: 13.5px">Cierre</div>
            <div class="text-sm text-muted">{{ fmtFecha(categoria.cierre) }} · 20:00</div>
          </div>
          <span class="badge badge-info">Pendiente</span>
        </div>
        <div style="margin-top: 18px" class="progress">
          <div class="progress-bar" style="width: 64%" />
        </div>
        <div class="text-sm text-muted" style="margin-top: 6px">64% del tiempo electoral transcurrido</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="checkSquare" :size="16" /> Pendientes</div>
        <div class="card-desc">Tareas sugeridas antes del cierre</div>
      </div>
      <div class="card-body">
        <div v-for="pendiente in pendientes" :key="pendiente.t" class="fila">
          <span
            :style="{ color: pendiente.ok ? 'hsl(var(--success))' : 'hsl(var(--warning))', flexShrink: 0 }"
          >
            <AppIcon :name="pendiente.ok ? 'check' : 'clock'" :size="16" />
          </span>
          <span
            style="flex: 1; font-size: 13.5px"
            :style="pendiente.ok ? 'text-decoration: line-through; color: hsl(var(--muted-foreground))' : ''"
          >
            {{ pendiente.t }}
          </span>
          <span v-if="!pendiente.ok" class="badge badge-warning">Pendiente</span>
        </div>
      </div>
      <div class="card-footer">
        <RouterLink class="btn btn-primary btn-sm" to="/org/tarjeton">Ir al tarjetón</RouterLink>
      </div>
    </div>
  </div>
</template>
