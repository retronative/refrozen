// Requests every route through the GitHub Pages simulation, with and without a trailing slash,
// follows redirects, refreshes, and checks status, final URL, canonical tag and that every
// referenced stylesheet, script, font and image loads. Also checks deep links with #anchors,
// the 404 behaviour, case sensitivity and the Open Graph image.
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'
import { createPagesServer } from './pages-sim.mjs'
import { base, siteUrl } from './site-config.mjs'
import { SHOW_SCREENSHOTS, hiddenPaths } from '../src/data/flags.ts'
import { ISSUES_URL, ORG, REPO_URL } from '../src/data/links.ts'

const dist = resolve(import.meta.dirname, '../dist')
const server = createPagesServer(dist, base)
await new Promise((r) => server.listen(0, '127.0.0.1', r))
const origin = `http://127.0.0.1:${server.address().port}`
const failures = []
const fail = (msg) => failures.push(msg)
const assetCache = new Map()

async function get(path, { follow = true } = {}) {
  const chain = []
  let url = new URL(path, origin)
  for (let i = 0; i < 5; i++) {
    const res = await fetch(url, { redirect: 'manual' })
    chain.push(`${res.status} ${url.pathname}`)
    if (follow && res.status >= 300 && res.status < 400) {
      url = new URL(res.headers.get('location'), url)
      continue
    }
    return { res, url, chain, body: await res.text() }
  }
  throw new Error(`Too many redirects for ${path}`)
}

const canonicalOf = (html) => /<link rel="canonical" href="([^"]+)"/.exec(html)?.[1]

async function checkAsset(href, from, label) {
  const url = new URL(href, from)
  if (url.origin !== origin) return fail(`${label}: asset ${href} is not same-origin`)
  if (assetCache.has(url.pathname)) return
  const res = await fetch(url)
  const type = res.headers.get('content-type') ?? ''
  assetCache.set(url.pathname, res.status)
  if (res.status !== 200) return fail(`${label}: asset ${url.pathname} → ${res.status}`)
  if (type.startsWith('text/css')) {
    const css = await res.text()
    for (const [, ref] of css.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)) {
      if (!ref.startsWith('data:') && !ref.startsWith('#')) await checkAsset(ref, url, `${label} (css)`)
    }
  } else if (type.startsWith('text/javascript')) {
    const js = await res.text()
    for (const [, ref] of js.matchAll(/["'`](\.\/[\w.-]+\.(?:js|css|svg))["'`]/g)) await checkAsset(ref, url, `${label} (js)`)
  }
}

async function checkAssets(html, from, label) {
  const refs = []
  for (const [tag] of html.matchAll(/<(?:link|script|img)\b[^>]*>/g)) {
    if (/^<link/.test(tag) && !/rel="(?:stylesheet|modulepreload|preload|icon)"/.test(tag)) continue
    const ref = /\s(?:href|src)="([^"]+)"/.exec(tag)?.[1]
    if (ref) refs.push(ref)
  }
  for (const ref of refs) await checkAsset(ref, from, label)
  return refs.length
}

