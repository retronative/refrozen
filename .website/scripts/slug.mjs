// Shared by the docs plugin and the link checker so heading anchors agree.
export function slugify(text) {
  return text
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/<[^>]*>/g, '')
    .replace(/&[a-z]+;|&#\d+;/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

// Docs with a dedicated top-level page; every other doc lives under /docs/<slug>/.
export const DEDICATED_ROUTES = { compatibility: '/compatibility/', faq: '/faq/', status: '/releases/' }

export function routeForDoc(slug) {
  return DEDICATED_ROUTES[slug] ?? `/docs/${slug}/`
}
