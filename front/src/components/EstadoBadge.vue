<script setup>
import { computed } from 'vue'
import { ESTADOS, ESTADO_USUARIO } from '../lib/data'

const props = defineProps({
  estado: { type: String, default: '' },
  tipo: { type: String, default: 'categoria' },
})

const info = computed(() => {
  const tabla = props.tipo === 'usuario' ? ESTADO_USUARIO : ESTADOS
  return tabla[props.estado] || Object.values(tabla)[0]
})
</script>

<template>
  <span class="badge" :class="info.cls">{{ info.label }}</span>
</template>
