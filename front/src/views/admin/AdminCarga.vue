<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import { db } from '../../lib/data'
import { toast } from '../../stores/toast'

const form = reactive({ nombres: '', apellidos: '', documento: '', correo: '', facultad: 'Ingeniería' })

const arrastrando = ref(false)
const archivo = ref(null)
const progreso = ref(0)
const resultado = ref(null)
const errorArchivo = ref('')
let intervalo = null

function registrar() {
  if (!form.nombres.trim() || !form.apellidos.trim() || !form.documento.trim() || !form.correo.trim()) {
    toast('Completa los campos obligatorios', 'destructive')
    return
  }

  if (db.usuarios.some((u) => u.documento === form.documento.trim())) {
    toast('Ya existe un usuario con ese documento', 'destructive')
    return
  }

  db.usuarios.push({
    id: Date.now(),
    nombres: form.nombres.trim(),
    apellidos: form.apellidos.trim(),
    documento: form.documento.trim(),
    correo: form.correo.trim(),
    rol: 'VOTANTE',
    estado: 'ACTIVO',
    intentos: 0,
  })

  toast('Votante registrado individualmente')
  Object.assign(form, { nombres: '', apellidos: '', documento: '', correo: '', facultad: 'Ingeniería' })
}

function limpiarIntervalo() {
  if (intervalo) {
    window.clearInterval(intervalo)
    intervalo = null
  }
}

function procesarArchivo(file) {
  if (!file) return
  limpiarIntervalo()
  resultado.value = null
  errorArchivo.value = ''

  const extension = file.name.split('.').pop().toLowerCase()
  const pesoMB = file.size / (1024 * 1024)

  if (!['csv', 'xlsx', 'xls'].includes(extension)) {
    archivo.value = null
    errorArchivo.value = `Formato .${extension} rechazado. Usa CSV o Excel.`
    toast('Formato no permitido. Usa CSV o Excel.', 'destructive')
    return
  }

  if (pesoMB > 10) {
    archivo.value = null
    errorArchivo.value = `El archivo pesa ${pesoMB.toFixed(1)} MB (máximo 10 MB).`
    toast('El archivo supera los 10 MB', 'destructive')
    return
  }

  archivo.value = { nombre: file.name, peso: `${(file.size / 1024).toFixed(0)} KB` }
  progreso.value = 0

  intervalo = window.setInterval(() => {
    progreso.value = Math.min(100, progreso.value + Math.random() * 18 + 6)
    if (progreso.value >= 100) {
      limpiarIntervalo()
      progreso.value = 100
      const validos = 284 + Math.floor(Math.random() * 40)
      const errores = Math.floor(Math.random() * 6)
      resultado.value = { validos, errores }
      toast(`Carga masiva: ${validos} votantes importados`)
    }
  }, 180)
}

function alSoltar(event) {
  event.preventDefault()
  arrastrando.value = false
  procesarArchivo(event.dataTransfer.files?.[0])
}

function alSeleccionar(event) {
  procesarArchivo(event.target.files?.[0])
  event.target.value = ''
}

onBeforeUnmount(limpiarIntervalo)
</script>

<template>
  <div class="grid-2" style="grid-template-columns: 1fr 1.4fr">
    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="userPlus" :size="16" /> Registro individual</div>
        <div class="card-desc">Alta manual de un votante en el padrón</div>
      </div>
      <div class="card-body">
        <div class="field-row">
          <div class="field">
            <label>Nombres *</label>
            <input v-model="form.nombres" class="input" placeholder="Ana" />
          </div>
          <div class="field">
            <label>Apellidos *</label>
            <input v-model="form.apellidos" class="input" placeholder="Torres" />
          </div>
        </div>

        <div class="field">
          <label>Documento *</label>
          <input v-model="form.documento" class="input" placeholder="1055987412" />
        </div>

        <div class="field">
          <label>Correo *</label>
          <input v-model="form.correo" class="input" placeholder="ana.torres@uni.edu.co" />
        </div>

        <div class="field">
          <label>Facultad</label>
          <select v-model="form.facultad" class="select">
            <option>Ingeniería</option>
            <option>Ciencias de la Salud</option>
            <option>Humanidades</option>
            <option>Ciencias Económicas</option>
          </select>
        </div>

        <button class="btn btn-primary btn-block" @click="registrar">
          <AppIcon name="check" :size="16" /> Registrar votante
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="upload" :size="16" /> Carga masiva (CSV / Excel)</div>
        <div class="card-desc">Importa hasta 5.000 votantes por archivo · Formatos .csv, .xlsx · máx. 10 MB</div>
      </div>
      <div class="card-body">
        <div
          class="dropzone"
          :class="{ dragover: arrastrando }"
          @click="$refs.fileInput.click()"
          @dragenter.prevent="arrastrando = true"
          @dragover.prevent="arrastrando = true"
          @dragleave.prevent="arrastrando = false"
          @drop="alSoltar"
        >
          <div class="dz-icon"><AppIcon name="upload" :size="22" /></div>
          <div class="dz-title">Arrastra tu archivo aquí</div>
          <div class="dz-hint">o haz clic para seleccionar · peso máximo 10 MB</div>
          <input ref="fileInput" type="file" accept=".csv,.xlsx,.xls" hidden @change="alSeleccionar" />
        </div>

        <div v-if="errorArchivo" class="alert alert-destructive" style="margin-top: 12px">
          <AppIcon name="alert" :size="15" /> {{ errorArchivo }}
        </div>

        <div v-if="archivo" class="file-item" style="margin-top: 12px">
          <div class="fi-icon"><AppIcon name="fileText" :size="17" /></div>
          <div style="flex: 1; min-width: 0">
            <div class="fi-name">{{ archivo.nombre }}</div>
            <div class="fi-meta">{{ archivo.peso }} · válido</div>
          </div>
          <span class="badge badge-success"><AppIcon name="check" :size="12" /> Aceptado</span>
        </div>

        <div v-if="archivo" class="progress" style="margin-top: 10px">
          <div class="progress-bar" :style="{ width: `${progreso}%` }" />
        </div>

        <div v-if="resultado" class="alert alert-success" style="margin-top: 14px">
          <span style="flex-shrink: 0; margin-top: 1px"><AppIcon name="check" :size="17" /></span>
          <div>
            <div class="alert-title">Importación completada</div>
            <div class="alert-body">
              {{ resultado.validos }} registros importados al padrón
              <template v-if="resultado.errores">
                · {{ resultado.errores }} filas con error (correo duplicado o documento inválido)
              </template>
              .
            </div>
          </div>
        </div>

        <button v-if="resultado?.errores" class="btn btn-outline btn-sm" style="margin-top: 10px">
          <AppIcon name="download" :size="14" /> Descargar reporte de errores
        </button>

        <div class="alert alert-info" style="margin-top: 18px">
          <span style="flex-shrink: 0; margin-top: 1px"><AppIcon name="info" :size="17" /></span>
          <div>
            <div class="alert-title">Columnas esperadas</div>
            <div class="alert-body font-mono" style="font-size: 11.5px">
              documento, nombres, apellidos, correo, facultad, jornada
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
