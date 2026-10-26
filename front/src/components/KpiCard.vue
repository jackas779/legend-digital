<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  label: { type: String, default: '' },
  valor: { type: [String, Number], default: '' },
  icon: { type: String, default: 'activity' },
})
</script>

<template>
  <div class="card kpi">
    <div class="kpi-label">
      <AppIcon :name="icon" :size="16" />
      {{ label }}
    </div>
    <div class="kpi-value"><slot name="value">{{ valor }}</slot></div>
    <div v-if="$slots.trend" class="kpi-trend neutral"><slot name="trend" /></div>
  </div>
</template>
