// Vite plugin exposing ../docs/*.md as `virtual:docs`, rendered to HTML at build time.
// docs/ stays the single source of truth; nothing is copied into the website.
import { readFileSync, readdirSync } from 'node:fs'
import { join, resolve } from 'node:path'
import MarkdownIt from 'markdown-it'
import { slugify, routeForDoc } from '../scripts/slug.mjs'

const VIRTUAL_ID = 'virtual:docs'
const RESOLVED_ID = '\0' + VIRTUAL_ID

export function parseFrontmatter(source) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(source)
  if (!match) return { data: {}, body: source }
  const data = {}
  for (const line of match[1].split(/\r?\n/)) {
    const kv = /^(\w+):\s*(.*)$/.exec(line)
    if (kv) data[kv[1]] = kv[2].trim()
  }
  return { data, body: source.slice(match[0].length) }
}

function createRenderer(base) {
  // html: false escapes any raw HTML in the Markdown; markdown-it's default validateLink
  // rejects javascript:, vbscript: and data: URLs. Together that is the sanitisation.
  const md = new MarkdownIt({ html: false, linkify: false, typographer: true })

  md.core.ruler.push('heading_ids', (state) => {
    const seen = new Map()
    state.tokens.forEach((token, i) => {
      if (token.type !== 'heading_open') return
      const id = slugify(state.tokens[i + 1].content)
      const n = seen.get(id) ?? 0
      seen.set(id, n + 1)
      token.attrSet('id', n ? `${id}-${n + 1}` : id)
    })
  })

  md.core.ruler.push('doc_links', (state) => {
    for (const block of state.tokens) {
      for (const token of block.children ?? []) {
        if (token.type !== 'link_open') continue
        const href = token.attrGet('href') ?? ''
        const doc = /^(?:\.\/)?([\w-]+)\.md(#[\w-]*)?$/.exec(href)
        if (doc) {
          token.attrSet('href', base + routeForDoc(doc[1]).slice(1) + (doc[2] ?? ''))
        } else if (/^https?:\/\//.test(href)) {
          token.attrSet('rel', 'noopener noreferrer')
        }
      }
    }
  })

  md.renderer.rules.table_open = () => '<div class="table-wrap" tabindex="0"><table>\n'
  md.renderer.rules.table_close = () => '</table></div>\n'
  return md
}

function splitSections(html) {
  const parts = html.split(/(?=<h2 id=")/)
  const intro = parts[0].startsWith('<h2 id="') ? '' : parts.shift()
  const sections = parts.map((part) => {
    const head = /^<h2 id="([^"]+)">([\s\S]*?)<\/h2>\n?/.exec(part)
    return { id: head[1], title: head[2], html: part.slice(head[0].length) }
  })
  return { intro, sections }
}

// Milestone states allowed in docs/status.md, mapped to the keys the site styles.
export const STATUS_STATES = {
  'passed, signed off': 'signed-off',
  'passed, sign-off pending': 'delegated',
  'in progress': 'in-progress',
  'future work': 'future',
}

// docs/status.md is the single source of milestone status and release scope.
export function parseStatus(docsDir, base) {
  const md = createRenderer(base)
  const { data, body } = parseFrontmatter(readFileSync(join(docsDir, 'status.md'), 'utf8'))
  const section = (heading) => {
    const start = body.search(new RegExp(`^#{2,3} ${heading}\\s*$`, 'm'))
    if (start < 0) throw new Error(`docs/status.md: missing heading "${heading}"`)
    const rest = body.slice(start).split('\n').slice(1).join('\n')
    const end = rest.search(/^#{2,3} /m)
    return end < 0 ? rest : rest.slice(0, end)
  }
  const milestones = section('Milestones')
    .split('\n')
    .filter((line) => /^\|\s*M\d+\s*\|/.test(line))
    .map((line) => {
      const [id, title, stateText, note] = line.split('|').slice(1, -1).map((c) => c.trim())
      const state = STATUS_STATES[stateText.toLowerCase()]
      if (!state) throw new Error(`docs/status.md: unknown state "${stateText}" for ${id}`)
      return { id, title, state, stateText, note: md.renderInline(note) }
    })
  const list = (heading) =>
    section(heading)
      .split('\n')
      .filter((line) => line.startsWith('- '))
      .map((line) => md.renderInline(line.slice(2).trim()))
  if (!data.release_headline || !data.release_planned) throw new Error('docs/status.md: release_headline and release_planned are required')
  return {
    releaseHeadline: data.release_headline,
    releasePlanned: data.release_planned,
    milestones,
    planned: list('Planned for v0.1.0'),
    excluded: list('Not part of v0.1.0'),
  }
}

export function loadDocs(docsDir, base) {
  const md = createRenderer(base)
  return readdirSync(docsDir)
    .filter((file) => file.endsWith('.md'))
    .map((file) => {
      const slug = file.replace(/\.md$/, '')
      const { data, body } = parseFrontmatter(readFileSync(join(docsDir, file), 'utf8'))
      const html = md.render(body).replace(/^<h1[^>]*>[\s\S]*?<\/h1>\n?/, '')
      const { intro, sections } = splitSections(html)
      return {
        slug,
        route: routeForDoc(slug),
        title: data.title || slug,
        description: data.description || '',
        order: Number(data.order ?? 99),
        html,
        intro,
        sections,
      }
    })
    .sort((a, b) => a.order - b.order || a.slug.localeCompare(b.slug))
}

export default function docsPlugin(docsDir = resolve(import.meta.dirname, '../../docs')) {
  let base = '/'
  return {
    name: 'refrozen-docs',
    configResolved(config) {
      base = config.base
    },
    resolveId(id) {
      if (id === VIRTUAL_ID) return RESOLVED_ID
    },
    load(id) {
      if (id !== RESOLVED_ID) return
      const docs = loadDocs(docsDir, base)
      for (const file of readdirSync(docsDir)) this.addWatchFile(join(docsDir, file))
      const status = parseStatus(docsDir, base)
      return `export default ${JSON.stringify(docs)}\nexport const status = ${JSON.stringify(status)}`
    },
    handleHotUpdate({ file, server }) {
      if (file.startsWith(docsDir) && file.endsWith('.md')) {
        const mod = server.moduleGraph.getModuleById(RESOLVED_ID)
        if (mod) server.reloadModule(mod)
      }
    },
  }
}
