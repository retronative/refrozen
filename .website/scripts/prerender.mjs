// Renders every route to static HTML after the client and SSR builds, then writes
// 404.html, sitemap.xml, robots.txt and .nojekyll. Static output only.
import { existsSync, readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { base, siteUrl, cname } from './site-config.mjs'

const root = resolve(import.meta.dirname, '..')
const dist = join(root, 'dist')
const ssrDir = join(root, '.ssr')
const { render, staticPaths, aliasPaths, screenshots, hiddenPaths, ORG, REPO_URL } = await import(pathToFileURL(join(ssrDir, 'entry-server.js')).href)

const template = readFileSync(join(dist, 'index.html'), 'utf8')

// Screenshot manifest: every entry must be complete and its files present.
for (const shot of screenshots) {
  const where = `screenshot ${shot.file}`
  for (const key of ['file', 'caption', 'alt', 'captureContext', 'rightsReviewedBy']) {
    if (!String(shot[key] ?? '').trim()) throw new Error(`${where}: "${key}" is required`)
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(shot.rightsReviewedOn ?? '')) throw new Error(`${where}: rightsReviewedOn must be YYYY-MM-DD`)
  if (!(shot.width > 0 && shot.height > 0)) throw new Error(`${where}: width and height are required`)
  for (const file of [shot.file, ...(shot.variants ?? []).map((v) => v.file)]) {
    if (!/^[\w.-]+\.(png|webp)$/.test(file)) throw new Error(`${where}: ${file} must be a .png or .webp file name`)
    if (!existsSync(join(dist, 'screenshots', file))) throw new Error(`${where}: public/screenshots/${file} is missing`)
  }
}

const escapeAttr = (value) =>
  value.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

function absolute(path) {
  return siteUrl + base + path.replace(/^\//, '')
}

// JSON-LD with facts stated on the site only: the publisher, WebSite, the application and its
// source repository on the home page, BreadcrumbList on docs pages. No versions, offers or
// ratings (nothing is released).
function structuredData(meta) {
  const url = absolute(meta.canonical)
  const graph = []
  if (meta.canonical === '/') {
    const publisher = { '@id': `${ORG.url}#organization` }
    const app = { '@id': `${url}#application` }
    graph.push(
      { '@type': 'Organization', ...publisher, name: ORG.name, url: ORG.url },
      { '@type': 'WebSite', name: 'reFrozen', url, inLanguage: 'en', publisher },
      { '@type': 'SoftwareApplication', ...app, name: 'reFrozen', description: meta.description, url, applicationCategory: 'GameApplication', operatingSystem: 'macOS (Apple Silicon)', publisher, sameAs: [REPO_URL] },
      { '@type': 'SoftwareSourceCode', name: 'reFrozen', codeRepository: REPO_URL, license: 'https://spdx.org/licenses/GPL-3.0-or-later.html', targetProduct: app, publisher },
    )
  }
  if (meta.breadcrumbs) {
    graph.push({
      '@type': 'BreadcrumbList',
      itemListElement: meta.breadcrumbs.map((crumb, i) => ({ '@type': 'ListItem', position: i + 1, name: crumb.name, item: absolute(crumb.path) })),
    })
  }
  if (!graph.length) return ''
  const json = JSON.stringify({ '@context': 'https://schema.org', '@graph': graph }).replace(/</g, '\\u003c')
  return `\n    <script type="application/ld+json">${json}</script>`
}

function page({ html, meta, notFound }) {
  const title = escapeAttr(meta.title)
  const description = escapeAttr(meta.description)
  const extraHead = notFound
    ? '<meta name="robots" content="noindex" />'
    : `<link rel="canonical" href="${absolute(meta.canonical)}" />\n    <meta property="og:url" content="${absolute(meta.canonical)}" />` +
      (hiddenPaths.includes(meta.canonical) ? '\n    <meta name="robots" content="noindex" />' : structuredData(meta))
  return template
    .replace(/<title>.*?<\/title>/, `<title>${title}</title>`)
    .replace(/(<meta (?:name|property)="(?:description|og:description|twitter:description)" content=")[^"]*"/g, `$1${description}"`)
    .replace(/(<meta (?:property|name)="(?:og:title|twitter:title)" content=")[^"]*"/g, `$1${title}"`)
    .replace(/(<meta (?:property|name)="(?:og:image|twitter:image)" content=")[^"]*"/g, `$1${absolute('/og.jpg')}"`)
    .replace('<!--head-->', () => extraHead)
    .replace('<!--app-html-->', html)
}

function write(file, contents) {
  mkdirSync(dirname(file), { recursive: true })
  writeFileSync(file, contents)
}

for (const path of [...staticPaths, ...aliasPaths]) {
  const result = await render(path)
  if (result.notFound) throw new Error(`Prerender: ${path} resolved to the 404 page`)
  if (staticPaths.includes(path) && result.meta.canonical !== path) throw new Error(`Prerender: ${path} has canonical ${result.meta.canonical}`)
  write(join(dist, path, 'index.html'), page(result))
}

write(join(dist, '404.html'), page(await render('/404/')))

write(
  join(dist, 'sitemap.xml'),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    staticPaths.filter((p) => !hiddenPaths.includes(p)).map((p) => `  <url><loc>${absolute(p)}</loc></url>`).join('\n') +
    '\n</urlset>\n',
)
write(join(dist, 'robots.txt'), `User-agent: *\nAllow: /\n\nSitemap: ${absolute('/sitemap.xml')}\n`)
write(join(dist, '.nojekyll'), '')
if (cname) {
  if (!/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(cname)) throw new Error(`SITE_CNAME is not a domain name: ${cname}`)
  write(join(dist, 'CNAME'), `${cname}\n`)
}
rmSync(ssrDir, { recursive: true, force: true })

console.log(`Prerendered ${staticPaths.length} routes, ${aliasPaths.length} aliases + 404.html (base ${base}, site ${siteUrl})`)
