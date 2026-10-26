<script setup>
import { computed, ref } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import BloqueoBanner from '../../components/BloqueoBanner.vue'
import { db, fmtFecha, state } from '../../lib/data'
import { toast } from '../../stores/toast'

const editable = computed(() => ['BORRADOR', 'PROGRAMADA'].includes(state.estadoEleccion))

const titulo = ref('Reglamento Electoral Estudiantil 2026')
const contenido = ref(`## Artículo 1. Del sufragio
Todo estudiante activo podrá emitir su voto de forma secreta...

## Artículo 2. Del tarjetón
El tarjetón incluirá la opción "Voto en Blanco" como última casilla.`)

const arrastrando = ref(false)

function publicar() {
  if (!titulo.value.trim()) {
    toast('Escribe un título para la normativa', 'destructive')
    return
  }

  db.normativas.push({
    id: Date.now(),
    categoriaId: 1,
    titulo: titulo.value.trim(),
    pdf: 'normativa-publicada.pdf',
    peso: '—',
    fecha: new Date().toISOString().slice(0, 10),
  })

  toast('Normativa publicada')
}

function eliminar(normativa) {
  if (!window.confirm(`¿Eliminar "${normativa.titulo}"?`)) return
  const index = db.normativas.findIndex((n) => n.id === normativa.id)
  if (index >= 0) db.normativas.splice(index, 1)
  toast('Normativa eliminada')
}

function alSoltar(event) {
  event.preventDefault()
  arrastrando.value = false
  const file = event.dataTransfer.files?.[0]
  if (!file) return

  const extension = file.name.split('.').pop().toLowerCase()
  if (!['pdf', 'docx'].includes(extension)) {
    toast('Solo se permiten archivos PDF o DOCX', 'destructive')
    return
  }
  if (file.size > 10 * 1048576) {
    toast('El archivo supera los 10 MB', 'destructive')
    return
  }
  toast(`"${file.name}" validado correctamente`)
}
</script>

<template>
  <BloqueoBanner />

  <div class="grid-2" style="grid-template-columns: 1.3fr 1fr">
    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="fileText" :size="16" /> Editor de normativa</div>
        <div class="card-desc">Redacta en HTML/Markdown. Se publica tal cual a los votantes.</div>
      </div>
      <div class="card-body">
        <div class="field">
          <label>Título</label>
          <input v-model="titulo" class="input" :disabled="!editable" />
        </div>

        <div class="tabs" style="margin-bottom: 12px">
          <button class="tab active">Redactar</button>
          <button class="tab">Vista previa</button>
        </div>

        <div class="field">
          <textarea v-model="contenido" class="textarea" style="min-height: 190px" :disabled="!editable" />
        </div>

        <button class="btn btn-primary" :disabled="!editable" @click="publicar">
          <AppIcon name="check" :size="16" /> Publicar normativa
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="upload" :size="16" /> Documentos PDF</div>
        <div class="card-desc">Archivos adjuntos · válidos PDF/DOCX · máx. 10 MB</div>
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
          <div class="dz-icon"><AppIcon name="upload" :size="22" /></div>
          <div class="dz-title">Arrastra el PDF aquí</div>
          <div class="dz-hint">pdf o docx · hasta 10 MB</div>
        </div>

        <div style="margin-top: 16px">
          <div v-for="normativa in db.normativas" :key="normativa.id" class="file-item" style="margin-bottom: 10px">
            <div class="fi-icon pdf-icon">PDF</div>
            <div style="flex: 1; min-width: 0">
              <div class="fi-name">{{ normativa.titulo }}</div>
              <div class="fi-meta">{{ normativa.pdf }} · {{ normativa.peso }} · {{ fmtFecha(normativa.fecha) }}</div>
            </div>
            <button class="btn btn-ghost btn-sm btn-icon" title="Descargar">
              <AppIcon name="download" :size="15" />
            </button>
            <button
              class="btn btn-ghost btn-sm btn-icon"
              style="color: hsl(var(--destructive))"
              title="Eliminar"
              :disabled="!editable"
              @click="eliminar(normativa)"
            >
              <AppIcon name="trash" :size="15" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pdf-icon {
  background: hsl(var(--destructive) / 0.12);
  color: hsl(var(--destructive));
  font-size: 10px;
  font-weight: 800;
}
</style>
