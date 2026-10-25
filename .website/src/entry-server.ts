import { renderToString } from 'vue/server-renderer'
import { createApp } from './app'
import { aliasPaths, metaFor, staticPaths } from './router'

export { aliasPaths, staticPaths }
export { screenshots } from './data/screenshots'
export { hiddenPaths } from './data/flags'

export async function render(url: string) {
  const { app, router } = createApp()
  await router.push(url)
  await router.isReady()
  const html = await renderToString(app)
  const route = router.currentRoute.value
  return { html, meta: metaFor(route), notFound: route.name === 'not-found' }
}
