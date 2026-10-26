<script setup>
import { computed } from 'vue'

const props = defineProps({
  seed: { type: String, default: 'demo' },
  size: { type: [Number, String], default: 130 },
})

const svg = computed(() => {
  const size = Number(props.size)
  let h = 0
  for (const c of props.seed) h = (h * 31 + c.charCodeAt(0)) >>> 0
  const rnd = () => {
    h = (h * 1103515245 + 12345) >>> 0
    return h / 4294967296
  }
  const n = 21
  const cell = size / n
  let rects = ''
  for (let y = 0; y < n; y++) {
    for (let x = 0; x < n; x++) {
      const esquina = (x < 7 && y < 7) || (x > n - 8 && y < 7) || (x < 7 && y > n - 8)
      if (esquina) continue
      if (rnd() > 0.52) rects += `<rect x="${x * cell}" y="${y * cell}" width="${cell}" height="${cell}"/>`
    }
  }
  const finder = (fx, fy) =>
    `<rect x="${fx * cell}" y="${fy * cell}" width="${7 * cell}" height="${7 * cell}" fill="none" stroke="currentColor" stroke-width="${cell}"/>`

  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" fill="currentColor">
    <rect width="${size}" height="${size}" fill="#fff"/>${rects}${finder(0, 0)}${finder(n - 7, 0)}${finder(0, n - 7)}</svg>`
})
</script>

<template>
  <span class="qr-code" v-html="svg" />
</template>
