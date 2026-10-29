import {
  createRouter,
  createMemoryHistory,
  createWebHistory,
  type RouteLocationNormalized,
  type RouteRecordRaw,
} from 'vue-router'
import { docs, findDoc } from './docs'
import { installPath, installSteps } from './data/release'

export interface PageMeta {
  title: string
  description: string
  /** Canonical path (with trailing slash); undefined for the 404 page. */
  canonical?: string
  /** Breadcrumb trail for docs pages (structured data), ending with the page itself. */
  breadcrumbs?: { name: string; path: string }[]
}

const SITE = 'reFrozen'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('./pages/HomePage.vue'),
    meta: {
      title: `${SITE} — Warcraft III 1.26a, native on Apple Silicon`,
      description:
        'reFrozen statically recompiles Warcraft III: The Frozen Throne 1.26a to native arm64 macOS for offline DotA. Not an emulator, not Wine. Unofficial fan project.',
    },
  },
  {
    path: '/features/',
    name: 'features',
    component: () => import('./pages/FeaturesPage.vue'),
    meta: {
      title: `Features — ${SITE}`,
      description:
        'What already runs natively: menus and rendering, a full local DotA match, Miles audio, mouse and keyboard, Retina and borderless fullscreen, replays and a Wine-free installer.',
    },
  },
  {
    path: '/screenshots/',
    name: 'screenshots',
    component: () => import('./pages/ScreenshotsPage.vue'),
    meta: {
      title: `Screenshots — ${SITE}`,
      description: 'Screenshot plates for reFrozen. Real screenshots will be published once approved.',
    },
  },
  {
    path: '/docs/',
    name: 'docs',
    component: () => import('./pages/DocsIndexPage.vue'),
    meta: {
      title: `Documentation — ${SITE}`,
      description: 'Getting started, how static recompilation works, compatibility, FAQ, disclaimer and credits.',
    },
  },
  {
    path: '/docs/installation/',
    name: 'install',
    component: () => import('./pages/InstallAllPage.vue'),
    meta: {
      title: `Installation guide — ${SITE}`,
      description:
        'Installing reFrozen 0.2.0, all five steps on one page: download, Applications, first launch, preparing your own game and playing.',
    },
  },
  ...installSteps.map(
    (step, index): RouteRecordRaw => ({
      path: installPath(step),
      name: `install-${step.slug}`,
      component: () => import('./pages/InstallStepPage.vue'),
      props: { index },
      meta: { title: `${step.title} — Installation guide — ${SITE}`, description: step.description },
    }),
  ),
  {
    path: '/docs/:slug/',
    name: 'doc',
    component: () => import('./pages/DocPage.vue'),
    beforeEnter: (to) => {
      const doc = findDoc(String(to.params.slug))
      if (!doc) return { name: 'not-found', params: { pathMatch: to.path.slice(1).split('/') } }
      if (doc.route !== to.path) return doc.route
    },
  },
  {
    path: '/compatibility/',
    alias: '/docs/compatibility/',
    name: 'compatibility',
    component: () => import('./pages/CompatibilityPage.vue'),
  },
  {
    path: '/faq/',
    alias: '/docs/faq/',
    name: 'faq',
    component: () => import('./pages/FaqPage.vue'),
  },
  {
    path: '/releases/',
    alias: '/docs/status/',
    name: 'releases',
    component: () => import('./pages/ReleasesPage.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('./pages/NotFoundPage.vue'),
    meta: {
      title: `Lost in the fog — ${SITE}`,
      description: 'This page does not exist.',
    },
  },
]

/** Every prerendered path. Docs with a dedicated page are only reachable there. */
export const staticPaths = [
  '/',
  '/features/',
  '/screenshots/',
  '/docs/',
  installPath(),
  ...installSteps.map((step) => installPath(step)),
  ...docs.filter((doc) => doc.route.startsWith('/docs/')).map((doc) => doc.route),
  '/compatibility/',
  '/faq/',
  '/releases/',
]

/** Docs with a dedicated page are also served at /docs/<slug>/, canonicalised to that page. */
export const aliasPaths = docs.filter((doc) => !doc.route.startsWith('/docs/')).map((doc) => `/docs/${doc.slug}/`)

const docRouteToSlug = Object.fromEntries(docs.map((doc) => [doc.route, doc.slug]))

function breadcrumbsFor(canonical: string, title: string): PageMeta['breadcrumbs'] {
  if (!canonical.startsWith('/docs/')) return undefined
  const crumbs = [
    { name: 'Home', path: '/' },
    { name: 'Documentation', path: '/docs/' },
  ]
  if (canonical !== installPath() && canonical.startsWith(installPath())) crumbs.push({ name: 'Installation guide', path: installPath() })
  if (canonical !== '/docs/') crumbs.push({ name: title.split(' — ')[0], path: canonical })
  return crumbs
}

export function metaFor(route: RouteLocationNormalized): PageMeta {
  if (route.name === 'not-found') return route.meta as unknown as PageMeta
  const record = route.matched[route.matched.length - 1]
  const canonical = route.params.slug ? route.path : (record?.aliasOf ?? record)?.path ?? route.path
  const slug = typeof route.params.slug === 'string' ? route.params.slug : docRouteToSlug[canonical]
  const doc = slug ? findDoc(slug) : undefined
  const meta = doc ? { title: `${doc.title} — ${SITE}`, description: doc.description } : (route.meta as unknown as PageMeta)
  return { title: meta.title, description: meta.description, canonical, breadcrumbs: breadcrumbsFor(canonical, meta.title) }
}

export function createAppRouter(base: string) {
  return createRouter({
    history: import.meta.env.SSR ? createMemoryHistory(base) : createWebHistory(base),
    routes,
    scrollBehavior(to, _from, saved) {
      if (saved) return saved
      if (to.hash) return { el: to.hash, top: 96 }
      return { top: 0 }
    },
  })
}
