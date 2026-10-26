<script setup>
import { computed } from 'vue'
import { Icons } from '../lib/icons'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
})

const svg = computed(() => {
  const fn = Icons[props.name]
  return typeof fn === 'function' && props.name !== '_wrap' ? fn(Number(props.size)) : ''
})
</script>

<template>
  <span class="app-icon" v-html="svg" />
</template>

<style scoped>
.app-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 0;
}
</style>
