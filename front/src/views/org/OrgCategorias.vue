<script setup>
import { computed } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import BloqueoBanner from '../../components/BloqueoBanner.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import { db, fmtFecha, state } from '../../lib/data'
import { toast } from '../../stores/toast'

const categoria = computed(() => db.categorias[0])
const editable = computed(() => ['BORRADOR', 'PROGRAMADA'].includes(state.estadoEleccion))

function guardar() {
  toast('Configuración de categoría guardada')
}

function nuevaCategoria() {
  db.categorias.push({
    id: Date.now(),
    titulo: 'Nueva categoría electoral',
    descripcion: '',
    apertura: '2026-12-01T07:00',
    cierre: '2026-12-01T18:00',
    estado: 'BORRADOR',
    enVivo: false,
    candidatos: [],
    resultados: [],
    padron: 0,
    participantes: 0,
  })
  toast('Categoría creada en estado BORRADOR', 'info')
}
</script>

<template>
  <BloqueoBanner />

  <div class="grid-2" style="grid-template-columns: 1fr 1.3fr">
    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="calendar" :size="16" /> Configuración</div>
        <div class="card-desc">Parámetros de la categoría seleccionada</div>
      </div>
      <div class="card-body">
        <div class="field">
          <label>Título de la elección</label>
          <input v-model="categoria.titulo" class="input" :disabled="!editable" />
        </div>

        <div class="field">
          <label>Descripción</label>
          <textarea v-model="categoria.descripcion" class="textarea" :disabled="!editable" />
        </div>

        <div class="field-row">
          <div class="field">
            <label>Apertura</label>
            <input v-model="categoria.apertura" class="input" type="datetime-local" :disabled="!editable" />
          </div>
          <div class="field">
            <label>Cierre</label>
            <input v-model="categoria.cierre" class="input" type="datetime-local" :disabled="!editable" />
          </div>
        </div>

        <div class="flex items-center gap-10 mb-16">
          <label class="switch">
            <input v-model="categoria.enVivo" type="checkbox" :disabled="!editable" />
            <span class="slider" />
          </label>
          <div>
            <div class="fw-600" style="font-size: 13px">Resultados en tiempo real</div>
            <div class="text-sm text-muted">Visibles para el auditor y (si se activa) para los votantes</div>
          </div>
        </div>

        <button class="btn btn-primary btn-block" :disabled="!editable" @click="guardar">
          <AppIcon name="check" :size="16" /> Guardar configuración
        </button>
        <div v-if="!editable" class="hint" style="margin-top: 8px">
          Campos bloqueados por el estado de la elección
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="layout" :size="16" /> Categorías del sistema</div>
        <div class="card-desc">Todas las elecciones y sus estados actuales</div>
      </div>
      <div class="card-body" style="padding: 0 22px 22px">
        <div v-for="cat in db.categorias" :key="cat.id" class="fila">
          <div style="flex: 1; min-width: 0">
            <div class="fw-600" style="font-size: 14px">{{ cat.titulo }}</div>
            <div class="text-sm text-muted">{{ fmtFecha(cat.apertura) }} → {{ fmtFecha(cat.cierre) }}</div>
          </div>
          <EstadoBadge :estado="cat.estado" />
          <button class="btn btn-ghost btn-sm btn-icon" title="Ver">
            <AppIcon name="chevronRight" :size="15" />
          </button>
        </div>

        <button class="btn btn-outline btn-block" style="margin-top: 16px" :disabled="!editable" @click="nuevaCategoria">
          <AppIcon name="plus" :size="15" /> Nueva categoría
        </button>
      </div>
    </div>
  </div>
</template>
