<script setup>
import { computed } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import KpiCard from '../../components/KpiCard.vue'
import { db, fmtNum } from '../../lib/data'
import { toast } from '../../stores/toast'

const k = computed(() => db.consistencia)

function exportar() {
  toast('Exportando bitácora a CSV…', 'info')
}
</script>

<template>
  <div class="card mb-20">
    <div class="card-header">
      <div class="card-title"><AppIcon name="checkSquare" :size="16" /> Ecuación de consistencia matemática</div>
      <div class="card-desc">Verificación automática: el padrón debe cuadrar con la urna</div>
    </div>
    <div class="card-body">
      <div class="equacion">
        <span class="eq-num">{{ fmtNum(k.padron) }}</span><span class="eq-sign">padrón</span>
        <span class="eq-sign">=</span>
        <span class="eq-num">{{ fmtNum(k.votosUrna) }}</span><span class="eq-sign">votos urna</span>
        <span class="eq-sign">+</span>
        <span class="eq-num">{{ fmtNum(k.padron - k.votosUrna) }}</span><span class="eq-sign">abstenciones</span>
        <span class="eq-ok"><AppIcon name="check" :size="20" /></span>
      </div>

      <div class="grid-3 mt-20">
        <KpiCard label="Votos en urna" :valor="fmtNum(k.votosUrna)" icon="checkSquare">
          <template #trend>
            <span style="color: hsl(var(--success))">coincide con participantes</span>
          </template>
        </KpiCard>

        <KpiCard label="Doble voto detectado" valor="0" icon="shield">
          <template #trend><span class="text-muted">restricción UNIQUE usuario-categoría</span></template>
        </KpiCard>

        <KpiCard label="Alertas de integridad" valor="0" icon="alert">
          <template #trend><span style="color: hsl(var(--success))">sin anomalías</span></template>
        </KpiCard>
      </div>

      <div class="alert alert-info" style="margin-top: 16px; margin-bottom: 0">
        <span style="flex-shrink: 0; margin-top: 1px"><AppIcon name="info" :size="17" /></span>
        <div>
          <div class="alert-title">Anonimato preservado</div>
          <div class="alert-body">
            La urna digital no almacena identidad de votantes. La auditoría valida totales y
            trazabilidad, nunca preferencias individuales.
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header flex items-center" style="padding-bottom: 16px">
      <div style="flex: 1">
        <div class="card-title"><AppIcon name="scroll" :size="16" /> Bitácora de eventos</div>
        <div class="card-desc">Registro inalterable con hash de trazabilidad · solo lectura</div>
      </div>
      <button class="btn btn-outline" @click="exportar">
        <AppIcon name="download" :size="15" /> Exportar CSV
      </button>
    </div>

    <div style="padding: 0 22px 22px">
      <div class="table-wrap stack">
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Timestamp</th>
              <th>Usuario</th>
              <th>Módulo</th>
              <th>Acción</th>
              <th>IP</th>
              <th>Hash</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in db.logs" :key="log.id">
              <td data-th="#" class="text-muted">{{ log.id }}</td>
              <td data-th="Timestamp" class="font-mono" style="font-size: 11.5px">{{ log.ts }}</td>
              <td data-th="Usuario">{{ log.usuario }}</td>
              <td data-th="Módulo">{{ log.modulo }}</td>
              <td data-th="Acción" class="fw-600">{{ log.accion }}</td>
              <td data-th="IP" class="font-mono" style="font-size: 11.5px">{{ log.ip }}</td>
              <td data-th="Hash" class="font-mono" style="font-size: 11.5px; color: hsl(var(--muted-foreground))">
                {{ log.hash }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex items-center gap-10 text-sm text-muted" style="margin-top: 12px">
        <AppIcon name="lock" :size="14" /> Los registros son append-only: no se pueden editar ni eliminar.
      </div>
    </div>
  </div>
</template>
