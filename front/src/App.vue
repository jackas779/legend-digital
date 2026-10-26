<script setup>
import { ref, onMounted } from 'vue'

const API_BASE_URL = 'http://127.0.0.1:8000'
const correo = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const user = ref(null)

function readStoredToken() {
  return localStorage.getItem('votacion_access_token') || ''
}

async function fetchProfile(token) {
  const response = await fetch(`${API_BASE_URL}/api/usuarios/me/`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error('No se pudo obtener el perfil del usuario.')
  }

  return response.json()
}

async function handleLogin() {
  error.value = ''
  success.value = ''
  loading.value = true

  try {
    const response = await fetch(`${API_BASE_URL}/api/usuarios/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        correo: correo.value,
        password: password.value,
      }),
    })

    const payload = await response.json()

    if (!response.ok) {
      const details = payload?.non_field_errors || payload?.detail || 'Credenciales incorrectas.'
      throw new Error(Array.isArray(details) ? details.join(', ') : details)
    }

    localStorage.setItem('votacion_access_token', payload.access)
    localStorage.setItem('votacion_refresh_token', payload.refresh)

    const profile = await fetchProfile(payload.access)
    user.value = profile
    success.value = 'Inicio de sesión correcto. Conectado al backend Django.'
    correo.value = ''
    password.value = ''
  } catch (err) {
    error.value = err.message || 'No se pudo iniciar sesión.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const token = readStoredToken()
  if (!token) return

  fetchProfile(token)
    .then((profile) => {
      user.value = profile
      success.value = 'Sesión recuperada desde el backend.'
    })
    .catch(() => {
      localStorage.removeItem('votacion_access_token')
      localStorage.removeItem('votacion_refresh_token')
    })
})
</script>

<template>
  <main class="page">
    <section class="card">
      <div class="header">
        <p class="eyebrow">Proyecto de votación</p>
        <h1>Conexión Vue + Django</h1>
      </div>

      <div v-if="!user" class="form-box">
        <label>
          <span>Correo</span>
          <input v-model="correo" type="email" placeholder="usuario@ejemplo.com" />
        </label>

        <label>
          <span>Contraseña</span>
          <input v-model="password" type="password" placeholder="••••••••" />
        </label>

        <button :disabled="loading" @click="handleLogin">
          {{ loading ? 'Ingresando...' : 'Iniciar sesión' }}
        </button>
      </div>

      <div v-else class="profile-box">
        <h2>Usuario autenticado</h2>
        <p><strong>Nombre:</strong> {{ user.nombres }} {{ user.apellidos }}</p>
        <p><strong>Correo:</strong> {{ user.correo }}</p>
        <p><strong>Documento:</strong> {{ user.documento }}</p>
        <p><strong>Estado:</strong> {{ user.estado }}</p>
      </div>

      <div v-if="error" class="alert error">{{ error }}</div>
      <div v-if="success" class="alert success">{{ success }}</div>

      <div class="api-info">
        <p>API Django:</p>
        <code>{{ API_BASE_URL }}/api/usuarios/login/</code>
      </div>
    </section>
  </main>
</template>
