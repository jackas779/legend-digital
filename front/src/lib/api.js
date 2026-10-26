const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export { API_BASE_URL }

export function extractApiError(payload, fallback = 'Ocurrió un error inesperado.') {
  if (!payload) return fallback

  const candidate =
    payload.non_field_errors ||
    payload.detail ||
    payload.correo ||
    payload.password ||
    payload.error

  if (Array.isArray(candidate)) return candidate.join(' ')
  if (typeof candidate === 'string') return candidate

  if (typeof payload === 'object') {
    const first = Object.values(payload)[0]
    if (Array.isArray(first)) return first.join(' ')
    if (typeof first === 'string') return first
  }

  return fallback
}

async function readPayload(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    })
  } catch {
    throw new Error(`No se pudo conectar con el backend (${API_BASE_URL}). Verifica que runserver esté activo.`)
  }

  const payload = await readPayload(response)

  if (!response.ok) {
    throw new Error(extractApiError(payload, 'No se pudo completar la solicitud.'))
  }

  return payload
}

export function loginRequest(identificador, password) {
  return request('/api/usuarios/login/', {
    method: 'POST',
    body: JSON.stringify({ correo: identificador, password }),
  })
}

export function meRequest(token) {
  return request('/api/usuarios/me/', {
    headers: { Authorization: `Bearer ${token}` },
  })
}
