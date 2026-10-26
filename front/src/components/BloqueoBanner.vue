<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'
import { ESTADOS, state } from '../lib/data'

const editable = computed(() => ['BORRADOR', 'PROGRAMADA'].includes(state.estadoEleccion))
</script>

<template>
  <div v-if="!editable" class="locked-banner">
    <span style="flex-shrink: 0"><AppIcon name="lock" :size="16" /></span>
    <span>
      La elección está en estado <b>{{ ESTADOS[state.estadoEleccion].label.toUpperCase() }}</b>: los
      formularios de configuración están bloqueados (solo lectura). Vuelve a <b>Borrador</b> o
      <b>Programada</b> con el simulador del panel superior para editar.
    </span>
  </div>
</template>
