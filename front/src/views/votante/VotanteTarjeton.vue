<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../../components/AppIcon.vue'
import AppModal from '../../components/AppModal.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import { db, sha256Mock, state } from '../../lib/data'
import { toast } from '../../stores/toast'

const router = useRouter()
const categoria = computed(() => db.categorias[0])
const seleccion = ref(null)
const modalAbierto = ref(false)
const procesando = ref(false)

onMounted(() => {
  if (state.votoEmitido) router.replace('/votante/comprobante')
})

function seleccionar(candidato) {
  seleccion.value = candidato
}

function abrirConfirmacion() {
  if (!seleccion.value) return
  modalAbierto.value = true
}

function confirmarVoto() {
  if (!seleccion.value || procesando.value) return
  procesando.value = true

  window.setTimeout(() => {
    state.hashVoto = sha256Mock()
    state.votoEmitido = true

    const index = categoria.value.candidatos.findIndex((c) => c.id === seleccion.value.id)
    if (index >= 0) categoria.value.resultados[index] += 1
    categoria.value.participantes += 1

    procesando.value = false
    modalAbierto.value = false
    toast('Voto registrado correctamente')
    router.push('/votante/comprobante')
  }, 2200)
}
</script>

<template>
  <div class="flex items-center justify-between mb-20" style="flex-wrap: wrap; gap: 12px">
    <div>
      <div class="section-title">{{ categoria.titulo }}</div>
      <div class="section-sub" style="margin-bottom: 0">
        Selecciona una casilla. Podrás revisar tu elección antes de confirmar.
      </div>
    </div>
    <EstadoBadge :estado="state.estadoEleccion" />
  </div>

  <div class="tarjeton-grid">
    <div
      v-for="(candidato, index) in categoria.candidatos"
      :key="candidato.id"
      class="tarjeton-option"
      :class="{ blanco: candidato.esBlanco, selected: seleccion?.id === candidato.id }"
      @click="seleccionar(candidato)"
    >
      <div class="check"><AppIcon name="check" :size="14" /></div>
      <div
        class="foto"
        :style="
          candidato.esBlanco
            ? ''
            : { background: `linear-gradient(135deg, hsl(${243 + index * 8} 70% 60%), hsl(${271 + index * 6} 70% 55%))` }
        "
      >
        <AppIcon v-if="candidato.esBlanco" name="checkSquare" :size="30" />
        <template v-else>
          {{ candidato.nombre.split(' ').map((p) => p[0]).slice(0, 2).join('') }}
        </template>
      </div>
      <div class="cand-nombre">{{ candidato.nombre }}</div>
      <div class="cand-lista">{{ candidato.lista }}</div>
    </div>
  </div>

  <div class="sticky-vote-bar">
    <div style="flex: 1; min-width: 0">
      <div class="text-sm text-muted">Tu selección</div>
      <div class="fw-600" style="font-size: 14.5px">
        {{ seleccion ? `${seleccion.nombre} · ${seleccion.lista}` : 'Ninguna — selecciona una casilla' }}
      </div>
    </div>
    <button class="btn btn-primary btn-lg" :disabled="!seleccion" @click="abrirConfirmacion">
      <AppIcon name="vote" :size="17" /> Emitir voto
    </button>
  </div>

  <AppModal
    v-model="modalAbierto"
    titulo="¿Confirma su voto?"
    :desc="`Está a punto de votar por <b>${seleccion?.nombre || ''}</b> (${seleccion?.lista || ''}).<br><br><b>Esta acción no se puede deshacer.</b> Su voto es anónimo y no podrá modificarse ni consultarse por quién votó.`"
    icono="alert"
    tono="destructive"
  >
    <div class="confirm-selected">
      <div class="confirm-check"><AppIcon name="check" :size="13" /></div>
      <div>
        <div class="fw-600" style="font-size: 13.5px">{{ seleccion?.nombre }}</div>
        <div class="text-sm text-muted">{{ seleccion?.lista }}</div>
      </div>
    </div>

    <template #footer>
      <button class="btn btn-secondary" :disabled="procesando" @click="modalAbierto = false">Revisar</button>
      <button class="btn btn-primary btn-lg" :disabled="procesando" @click="confirmarVoto">
        <span v-if="procesando" class="spinner" />
        <AppIcon v-else name="check" :size="17" />
        {{ procesando ? 'Procesando voto…' : 'Sí, emitir mi voto' }}
      </button>
    </template>
  </AppModal>
</template>

<style scoped>
.confirm-selected {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: hsl(var(--muted) / 0.5);
  border: 1px solid hsl(var(--border));
  border-radius: 10px;
}

.confirm-check {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: hsl(var(--primary));
  color: #fff;
  display: grid;
  place-items: center;
}
</style>
