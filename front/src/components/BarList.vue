<script setup>
import { computed } from 'vue'
import { fmtNum } from '../lib/data'

const props = defineProps({
  items: { type: Array, default: () => [] },
})

const max = computed(() => Math.max(...props.items.map((i) => Number(i.valor) || 0), 1))
</script>

<template>
  <div>
    <div v-for="item in items" :key="item.nombre" class="bar-row">
      <div class="bar-label" :title="item.nombre">{{ item.nombre }}</div>
      <div class="bar-track">
        <div class="bar-fill" :class="item.cls" :style="{ width: `${(item.valor / max) * 100}%` }" />
      </div>
      <div class="bar-val">{{ fmtNum(item.valor) }}</div>
    </div>
  </div>
</template>
