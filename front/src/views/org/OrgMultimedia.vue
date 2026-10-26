<script setup>
import { computed, ref } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import AppModal from '../../components/AppModal.vue'
import BloqueoBanner from '../../components/BloqueoBanner.vue'
import { db, state } from '../../lib/data'
import { toast } from '../../stores/toast'

const editable = computed(() => ['BORRADOR', 'PROGRAMADA'].includes(state.estadoEleccion))

const arrastrando = ref(false)
const modalRecorte = ref(false)
const archivoPendiente = ref(null)

function alSoltar(event) {
  event.preventDefault()
  arrastrando.value = false
  const file = event.dataTransfer.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    toast('Solo se permiten imágenes', 'destructive')
    return
  }
  if (file.size > 5 * 1048576) {
    toast('La imagen supera los 5 MB', 'destructive')
    return
  }

  archivoPendiente.value = file
  modalRecorte.value = true
}

function aplicarRecorte() {
  if (!archivoPendiente.value) return
  db.multimedia.push({
    id: Date.now(),
    nombre: archivoPendiente.value.name,
    tipo: archivoPendiente.value.type,
    peso: `${(archivoPendiente.value.size / 1024).toFixed(0)} KB`,
    etiqueta: 'Nuevo',
  })
  modalRecorte.value = false
  archivoPendiente.value = null
  toast('Imagen recortada y estandarizada')
}
</script>

<template>
  <BloqueoBanner />

  <div class="grid-2" style="grid-template-columns: 1fr 1.6fr">
    <div>
      <div class="card">
        <div class="card-header">
          <div class="card-title"><AppIcon name="image" :size="16" /> Subir recurso</div>
          <div class="card-desc">JPG, PNG o WebP · máx. 5 MB</div>
        </div>
        <div class="card-body">
          <div
            class="dropzone"
            :class="{ dragover: arrastrando }"
            @dragenter.prevent="arrastrando = true"
            @dragover.prevent="arrastrando = true"
            @dragleave.prevent="arrastrando = false"
            @drop="alSoltar"
          >
            <div class="dz-icon"><AppIcon name="image" :size="22" /></div>
            <div class="dz-title">Arrastra una imagen</div>
            <div class="dz-hint">se estandarizará a 400×400 px</div>
          </div>
          <button class="btn btn-primary btn-block" style="margin-top: 14px" :disabled="!editable" @click="modalRecorte = true">
            <AppIcon name="crop" :size="15" /> Recortar y estandarizar
          </button>
        </div>
      </div>

      <div class="card mt-20">
        <div class="card-header">
          <div class="card-title"><AppIcon name="info" :size="16" /> Estandarización</div>
        </div>
        <div class="card-body text-sm text-muted">
          Las fotos de candidatos se recortan a <b>cuadrado 1:1</b> y se comprimen a máx. 300 KB para
          que el tarjetón sea visualmente neutro.
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="layout" :size="16" /> Biblioteca ({{ db.multimedia.length }})</div>
        <div class="card-desc">Recursos disponibles para las categorías</div>
      </div>
      <div class="card-body">
        <div class="grid-3 galeria">
          <div v-for="recurso in db.multimedia" :key="recurso.id" class="card" style="box-shadow: none">
            <div class="media-placeholder"><AppIcon name="image" :size="28" /></div>
            <div style="padding: 11px 13px">
              <div class="media-name">{{ recurso.nombre }}</div>
              <div class="text-sm text-muted">{{ recurso.etiqueta }} · {{ recurso.peso }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <AppModal
    v-model="modalRecorte"
    titulo="Recortar imagen"
    :desc="`Encuadre estandarizado 1:1 para <b>${archivoPendiente?.name || 'la imagen'}</b>. Ajusta el zoom antes de aplicar.`"
    icono="crop"
    :ancho="520"
  >
    <div class="crop-stage"><div class="crop-frame" /></div>
    <div class="flex items-center gap-14" style="margin-top: 16px">
      <span class="text-sm text-muted fw-600">Zoom</span>
      <input type="range" min="1" max="3" step="0.1" value="1.4" style="flex: 1; accent-color: hsl(var(--primary))" />
      <span class="badge badge-muted">400 × 400</span>
    </div>

    <template #footer>
      <button class="btn btn-secondary" @click="modalRecorte = false">Cancelar</button>
      <button class="btn btn-primary" @click="aplicarRecorte">
        <AppIcon name="check" :size="16" /> Aplicar recorte
      </button>
    </template>
  </AppModal>
</template>

<style scoped>
.media-placeholder {
  aspect-ratio: 1;
  background: linear-gradient(135deg, hsl(243 60% 45%), hsl(271 60% 35%));
  border-radius: var(--radius) var(--radius) 0 0;
  display: grid;
  place-items: center;
  color: #fff;
}

.media-name {
  font-weight: 600;
  font-size: 12.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
