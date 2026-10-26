<script setup>
import { toasts } from '../stores/toast'
import AppIcon from './AppIcon.vue'

const iconos = { success: 'check', destructive: 'alert', warning: 'alert', info: 'info' }
</script>

<template>
  <div class="toast-container">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type">
      <span class="t-icon"><AppIcon :name="iconos[t.type] || 'info'" :size="18" /></span>
      <span>{{ t.message }}</span>
    </div>
  </div>
</template>
