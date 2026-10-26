import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'
import { useSessionStore } from './stores/session'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const session = useSessionStore(pinia)

session.restore().finally(() => {
  app.use(router)
  app.mount('#app')
})
