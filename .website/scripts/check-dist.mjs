// Artifact hygiene: dist/ is what gets published. Fail on unexpected file types, source maps,
// or content that suggests private material (internal notes, game files, local paths, keys).
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { basename, extname, join, relative, resolve } from 'node:path'

const dist = resolve(import.meta.dirname, '../dist')
const ALLOWED_EXT = new Set(['.html', '.css', '.js', '.svg', '.woff2', '.txt', '.xml', '.json', '.ico', '.webmanifest'])
const ALLOWED_NAMES = new Set(['CNAME', '.nojekyll'])
const TEXT_EXT = new Set(['.html', '.css', '.js', '.svg', '.txt', '.xml', '.json', '.webmanifest'])
const MAX_FILE_BYTES = 1_000_000
// Raster images: only the generated Open Graph image and rights-reviewed screenshots.
const OG_IMAGE = 'og.png'
const OG_MAX_BYTES = 500_000
const SCREENSHOT_EXT = new Set(['.png', '.webp'])
const SCREENSHOT_MAX_BYTES = 1_500_000
// The home hero's artwork (AI-generated, rights-reviewed; see the disclaimer): exactly these responsive files.
const HERO_FILE = /^hero\/hero-b-(640|960|1280|1920|2560|2880|3840)\.(avif|webp)$/
const HERO_MAX_BYTES = 600_000
// Page banner paintings (see the disclaimer): exactly these responsive files.
const BANNER_FILE = /^banners\/(forge|library|portal|tavern|battlefield|fog)-(640|1280|1920)\.(avif|webp)$/
const BANNER_MAX_BYTES = 400_000

const FORBIDDEN = [
  [/(?<![\w./-])reference\//, 'internal reference/ path'],
  [/(?<![\w./-])game\//, 'game/ path'],
  [/(?<![\w./-])(?:tools|patches|scripts)\/[\w.-]+\.(?:py|sh|md)/, 'repository tool/script path'],
  [/WORKLOG/i, 'local work log'],
  [/(?:FEASIBILITY|TEST_COVERAGE|RELEASE_PLAN|ROADMAP)\.md/, 'internal planning document'],
  [/[\w-]\.(?:w3x|w3m|w3g|mpq|exe|dll|blp|mdx)\b/i, 'game file name'],
  [/\/Users\/|\/home\/[a-z]|[A-Z]:\\\\Users/, 'absolute local path'],
  [/\b[A-Z0-9]{4,6}(?:-[A-Z0-9]{4,6}){3,}\b/, 'CD-key-like pattern'],
  [/\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{26}\b/, 'CD-key-like pattern (26 characters)'],
  [/sourceMappingURL=/, 'source map reference'],
]

// No runtime requests to other origins: scripts, stylesheets, fonts, preconnects.
const THIRD_PARTY = [
  [/<script\b[^>]*\ssrc="(?:https?:)?\/\//i, 'external script'],
  [/<link\b(?=[^>]*\srel="(?:stylesheet|preload|modulepreload|preconnect|dns-prefetch|icon)")[^>]*\shref="(?:https?:)?\/\/[^"]*"/i, 'external stylesheet/font/preconnect'],
  [/@import\s+(?:url\()?["']?(?:https?:)?\/\//i, 'external CSS @import'],
  [/url\(\s*["']?(?:https?:)?\/\/(?!www\.w3\.org)/i, 'external url() in CSS'],
  [/fonts\.(?:googleapis|gstatic)\.com|use\.typekit\.net|fonts\.bunny\.net/i, 'web-font service'],
]

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    return statSync(path).isDirectory() ? walk(path) : [path]
  })
}

const errors = []
const files = walk(dist)
let bytes = 0
for (const file of files) {
  const rel = relative(dist, file)
  const name = basename(file)
  const ext = extname(file).toLowerCase()
  const size = statSync(file).size
  bytes += size
  const inScreenshots = rel.startsWith('screenshots/') && !rel.slice(12).includes('/')
  if (ext === '.map') errors.push(`${rel}: source map (not published)`)
  else if (rel === OG_IMAGE) {
    if (size > OG_MAX_BYTES) errors.push(`${rel}: ${size} bytes exceeds ${OG_MAX_BYTES}`)
  } else if (BANNER_FILE.test(rel.split('\\').join('/'))) {
    if (size > BANNER_MAX_BYTES) errors.push(`${rel}: ${size} bytes exceeds ${BANNER_MAX_BYTES}`)
  } else if (HERO_FILE.test(rel.split('\\').join('/'))) {
    if (size > HERO_MAX_BYTES) errors.push(`${rel}: ${size} bytes exceeds ${HERO_MAX_BYTES}`)
  } else if (inScreenshots && SCREENSHOT_EXT.has(ext)) {
    if (size > SCREENSHOT_MAX_BYTES) errors.push(`${rel}: ${size} bytes exceeds ${SCREENSHOT_MAX_BYTES}`)
  } else if (inScreenshots && name === '.gitkeep') {
    if (size !== 0) errors.push(`${rel}: placeholder must be empty`)
  } else if (!ALLOWED_NAMES.has(name) && !ALLOWED_EXT.has(ext)) errors.push(`${rel}: file type not on the allowlist`)
  if (size > MAX_FILE_BYTES && !inScreenshots) errors.push(`${rel}: ${size} bytes is larger than expected`)
  if (!TEXT_EXT.has(ext)) continue
  const text = readFileSync(file, 'utf8')
  for (const [pattern, why] of THIRD_PARTY) {
    const m = pattern.exec(text)
    if (m) errors.push(`${rel}: ${why}: "${m[0].slice(0, 120)}"`)
  }
  for (const [pattern, why] of FORBIDDEN) {
    const m = pattern.exec(text)
    if (m) errors.push(`${rel}: ${why}: "…${text.slice(Math.max(0, m.index - 30), m.index + m[0].length + 30).replace(/\s+/g, ' ')}…"`)
  }
}

console.log(`Scanned ${files.length} files in dist/ (${(bytes / 1024).toFixed(1)} KiB).`)
if (errors.length) {
  console.error(`\n${errors.length} problem(s):`)
  for (const e of errors) console.error(`  ✗ ${e}`)
  process.exit(1)
}
console.log('Artifact contains only allowed file types and no private-looking content.')
