<script setup>
import AppIcon from '../../components/AppIcon.vue'
import QrCode from '../../components/QrCode.vue'
import { db, fmtFecha, state } from '../../lib/data'
import { toast } from '../../stores/toast'
</script>

<template>
  <div class="section-title">Historial de participación</div>
  <div class="section-sub">Descarga tu certificado en PDF con código QR verificable</div>

  <div class="grid-auto">
    <div v-for="certificado in db.certificados" :key="certificado.id" class="card">
      <div class="card-body">
        <div class="flex items-center justify-between mb-16">
          <span class="badge badge-success"><AppIcon name="award" :size="12" /> Certificado válido</span>
          <span class="text-sm text-muted">{{ fmtFecha(certificado.fecha) }}</span>
        </div>

        <div class="fw-600" style="font-size: 15px">{{ certificado.titulo }}</div>
        <div class="text-sm text-muted" style="margin: 4px 0 16px">
          Código: <span class="font-mono">{{ certificado.codigo }}</span>
        </div>

        <div class="qr-box"><QrCode :seed="certificado.codigo" :size="130" /></div>
        <div class="text-sm text-muted" style="text-align: center; margin-top: 8px">
          Escanea para verificar autenticidad
        </div>

        <button class="btn btn-primary btn-block" style="margin-top: 16px" @click="toast('Generando certificado en PDF…', 'info')">
          <AppIcon name="download" :size="15" /> Descargar PDF
        </button>
      </div>
    </div>

    <div v-if="state.votoEmitido" class="card">
      <div class="card-body">
        <div class="flex items-center justify-between mb-16">
          <span class="badge badge-success"><AppIcon name="award" :size="12" /> Disponible</span>
          <span class="text-sm text-muted">hoy</span>
        </div>

        <div class="fw-600" style="font-size: 15px">Elecciones Estudiantiles 2026</div>
        <div class="text-sm text-muted" style="margin: 4px 0 16px">
          Código: <span class="font-mono">CERT-2026-7D21E9</span>
        </div>

        <div class="qr-box"><QrCode :seed="state.hashVoto || 'x'" :size="130" /></div>
        <div class="text-sm text-muted" style="text-align: center; margin-top: 8px">
          Escanea para verificar autenticidad
        </div>

        <button class="btn btn-primary btn-block" style="margin-top: 16px" @click="toast('Generando certificado en PDF…', 'info')">
          <AppIcon name="download" :size="15" /> Descargar PDF
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.qr-box {
  display: flex;
  justify-content: center;
  padding: 14px;
  background: #fff;
  border-radius: 12px;
  color: #000;
}
</style>
