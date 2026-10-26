import { reactive } from 'vue'

export const toasts = reactive([])

let nextId = 1

export function toast(message, type = 'success', duration = 3400) {
  const id = nextId++
  toasts.push({ id, message, type })

  window.setTimeout(() => {
    const index = toasts.findIndex((t) => t.id === id)
    if (index >= 0) toasts.splice(index, 1)
  }, duration)
}
