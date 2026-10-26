<script setup>
import { onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import AppIcon from '../../components/AppIcon.vue'
import { state } from '../../lib/data'
import { toast } from '../../stores/toast'

const router = useRouter()

onMounted(() => {
  if (!state.votoEmitido) router.replace('/votante/tarjeton')
})

function copiarHash() {
  if (!state.hashVoto) return
  navigator.clipboard?.writeText(state.hashVoto).catch(() => {})
  toast('Hash copiado al portapapeles')
}
</script>

<template>
  <div style="max-width: 560px; margin: 24px auto 0">
    <div class="card" style="text-align: center; padding: 36px 30px">
      <div class="success-circle"><AppIcon name="check" :size="38" /></div>
      <div style="font-size: 23px; font-weight: 800; letter-spacing: -0.02em">Tu voto fue registrado</div>
      <div class="text-muted" style="margin-top: 8px; line-height: 1.6">
        Guarda este comprobante. Certifica que participaste en
        <b>Elecciones Estudiantiles 2026</b>.<br />No contiene información sobre tu elección.
      </div>

      <div style="text-align: left; margin-top: 26px">
        <div class="text-sm text-muted fw-600" style="margin-bottom: 7px">HASH SHA-256 DEL COMPROBANTE</div>
        <div class="hash-box">{{ state.hashVoto }}</div>
      </div>

      <div class="flex gap-10" style="margin-top: 22px">
        <button class="btn btn-outline" style="flex: 1" @click="copiarHash">
          <AppIcon name="copy" :size="16" /> Copiar hash
        </button>
        <button class="btn btn-primary" style="flex: 1" @click="toast('Generando comprobante en PDF…', 'info')">
          <AppIcon name="download" :size="16" /> Descargar comprobante
        </button>
      </div>

      <div class="flex gap-10" style="margin-top: 12px">
        <RouterLink class="btn btn-ghost btn-block" to="/votante/certificados">
          Ver mis certificados →
        </RouterLink>
      </div>
    </div>

    <div class="alert alert-success" style="margin-top: 16px">
      <span style="flex-shrink: 0; margin-top: 1px"><AppIcon name="shield" :size="17" /></span>
      <div>
        <div class="alert-title">Anonimato garantizado</div>
        <div class="alert-body">
          La urna digital almacena tu voto sin ninguna referencia a tu identidad. El hash solo prueba
          tu participación.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.success-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: hsl(var(--success) / 0.12);
  color: hsl(var(--success));
  display: grid;
  place-items: center;
  margin: 0 auto 18px;
}
</style>
