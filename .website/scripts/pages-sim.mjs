// A small static server that emulates GitHub Pages' documented behaviour for a project site,
// so routing can be tested locally. Emulated:
//   - the site is mounted at SITE_BASE (default /refrozen/); "/refrozen" → 301 "/refrozen/"
//   - a directory requested without a trailing slash → 301 to the slash form
//   - a directory with a trailing slash → its index.html
//   - "/foo" with no file or directory but "foo.html" present → that file
//   - case-sensitive paths (checked per segment, even on a case-insensitive disk)
//   - anything else → the site's 404.html with status 404
// Not emulated: CDN caching headers, HTTPS redirects, custom-domain behaviour. Real Pages
// behaviour can only be confirmed after deployment.
//   node scripts/pages-sim.mjs [port]
import { createServer } from 'node:http'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { extname, join, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { base } from './site-config.mjs'

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.webp': 'image/webp',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml',
  '.json': 'application/json',
}

function exact(dist, segments) {
  let current = dist
  for (const segment of segments) {
    let entries
    try {
      entries = readdirSync(current)
    } catch {
      return null
    }
    if (!entries.includes(segment)) return null
    current = join(current, segment)
  }
  return current
}

const isFile = (p) => p && statSync(p).isFile()
const isDir = (p) => p && statSync(p).isDirectory()

export function createPagesServer(dist = resolve(import.meta.dirname, '../dist'), siteBase = base) {
  const mount = siteBase.replace(/\/$/, '')
  return createServer((req, res) => {
    const url = new URL(req.url, 'http://pages.local')
    const send = (status, file, headers = {}) => {
      const body = file ? readFileSync(file) : Buffer.from('Not Found')
      res.writeHead(status, { 'Content-Type': file ? TYPES[extname(file)] ?? 'application/octet-stream' : 'text/plain', ...headers })
      res.end(req.method === 'HEAD' ? undefined : body)
    }
    const notFound = () => {
      const page = exact(dist, ['404.html'])
      return isFile(page) ? send(404, page) : send(404, null)
    }
    const redirect = (location) => {
      res.writeHead(301, { Location: location + url.search, 'Content-Type': 'text/html' })
      res.end()
    }

    if (req.method !== 'GET' && req.method !== 'HEAD') return send(405, null)
    let path
    try {
      path = decodeURIComponent(url.pathname)
    } catch {
      return notFound()
    }
    if (path === mount) return redirect(`${mount}/`)
    if (!path.startsWith(`${mount}/`)) return send(404, null)
    const rel = path.slice(mount.length + 1)
    if (rel.split('/').some((s) => s === '..' || s.includes('\0'))) return notFound()
    const segments = rel.split('/').filter(Boolean)

    if (rel === '' || rel.endsWith('/')) {
      const dir = exact(dist, segments)
      const index = isDir(dir) ? exact(dir, ['index.html']) : null
      return isFile(index) ? send(200, index) : notFound()
    }
    const target = exact(dist, segments)
    if (isFile(target)) return send(200, target)
    if (isDir(target) && isFile(exact(target, ['index.html']))) return redirect(`${url.pathname}/`)
    const html = exact(dist, [...segments.slice(0, -1), `${segments.at(-1)}.html`])
    if (isFile(html)) return send(200, html)
    return notFound()
  })
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const port = Number(process.argv[2] ?? 4790)
  createPagesServer().listen(port, () => console.log(`Pages simulation: http://localhost:${port}${base}`))
}
