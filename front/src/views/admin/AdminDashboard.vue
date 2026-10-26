<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '../../components/AppIcon.vue'
import KpiCard from '../../components/KpiCard.vue'
import { db, fmtNum } from '../../lib/data'

const votantes = computed(() => db.usuarios.filter((u) => u.rol === 'VOTANTE'))
const activos = computed(() => votantes.value.filter((u) => u.estado === 'ACTIVO').length)
const suspendidos = computed(() => votantes.value.filter((u) => u.estado === 'SUSPENDIDO').length)
const categoria = computed(() => db.categorias[0])
</script>

<template>
  <div class="kpi-grid">
    <KpiCard label="Usuarios del sistema" :valor="fmtNum(db.usuarios.length)" icon="users">
      <template #trend>
        <span class="text-muted">
          {{ votantes.length }} votantes · {{ db.usuarios.length - votantes.length }} staff
        </span>
      </template>
    </KpiCard>

    <KpiCard label="Elecciones activas" valor="1" icon="calendar">
      <template #trend><span class="text-muted">2 programadas/finalizadas</span></template>
    </KpiCard>

    <KpiCard label="Participación global" valor="41%" icon="vote">
      <template #trend>
        <span class="text-muted">
          {{ fmtNum(categoria.participantes) }} de {{ fmtNum(categoria.padron) }} habilitados
        </span>
      </template>
    </KpiCard>

    <KpiCard label="Cuentas bloqueadas" :valor="String(suspendidos)" icon="lock">
      <template #trend><span class="text-muted">{{ activos }} cuentas activas</span></template>
    </KpiCard>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="scroll" :size="16" /> Actividad reciente</div>
        <div class="card-desc">Últimos eventos registrados en la bitácora de auditoría</div>
      </div>
      <div class="card-body" style="padding-top: 14px">
        <div v-for="log in db.logs.slice(0, 5)" :key="log.id" class="fila">
          <div class="activity-dot" />
          <div style="flex: 1; min-width: 0">
            <div style="font-size: 13px; font-weight: 600">{{ log.accion }}</div>
            <div class="text-sm text-muted">{{ log.usuario }} · {{ log.modulo }} · IP {{ log.ip }}</div>
          </div>
          <div class="text-sm text-muted" style="white-space: nowrap">{{ log.ts.slice(11) }}</div>
        </div>
      </div>
      <div class="card-footer">
        <RouterLink class="btn btn-outline btn-sm" to="/auditor/logs">Ver bitácora completa</RouterLink>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="key" :size="16" /> Estado de seguridad</div>
        <div class="card-desc">Indicadores del módulo de autenticación</div>
      </div>
      <div class="card-body">
        <div class="fila">
          <div>
            <div class="fw-600" style="font-size: 13.5px">Sesiones JWT activas</div>
            <div class="text-sm text-muted">Access token 60 min · Refresh rotativo</div>
          </div>
          <span class="badge badge-success">7 activas</span>
        </div>
        <div class="fila">
          <div>
            <div class="fw-600" style="font-size: 13.5px">Intentos fallidos (24 h)</div>
            <div class="text-sm text-muted">Bloqueo automático a los 5 intentos</div>
          </div>
          <span class="badge badge-warning">3 eventos</span>
        </div>
        <div class="fila">
          <div>
            <div class="fw-600" style="font-size: 13.5px">Consistencia de la urna</div>
            <div class="text-sm text-muted">Padrón = votos + abstenciones</div>
          </div>
          <span class="badge badge-success"><AppIcon name="check" :size="12" /> OK</span>
        </div>
      </div>
      <div class="card-footer">
        <RouterLink class="btn btn-outline btn-sm" to="/admin/permisos">Matriz de permisos</RouterLink>
        <RouterLink class="btn btn-primary btn-sm" to="/admin/carga">Cargar votantes</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: hsl(var(--primary));
  flex-shrink: 0;
}
</style>
