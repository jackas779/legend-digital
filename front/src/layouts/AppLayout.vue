<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { ESTADOS, MENUS, state } from '../lib/data'
import { useSessionStore } from '../stores/session'
import { toast } from '../stores/toast'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const sidebarOpen = ref(false)
const isDark = ref(false)

const menu = computed(() => MENUS[session.role] || [])
const titulo = computed(() => route.meta.title || 'Panel')
const sub = computed(() => route.meta.sub || '')

onMounted(() => {
  try {
    isDark.value = localStorage.getItem('vs-tema') === 'dark'
  } catch {
    isDark.value = false
  }
  document.documentElement.classList.toggle('dark', isDark.value)
})

function toggleTema() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  try {
    localStorage.setItem('vs-tema', isDark.value ? 'dark' : 'light')
  } catch {
    /* noop */
  }
}

function cambiarEstado(event) {
  state.estadoEleccion = event.target.value
  toast(`Elección en estado: ${ESTADOS[state.estadoEleccion].label}`, 'info')
}

function cerrarSesion() {
  session.logout()
  state.seleccionVoto = null
  state.votoEmitido = false
  state.hashVoto = null
  router.push('/login')
}
</script>

<template>
  <div class="sidebar-overlay" :class="{ show: sidebarOpen }" @click="sidebarOpen = false" />

  <div class="layout">
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-brand">
        <div class="brand-icon"><AppIcon name="vote" :size="19" /></div>
        <div>
          <h1>Votación Segura</h1>
          <span>Universidad 2026</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section" style="padding-top: 2px">{{ session.role }}</div>
        <template v-for="(item, index) in menu" :key="`${item.seccion || item.to}-${index}`">
          <div v-if="item.seccion" class="nav-section">{{ item.seccion }}</div>
          <RouterLink
            v-else
            class="nav-item"
            :class="{ active: route.path === item.to }"
            :to="item.to"
            @click="sidebarOpen = false"
          >
            <AppIcon :name="item.icon" :size="17" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </template>
      </nav>

      <div class="sidebar-footer">
        <div class="user-chip">
          <UserAvatar :nombre="session.user?.nombre" :size="34" />
          <div class="uc-info">
            <div class="uc-name">{{ session.user?.nombre }}</div>
            <div class="uc-rol">{{ session.role }}</div>
          </div>
          <button class="icon-btn" style="width: 32px; height: 32px" title="Cerrar sesión" @click="cerrarSesion">
            <AppIcon name="logout" :size="15" />
          </button>
        </div>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <button class="icon-btn" title="Menú" @click="sidebarOpen = true">
          <AppIcon name="grip" :size="16" />
        </button>

        <div>
          <div class="page-title">{{ titulo }}</div>
          <div class="page-sub">{{ sub }}</div>
        </div>

        <div class="topbar-actions">
          <div class="search-box">
            <AppIcon name="search" :size="15" />
            <input placeholder="Buscar…" />
          </div>

          <span v-if="state.enVivo" class="badge badge-success en-vivo" style="gap: 6px">
            <span class="live-dot" />
            EN VIVO
          </span>

          <button class="icon-btn" :title="isDark ? 'Tema claro' : 'Tema oscuro'" @click="toggleTema">
            <AppIcon :name="isDark ? 'sun' : 'moon'" :size="16" />
          </button>
          <button class="icon-btn bell" title="Notificaciones">
            <AppIcon name="bell" :size="16" />
            <span class="dot" />
          </button>
          <UserAvatar :nombre="session.user?.nombre" :size="34" />
        </div>

        <div class="sim-wrap" title="Simulador de estado de la elección (prototipo)">
          <span class="text-sm text-muted fw-600 sim-label" style="white-space: nowrap">Estado:</span>
          <select class="select sim-select" :value="state.estadoEleccion" @change="cambiarEstado">
            <option v-for="(info, key) in ESTADOS" :key="key" :value="key">{{ info.label }}</option>
          </select>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: hsl(var(--success));
  animation: pulse 1.4s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.35;
  }
}

.sim-select {
  width: auto;
  padding: 6px 30px 6px 10px;
  font-size: 12.5px;
}

@media (max-width: 900px) {
  .sim-wrap {
    display: none;
  }

  .search-box {
    display: none;
  }
}
</style>
