<script setup>
import { computed } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import BarList from '../../components/BarList.vue'
import { db, fmtFecha, fmtNum, state } from '../../lib/data'
import { toast } from '../../stores/toast'

const categoria = computed(() => db.categorias[0])
const finalizada = computed(() => state.estadoEleccion === 'FINALIZADA')

const items = computed(() =>
  categoria.value.candidatos.map((candidato, index) => ({
    nombre: candidato.nombre,
    valor: categoria.value.resultados[index] || 0,
    cls: candidato.esBlanco ? 'blanco' : '',
  })),
)

function finalizar() {
  if (!window.confirm('¿Finalizar la elección? La urna se sellará y se generará el Acta de Escrutinio. Esta acción no se puede deshacer.')) {
    return
  }

  state.estadoEleccion = 'FINALIZADA'
  categoria.value.estado = 'FINALIZADA'
  toast('Elección finalizada · Acta generada')
}

function descargarActa() {
  toast('Generando Acta de Escrutinio en PDF…', 'info')
}
</script>

<template>
  <div class="grid-2" style="grid-template-columns: 1.4fr 1fr">
    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="award" :size="16" /> Acta de Escrutinio</div>
        <div class="card-desc">{{ categoria.titulo }} · cierre {{ fmtFecha(categoria.cierre) }}</div>
      </div>
      <div class="card-body">
        <div class="equacion">
          <span class="eq-num">{{ fmtNum(categoria.padron) }}</span><span class="eq-sign">padrón</span>
          <span class="eq-sign">=</span>
          <span class="eq-num">{{ fmtNum(categoria.participantes) }}</span><span class="eq-sign">votos</span>
          <span class="eq-sign">+</span>
          <span class="eq-num">{{ fmtNum(categoria.padron - categoria.participantes) }}</span>
          <span class="eq-sign">abstenciones</span>
          <span class="eq-ok"><AppIcon name="check" :size="18" /></span>
        </div>

        <div class="mt-20">
          <BarList :items="items" />
        </div>

        <div class="hash-box mt-20">
          hash_sello_bd: 7f3a9c1e5b8d2f604a7c3e9b1d5f8a2c604b7e9d1f3a5c8b2e6d9f1a4c7b3e8d205
        </div>
      </div>
      <div class="card-footer">
        <button class="btn btn-outline" :disabled="!finalizada" @click="descargarActa">
          <AppIcon name="download" :size="15" /> Descargar Acta (PDF)
        </button>
        <button class="btn btn-primary" :disabled="finalizada" @click="finalizar">
          <AppIcon name="award" :size="15" /> Finalizar elección
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title"><AppIcon name="alert" :size="16" /> Antes de cerrar</div>
      </div>
      <div class="card-body">
        <div
          v-for="texto in [
            'La urna queda sellada: no se aceptan más votos.',
            'Se genera el Acta de Escrutinio con hash de sellado.',
            'Los votantes podrán descargar sus certificados.',
            'Los resultados pasan a ser públicos.',
          ]"
          :key="texto"
          class="check-row"
        >
          <span style="color: hsl(var(--primary))"><AppIcon name="check" :size="15" /></span>{{ texto }}
        </div>

        <div class="alert alert-warning" style="margin-top: 16px">
          <span style="flex-shrink: 0; margin-top: 1px"><AppIcon name="alert" :size="17" /></span>
          <div>
            <div class="alert-title">Acción irreversible</div>
            <div class="alert-body">
              Una vez finalizada la elección no podrás modificar candidatos ni normativas.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.check-row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid hsl(var(--border));
  font-size: 13.5px;
}
</style>