const sitemap = [...readFileSync(join(dist, 'sitemap.xml'), 'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])
const walk = (dir) => readdirSync(dir).flatMap((n) => (statSync(join(dir, n)).isDirectory() ? walk(join(dir, n)) : [join(dir, n)]))
const routes = walk(dist)
  .filter((f) => f.endsWith('index.html'))
  .map((f) => relative(dist, f).replace(/index\.html$/, ''))
  .sort()

const hiddenUrls = hiddenPaths.map((p) => siteUrl + base + p.slice(1))

const rows = []
for (const route of routes) {
  const slash = base + route
  const forms = route === '' ? [base.replace(/\/$/, ''), base] : [slash.replace(/\/$/, ''), slash]
  for (const form of forms) {
    const { res, url, chain, body } = await get(form)
    const label = form
    if (res.status !== 200) fail(`${label}: final status ${res.status}`)
    if (url.pathname !== slash) fail(`${label}: ended at ${url.pathname}, expected ${slash}`)
    const canonical = canonicalOf(body)
    if (!canonical) fail(`${label}: no canonical tag`)
    else if (!sitemap.includes(canonical) && !hiddenUrls.includes(canonical)) fail(`${label}: canonical ${canonical} is not a sitemap URL`)
    else if (!canonical.endsWith('/')) fail(`${label}: canonical without trailing slash`)
    const assets = await checkAssets(body, url, label)
    const again = await get(url.pathname)
    if (again.res.status !== 200 || again.body !== body) fail(`${label}: refresh returned a different response`)
    rows.push(`${chain.join(' → ')}  canonical ${canonical?.replace(siteUrl, '')}  ${assets} assets`)
  }
}

// Deep links with anchors (the fragment is never sent; the target id must exist).
for (const link of [`${base}faq/#is-it-legal`, `${base}docs/how-it-works#static-recompilation-vs-emulation`, `${base}compatibility#dota-maps`, `${base}releases/#milestones`, `${base}docs/faq#why-version-126a`]) {
  const [path, anchor] = link.split('#')
  const { res, chain, body } = await get(path)
  if (res.status !== 200) fail(`${link}: status ${res.status}`)
  if (!body.includes(`id="${anchor}"`)) fail(`${link}: anchor #${anchor} not found`)
  rows.push(`${chain.join(' → ')}  #${anchor} present`)
}

// 404 behaviour, including case sensitivity.
for (const path of [`${base}no-such-page`, `${base}no-such-page/`, `${base}FAQ/`, `${base}docs/nope/`, `${base}Docs/how-it-works/`]) {
  const { res, url, chain, body } = await get(path)
  if (res.status !== 404) fail(`${path}: expected 404, got ${res.status}`)
  if (!body.includes('Lost in the fog') || !body.includes('noindex')) fail(`${path}: not the site's 404 page`)
  const assets = await checkAssets(body, url, path)
  rows.push(`${chain.join(' → ')}  404 page, ${assets} assets`)
}

// Open Graph image: absolute URL on the canonical origin, served from dist with the declared type
// and pixel size.
const home = await get(base)
const metaContent = (html, key) => new RegExp(`<meta (?:name|property)="${key}" content="([^"]*)"`).exec(html)?.[1]
const og = metaContent(home.body, 'og:image') ?? ''
const ogType = metaContent(home.body, 'og:image:type')
const ogSize = [metaContent(home.body, 'og:image:width'), metaContent(home.body, 'og:image:height')].map(Number)
function imageSize(buf) {
  if (buf.readUInt32BE(0) === 0x89504e47) return [buf.readUInt32BE(16), buf.readUInt32BE(20)]
  if (buf.readUInt16BE(0) === 0xffd8) {
    for (let i = 2; i + 9 < buf.length; i += 2 + buf.readUInt16BE(i + 2)) {
      const marker = buf.readUInt16BE(i)
      if (marker >= 0xffc0 && marker <= 0xffcf && ![0xffc4, 0xffc8, 0xffcc].includes(marker)) return [buf.readUInt16BE(i + 7), buf.readUInt16BE(i + 5)]
    }
  }
  return [0, 0]
}
if (!og.startsWith(`${siteUrl}${base}`)) fail(`og:image ${og} is not under ${siteUrl}${base}`)
else {
  const res = await fetch(new URL(og.slice(siteUrl.length), origin))
  if (res.status !== 200 || res.headers.get('content-type') !== ogType) fail(`og:image ${og} → ${res.status} ${res.headers.get('content-type')} (declared ${ogType})`)
  else {
    const size = imageSize(Buffer.from(await res.arrayBuffer()))
    if (size.join('x') !== ogSize.join('x')) fail(`og:image is ${size.join('×')}, declared ${ogSize.join('×')}`)
    else rows.push(`200 ${og.slice(siteUrl.length)}  og:image (${ogType}, ${size.join('×')})`)
  }
}

// Hidden pages (src/data/flags.ts): still prerendered and served (checked above), but noindex, out of
// the sitemap and linked from no other page. With SHOW_SCREENSHOTS on, the page must be linked and indexable.
const isNoindex = (html) => /<meta name="robots" content="noindex/.test(html)
const pages = routes.map((route) => [`/${route}`, readFileSync(join(dist, route, 'index.html'), 'utf8')])
for (const [path, html] of pages) {
  if (isNoindex(html) !== hiddenPaths.includes(path)) fail(`${path}: noindex ${hiddenPaths.includes(path) ? 'missing' : 'unexpected'}`)
}
for (const [path, html] of [...pages, ['/404.html', readFileSync(join(dist, '404.html'), 'utf8')]]) {
  for (const hidden of hiddenPaths) {
    if (hidden !== path && html.includes(`href="${base}${hidden.slice(1)}"`)) fail(`${path}: links to hidden page ${hidden}`)
  }
}
for (const url of hiddenUrls) if (sitemap.includes(url)) fail(`sitemap lists hidden page ${url}`)
if (SHOW_SCREENSHOTS) {
  if (!sitemap.includes(`${siteUrl}${base}screenshots/`)) fail('SHOW_SCREENSHOTS is on but the sitemap lacks /screenshots/')
  if (!pages.find(([p]) => p === '/')[1].includes(`href="${base}screenshots/"`)) fail('SHOW_SCREENSHOTS is on but the home page does not link /screenshots/')
}
rows.push(`hidden pages: ${hiddenPaths.join(', ') || 'none'} (noindex, not in sitemap, unlinked)`)

// SEO head tags on every page (and 404.html): non-empty title and description mirrored in og:/twitter:,
// absolute og:image/twitter:image, canonical === og:url under the site URL, unique titles across
// sitemap pages, valid JSON-LD; robots.txt points at the sitemap.
const titles = new Map()
for (const [path, html] of [...pages, ['/404.html', readFileSync(join(dist, '404.html'), 'utf8')]]) {
  const head = html.slice(0, html.indexOf('</head>'))
  const title = /<title>([^<]*)<\/title>/.exec(head)?.[1] ?? ''
  const description = metaContent(head, 'description') ?? ''
  if (!title.trim()) fail(`${path}: empty <title>`)
  if (!description.trim()) fail(`${path}: empty meta description`)
  for (const key of ['og:title', 'twitter:title']) if (metaContent(head, key) !== title) fail(`${path}: ${key} differs from <title>`)
  for (const key of ['og:description', 'twitter:description']) if (metaContent(head, key) !== description) fail(`${path}: ${key} differs from the description`)
  for (const key of ['og:image', 'twitter:image']) if (metaContent(head, key) !== og) fail(`${path}: ${key} is not ${og}`)
  for (const [, json] of head.matchAll(/<script type="application\/ld\+json">([^<]*)<\/script>/g)) {
    try {
      JSON.parse(json)
    } catch {
      fail(`${path}: invalid JSON-LD`)
    }
  }
  const footer = html.slice(html.lastIndexOf('<footer'))
  for (const href of [ORG.url, REPO_URL, ISSUES_URL]) if (!footer.includes(`href="${href}"`)) fail(`${path}: footer does not link ${href}`)
  if (path === '/404.html') continue
  const canonical = canonicalOf(head)
  if (!canonical?.startsWith(`${siteUrl}${base}`)) fail(`${path}: canonical ${canonical} is not under ${siteUrl}${base}`)
  if (metaContent(head, 'og:url') !== canonical) fail(`${path}: og:url differs from the canonical URL`)
  if (sitemap.includes(siteUrl + base + path.slice(1))) {
    if (titles.has(title)) fail(`${path}: title "${title}" duplicates ${titles.get(title)}`)
    titles.set(title, path)
  }
}
const robots = readFileSync(join(dist, 'robots.txt'), 'utf8')
if (!robots.split('\n').includes(`Sitemap: ${siteUrl}${base}sitemap.xml`)) fail('robots.txt does not reference the sitemap')
rows.push(`head tags: ${pages.length + 1} pages with title, description, og/twitter, footer project links, ${titles.size} unique sitemap titles; robots.txt → sitemap`)

server.close()
console.log(`Pages simulation at ${base} — ${routes.length} routes × 2 URL forms, ${assetCache.size} distinct assets:`)
for (const row of rows) console.log(`  ${row}`)
if (failures.length) {
  console.error(`\n${failures.length} routing failure(s):`)
  for (const f of failures) console.error(`  ✗ ${f}`)
  process.exit(1)
}
console.log('All routes, redirects, assets, anchors and 404s behave as expected.')
