<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import BarList from '../../components/BarList.vue'
import DonutChart from '../../components/DonutChart.vue'
import KpiCard from '../../components/KpiCard.vue'
import { db, fmtNum, state } from '../../lib/data'
import { toast } from '../../stores/toast'

const categoria = computed(() => db.categorias[0])
const total = computed(() => categoria.value.resultados.reduce((a, b) => a + b, 0))
const items = computed(() =>
  categoria.value.candidatos.map((candidato, index) => ({
    nombre: candidato.nombre,
    valor: categoria.value.resultados[index] || 0,
    cls: candidato.esBlanco ? 'blanco' : '',
  })),
)
const hora = ref(new Date().toLocaleTimeString('es-CO'))

let intervalo = null

function detener() {
  if (intervalo) {
    window.clearInterval(intervalo)
    intervalo = null
  }
}

function arrancar() {
  detener()
  intervalo = window.setInterval(() => {
    const index = Math.floor(Math.random() * categoria.value.candidatos.length)
    categoria.value.resultados[index] += Math.floor(Math.random() * 4) + 1
    hora.value = new Date().toLocaleTimeString('es-CO')
  }, 2000)
}

function alternarTiempoReal() {
  state.enVivo = !state.enVivo
  if (state.enVivo) {
    arrancar()
    toast('Actualización en tiempo real conectada', 'info')
  } else {
    detener()
    toast('Actualización en tiempo real pausada', 'info')
  }
}

onMounted(() => {
  if (state.enVivo) arrancar()
})

onBeforeUnmount(detener)
</script>

<template>
  <div class="flex items-center justify-between mb-20" style="flex-wrap: wrap; gap: 12px">
    <div>
      <div class="section-title">{{ categoria.titulo }}</div>
      <div class="section-sub" style="margin-bottom: 0">
        Solo lectura · actualización automática vía WebSocket
      </div>
    </div>
    <div class="flex items-center gap-10">
      <label class="switch">
        <input type="checkbox" :checked="state.enVivo" @change="alternarTiempoReal" />
        <span class="slider" />
      </label>
      <span class="text-sm fw-600">Tiempo real</span>
      <span class="badge" :class="state.enVivo ? 'badge-success' : 'badge-muted'">
        {{ state.enVivo ? 'CONECTADO' : 'PAUSADO' }}
      </span>
    </div>
  </div>

  <div class="kpi-grid">
    <KpiCard label="Padrón habilitado" :valor="fmtNum(categoria.padron)" icon="users">
      <template #trend><span class="text-muted">registrados en el sistema</span></template>
    </KpiCard>

    <KpiCard label="Participantes" :valor="fmtNum(categoria.participantes)" icon="vote">
      <template #trend>
        <span style="color: hsl(var(--success))"><AppIcon name="activity" :size="13" /> en curso</span>
      </template>
    </KpiCard>

    <KpiCard label="Votos en urna" :valor="fmtNum(total)" icon="checkSquare">
      <template #trend><span class="text-muted">{{ categoria.candidatos.length }} casillas</span></template>
    </KpiCard>

    <KpiCard
      label="Abstenciones"
      :valor="fmtNum(categoria.padron - categoria.participantes)"
      icon="clock"
    >
      <template #trend><span class="text-muted">sin participación</span></template>
    </KpiCard>
  </div>

  <div class="grid-2" style="grid-template-columns: 1.5fr 1fr">
    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="chart" :size="16" /> Conteo por casilla</div>
        <div class="card-desc">Votos registrados en la urna digital (anónimos)</div>
      </div>
      <div class="card-body">
        <BarList :items="items" />
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="activity" :size="16" /> Participación</div>
        <div class="card-desc">Padrón vs. asistencia electoral</div>
      </div>
      <div class="card-body" style="display: grid; place-items: center; padding: 26px">
        <DonutChart :participantes="categoria.participantes" :total="categoria.padron" />
      </div>
      <div class="card-footer" style="justify-content: center">
        <span class="text-sm text-muted">Actualizado: {{ hora }}</span>
      </div>
    </div>
  </div>
</template>
