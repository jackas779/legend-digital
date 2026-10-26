import { defineStore } from 'pinia'
import { CUENTAS_DEMO, HOME, db } from '../lib/data'
import { loginRequest, meRequest } from '../lib/api'

const ROLE_MAP = {
  ADMINISTRADOR: 'ADMIN',
  ADMIN: 'ADMIN',
  ORGANIZADOR: 'ORGANIZADOR',
  VOTANTE: 'VOTANTE',
  AUDITOR: 'AUDITOR',
}

const TOKEN_KEY = 'votacion_access_token'
const REFRESH_KEY = 'votacion_refresh_token'
const USER_KEY = 'votacion_user'

function mapRole(perfil) {
  const roleName = String(perfil?.rol?.nombre || '').trim().toUpperCase()
  if (ROLE_MAP[roleName]) return ROLE_MAP[roleName]
  if (perfil?.is_superuser) return 'ADMIN'
  return 'VOTANTE'
}

function profileToUser(perfil) {
  return {
    id: perfil.id,
    nombre: [perfil.nombres, perfil.apellidos].filter(Boolean).join(' ') || perfil.username || 'Usuario',
    correo: perfil.correo || '',
    documento: perfil.documento || '',
    rol: mapRole(perfil),
  }
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    user: null,
    loading: false,
    error: '',
  }),

  getters: {
    role: (state) => state.user?.rol || null,
    home: (state) => HOME[state.user?.rol] || '/login',
    isAuthenticated: (state) => Boolean(state.user),
  },

  actions: {
    persist() {
      try {
        if (this.user) localStorage.setItem(USER_KEY, JSON.stringify(this.user))
        else localStorage.removeItem(USER_KEY)
      } catch {
        /* almacenamiento no disponible */
      }
    },

    setUser(user) {
      this.user = user
      this.persist()
    },

    loginDemo(rol) {
      const cuenta = CUENTAS_DEMO.find((c) => c.rol === rol)
      if (!cuenta) return false

      const perfil = db.usuarios.find((u) => u.documento === cuenta.doc)
      const nombre = perfil ? `${perfil.nombres} ${perfil.apellidos}` : cuenta.nombre

      this.setUser({
        id: perfil?.id ?? null,
        nombre,
        correo: perfil?.correo ?? '',
        documento: perfil?.documento ?? cuenta.doc,
        rol,
        demo: true,
      })
      this.error = ''
      return true
    },

    async loginReal(identificador, password) {
      this.loading = true
      this.error = ''

      try {
        const payload = await loginRequest(identificador.trim(), password)

        if (!payload?.access) {
          throw new Error('El backend no devolvió un token de acceso.')
        }

        localStorage.setItem(TOKEN_KEY, payload.access)
        localStorage.setItem(REFRESH_KEY, payload.refresh || '')

        const perfil = await meRequest(payload.access)
        this.setUser({ ...profileToUser(perfil), demo: false })
        return true
      } catch (err) {
        this.error = err.message || 'No se pudo iniciar sesión.'
        return false
      } finally {
        this.loading = false
      }
    },

    async restore() {
      try {
        const storedUser = localStorage.getItem(USER_KEY)
        if (storedUser) this.user = JSON.parse(storedUser)
      } catch {
        this.user = null
      }

      const token = localStorage.getItem(TOKEN_KEY)
      if (!token) return

      try {
        const perfil = await meRequest(token)
        this.setUser({ ...profileToUser(perfil), demo: false })
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(REFRESH_KEY)
        if (!this.user?.demo) {
          this.user = null
          this.persist()
        }
      }
    },

    logout() {
      this.user = null
      this.error = ''
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})
