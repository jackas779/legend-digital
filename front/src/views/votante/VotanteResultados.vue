<script setup>
import { computed, onBeforeUnmount, onMounted } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import BarList from '../../components/BarList.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import KpiCard from '../../components/KpiCard.vue'
import { db, fmtNum, state } from '../../lib/data'

const categoria = computed(() => db.categorias[0])
const visible = computed(() => state.estadoEleccion === 'FINALIZADA' || categoria.value.enVivo)
const total = computed(() => categoria.value.resultados.reduce((a, b) => a + b, 0))
const items = computed(() =>
  categoria.value.candidatos.map((candidato, index) => ({
    nombre: candidato.nombre,
    valor: categoria.value.resultados[index] || 0,
    cls: candidato.esBlanco ? 'blanco' : '',
  })),
)

let intervalo = null

function detener() {
  if (intervalo) {
    window.clearInterval(intervalo)
    intervalo = null
  }
}

onMounted(() => {
  if (!visible.value || state.estadoEleccion === 'FINALIZADA' || !state.enVivo) return

  intervalo = window.setInterval(() => {
    const index = Math.floor(Math.random() * categoria.value.candidatos.length)
    categoria.value.resultados[index] += Math.floor(Math.random() * 3)
  }, 2600)
})

onBeforeUnmount(detener)
</script>

<template>
  <div v-if="!visible" class="card card-body" style="text-align: center; padding: 60px 30px">
    <div class="lock-circle"><AppIcon name="lock" :size="26" /></div>
    <div class="fw-600" style="font-size: 16px">Resultados no disponibles</div>
    <div class="text-muted text-sm" style="margin-top: 6px; max-width: 380px; margin-inline: auto">
      Los resultados parciales no están habilitados para los votantes en esta elección. Podrás
      consultarlos cuando finalice el proceso.
    </div>
  </div>

  <template v-else>
    <div class="flex items-center justify-between mb-20">
      <div>
        <div class="section-title">{{ categoria.titulo }}</div>
        <div class="section-sub" style="margin-bottom: 0">
          {{ state.estadoEleccion === 'FINALIZADA' ? 'Resultados finales' : 'Avance en tiempo real' }}
        </div>
      </div>
      <div class="flex items-center gap-10">
        <span class="badge" :class="state.enVivo ? 'badge-success' : 'badge-muted'">
          {{ state.enVivo ? 'EN VIVO' : 'ESTÁTICO' }}
        </span>
        <EstadoBadge :estado="state.estadoEleccion" />
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="Votos contabilizados" :valor="fmtNum(total)" icon="vote">
        <template #trend><span class="text-muted">de {{ fmtNum(categoria.padron) }} habilitados</span></template>
      </KpiCard>
      <KpiCard
        label="Participación"
        :valor="`${Math.round((categoria.participantes / categoria.padron) * 100)}%`"
        icon="chart"
      />
      <KpiCard
        label="Votos en blanco"
        :valor="fmtNum(categoria.resultados[categoria.resultados.length - 1])"
        icon="checkSquare"
      />
      <KpiCard label="Casillas" :valor="String(categoria.candidatos.length)" icon="layout" />
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="chart" :size="16" /> Conteo por casilla</div>
      </div>
      <div class="card-body">
        <BarList :items="items" />
      </div>
    </div>
  </template>
</template>

<style scoped>
.lock-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
  display: grid;
  place-items: center;
  margin: 0 auto 16px;
}
</style>
