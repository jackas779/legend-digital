<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  modelValue: { type: Boolean, default: false },
  titulo: { type: String, default: '' },
  desc: { type: String, default: '' },
  icono: { type: String, default: 'info' },
  tono: { type: String, default: 'primary' },
  ancho: { type: [Number, String], default: 470 },
})

const emit = defineEmits(['update:modelValue'])

function cerrar() {
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-overlay" @click.self="cerrar">
      <div class="modal" :style="{ maxWidth: `${ancho}px` }" role="dialog" aria-modal="true">
        <div class="modal-header">
          <div class="mh-icon" :class="tono">
            <AppIcon :name="icono" :size="20" />
          </div>
          <div style="flex: 1">
            <div class="modal-title">{{ titulo }}</div>
            <div v-if="desc" class="modal-desc" v-html="desc" />
          </div>
          <button class="icon-btn" style="width: 30px; height: 30px" title="Cerrar" @click="cerrar">
            <AppIcon name="x" :size="14" />
          </button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
        <div class="modal-footer">
          <slot name="footer">
            <button class="btn btn-secondary" @click="cerrar">Cerrar</button>
          </slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>
