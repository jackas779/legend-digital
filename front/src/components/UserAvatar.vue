<script setup>
import { computed } from 'vue'
import { avatarColor, iniciales } from '../lib/data'

const props = defineProps({
  nombre: { type: String, default: '' },
  size: { type: [Number, String], default: 36 },
})

const initials = computed(() => iniciales(props.nombre))
const color = computed(() => avatarColor(props.nombre))
</script>

<template>
  <span
    class="avatar"
    :style="{ width: `${size}px`, height: `${size}px`, background: color, fontSize: `${Math.max(10, Number(size) * 0.36)}px` }"
  >
    {{ initials }}
  </span>
</template>
