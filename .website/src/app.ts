import { createSSRApp } from 'vue'
import App from './App.vue'
import { createAppRouter } from './router'
import './styles/main.css'

export function createApp() {
  const app = createSSRApp(App)
  const router = createAppRouter(import.meta.env.BASE_URL)
  app.use(router)
  return { app, router }
}
