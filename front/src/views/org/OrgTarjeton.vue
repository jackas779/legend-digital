<script setup>
import { computed, ref } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import BloqueoBanner from '../../components/BloqueoBanner.vue'
import UserAvatar from '../../components/UserAvatar.vue'
import { db, state } from '../../lib/data'
import { toast } from '../../stores/toast'

const categoria = computed(() => db.categorias[0])
const bloqueado = computed(() => !['BORRADOR', 'PROGRAMADA'].includes(state.estadoEleccion))

const candidatos = ref(categoria.value.candidatos.map((c) => ({ ...c })))
const dragIndex = ref(null)

function alArrastrar(index) {
  if (bloqueado.value) return
  dragIndex.value = index
}

function alSoltar(index) {
  if (bloqueado.value || dragIndex.value === null || dragIndex.value === index) return
  const copia = [...candidatos.value]
  const [movido] = copia.splice(dragIndex.value, 1)
  copia.splice(index, 0, movido)
  candidatos.value = copia
  dragIndex.value = null
}

function guardarOrden() {
  categoria.value.candidatos = candidatos.value.map((candidato, index) => ({
    ...candidato,
    orden: index + 1,
  }))
  toast('Orden del tarjetón guardado')
}

function agregarCandidato() {
  const nombre = window.prompt('Nombre del candidato:')
  if (!nombre?.trim()) return

  const lista = window.prompt('Partido o lista:') || 'Lista independiente'
  const nuevo = {
    id: Date.now(),
    nombre: nombre.trim(),
    lista: lista.trim(),
    orden: candidatos.value.length + 1,
    esBlanco: false,
  }

  const indiceBlanco = candidatos.value.findIndex((c) => c.esBlanco)
  if (indiceBlanco >= 0) candidatos.value.splice(indiceBlanco, 0, nuevo)
  else candidatos.value.push(nuevo)

  toast('Candidato agregado al tarjetón')
}
</script>

<template>
  <BloqueoBanner />

  <div class="grid-2" style="grid-template-columns: 1fr 1fr">
    <div class="card">
      <div class="card-header flex items-center" style="padding-bottom: 14px">
        <div style="flex: 1">
          <div class="card-title"><AppIcon name="grip" :size="16" /> Orden de casillas</div>
          <div class="card-desc">Arrastra para reordenar · el voto en blanco siempre va al final</div>
        </div>
        <span v-if="bloqueado" class="badge badge-warning"><AppIcon name="lock" :size="12" /> Bloqueado</span>
      </div>
      <div class="card-body">
        <div class="drag-list">
          <div
            v-for="(candidato, index) in candidatos"
            :key="candidato.id"
            class="drag-item"
            :draggable="!bloqueado"
            @dragstart="alArrastrar(index)"
            @dragover.prevent
            @drop="alSoltar(index)"
          >
            <span class="grip"><AppIcon name="grip" :size="16" /></span>
            <span class="orden">{{ index + 1 }}</span>
            <UserAvatar :nombre="candidato.nombre" :size="34" />
            <div class="di-info">
              <div class="di-nombre">{{ candidato.nombre }}</div>
              <div class="di-lista">{{ candidato.lista }}</div>
            </div>
            <span v-if="candidato.esBlanco" class="badge badge-muted">Obligatoria</span>
          </div>
        </div>

        <div class="flex gap-10" style="margin-top: 16px; flex-wrap: wrap">
          <button class="btn btn-primary" :disabled="bloqueado" @click="guardarOrden">
            <AppIcon name="check" :size="16" /> Guardar orden
          </button>
          <button class="btn btn-outline" :disabled="bloqueado" @click="agregarCandidato">
            <AppIcon name="plus" :size="15" /> Agregar candidato
          </button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="checkSquare" :size="16" /> Vista previa del tarjetón</div>
        <div class="card-desc">Así lo verá el votante</div>
      </div>
      <div class="card-body">
        <div class="tarjeton-grid tarjeton-preview">
          <div
            v-for="(candidato, index) in candidatos"
            :key="candidato.id"
            class="tarjeton-option"
            :class="{ blanco: candidato.esBlanco }"
            style="cursor: default"
          >
            <div
              class="foto"
              :style="
                candidato.esBlanco
                  ? ''
                  : { background: `linear-gradient(135deg, hsl(${243 + index * 8} 70% 60%), hsl(${271 + index * 6} 70% 55%))` }
              "
            >
              <AppIcon v-if="candidato.esBlanco" name="checkSquare" :size="28" />
              <template v-else>
                {{ candidato.nombre.split(' ').map((p) => p[0]).slice(0, 2).join('') }}
              </template>
            </div>
            <div class="cand-nombre">{{ candidato.nombre }}</div>
            <div class="cand-lista">{{ candidato.lista }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
