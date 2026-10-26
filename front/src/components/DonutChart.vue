<script setup>
import { computed } from 'vue'

const props = defineProps({
  participantes: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  label: { type: String, default: 'participación' },
})

const radius = 58
const circumference = 2 * Math.PI * radius
const pct = computed(() => (props.total ? Math.round((props.participantes / props.total) * 100) : 0))
const offset = computed(() => circumference - (circumference * pct.value) / 100)
</script>

<template>
  <div class="donut-wrap">
    <div class="donut">
      <svg width="150" height="150">
        <circle cx="75" cy="75" :r="radius" fill="none" stroke="hsl(var(--muted))" stroke-width="14" />
        <circle
          cx="75"
          cy="75"
          :r="radius"
          fill="none"
          stroke="hsl(var(--primary))"
          stroke-width="14"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="offset"
          style="transition: stroke-dashoffset 1s"
        />
      </svg>
      <div class="donut-center">
        <div>
          <div class="pct">{{ pct }}%</div>
          <div class="lbl">{{ label }}</div>
        </div>
      </div>
    </div>
    <slot />
  </div>
</template>
