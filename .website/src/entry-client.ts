import { createApp } from './app'
import { metaFor } from './router'

const { app, router } = createApp()

function setMeta(name: string, content: string, attr: 'name' | 'property' = 'name') {
  document.head.querySelector(`meta[${attr}="${name}"]`)?.setAttribute('content', content)
}

router.afterEach((to, from) => {
  if (to.path === from.path) return
  const meta = metaFor(to)
  document.title = meta.title
  setMeta('description', meta.description)
  setMeta('og:title', meta.title, 'property')
  setMeta('og:description', meta.description, 'property')
  setMeta('twitter:title', meta.title)
  setMeta('twitter:description', meta.description)
})

router.isReady().then(() => app.mount('#app'))
