<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { CUENTAS_DEMO } from '../lib/data'
import { useSessionStore } from '../stores/session'
import { toast } from '../stores/toast'

const router = useRouter()
const session = useSessionStore()

const identificador = ref('')
const password = ref('')
const error = ref('')

onMounted(() => {
  if (session.user) router.replace(session.home)
})

async function ingresar() {
  error.value = ''

  if (!identificador.value.trim() || !password.value) {
    error.value = 'Escribe tu correo/usuario y tu contraseña.'
    return
  }

  const ok = await session.loginReal(identificador.value, password.value)
  if (!ok) {
    error.value = session.error || 'No se pudo iniciar sesión.'
    return
  }

  toast(`Bienvenido, ${session.user.nombre}`, 'success')
  router.push(session.home)
}

function entrarDemo(rol) {
  if (!session.loginDemo(rol)) return
  toast(`Sesión demo iniciada como ${rol}`, 'info')
  router.push(session.home)
}
</script>

<template>
  <div class="login-page">
    <div class="login-left">
      <div class="ll-badge"><AppIcon name="shield" :size="14" /> Sistema de Votación Seguro</div>
      <h2>Elecciones<br />transparentes y<br />auditables.</h2>
      <p>
        Plataforma de votación electrónica con trazabilidad criptográfica, anonimato del voto y
        verificación matemática en tiempo real para toda la comunidad universitaria.
      </p>

      <div class="login-features">
        <div class="login-feature">
          <div class="lf-icon"><AppIcon name="lock" :size="18" /></div>
          <div>
            <div class="lf-title">Voto 100% anónimo</div>
            <div class="lf-desc">La urna almacena el voto sin vincular identidad. Comprobante con Hash SHA-256.</div>
          </div>
        </div>
        <div class="login-feature">
          <div class="lf-icon"><AppIcon name="scroll" :size="18" /></div>
          <div>
            <div class="lf-title">Auditoría inalterable</div>
            <div class="lf-desc">Registro de eventos con hash de trazabilidad y ecuación de consistencia.</div>
          </div>
        </div>
        <div class="login-feature">
          <div class="lf-icon"><AppIcon name="chart" :size="18" /></div>
          <div>
            <div class="lf-title">Resultados en tiempo real</div>
            <div class="lf-desc">Dashboards dinámicos según las reglas de visibilidad de cada categoría.</div>
          </div>
        </div>
      </div>

      <div class="ll-footer">Prototipo UX/UI · Universidad 2026</div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 22px">
          <div class="sidebar-brand" style="border: none; padding: 0">
            <div class="brand-icon"><AppIcon name="vote" :size="20" /></div>
            <div>
              <h1>Votación Segura</h1>
              <span>Panel del sistema</span>
            </div>
          </div>
        </div>

        <h3>Iniciar sesión</h3>
        <p class="lc-sub">Ingresa con tu correo o usuario institucional</p>

        <div v-if="error" class="alert alert-destructive">
          <span style="flex-shrink: 0; margin-top: 1px"><AppIcon name="alert" :size="17" /></span>
          <div>
            <div class="alert-title">No se pudo ingresar</div>
            <div class="alert-body">{{ error }}</div>
          </div>
        </div>

        <form @submit.prevent="ingresar">
          <div class="field">
            <label>Correo o usuario</label>
            <input
              v-model="identificador"
              class="input"
              placeholder="admin o admin@ejemplo.com"
              autocomplete="username"
            />
          </div>
          <div class="field">
            <label>Contraseña</label>
            <input
              v-model="password"
              class="input"
              type="password"
              placeholder="••••••••"
              autocomplete="current-password"
            />
          </div>
          <button class="btn btn-primary btn-lg btn-block" type="submit" :disabled="session.loading">
            <span v-if="session.loading" class="spinner" />
            <AppIcon v-else name="key" :size="17" />
            {{ session.loading ? 'Ingresando…' : 'Ingresar' }}
          </button>
        </form>

        <div class="demo-users">
          <div class="du-title">Entrar como demo (por rol)</div>
          <button
            v-for="cuenta in CUENTAS_DEMO"
            :key="cuenta.rol"
            class="demo-user"
            type="button"
            @click="entrarDemo(cuenta.rol)"
          >
            <UserAvatar :nombre="cuenta.nombre" :size="34" />
            <div style="flex: 1; min-width: 0; text-align: left">
              <div style="font-size: 13px; font-weight: 700">{{ cuenta.nombre }}</div>
              <div style="font-size: 11.5px; color: hsl(var(--muted-foreground))">{{ cuenta.rol }}</div>
            </div>
            <AppIcon name="chevronRight" :size="15" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
