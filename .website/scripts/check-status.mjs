// docs/status.md is the only place a milestone's state may be written. Fails if any other doc
// or site source pairs a milestone id (M0–M9) with a state word, or reintroduces a status file.
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const docsDir = resolve(root, '../docs')
const STATE = String.raw`(?:passed|signed[ -]off|sign-off|in progress|future work|delegat\w*|pending|not started|blocked|partial)`
const ID = String.raw`\bM[0-9]\b`
const NEAR = new RegExp(String.raw`${ID}[^\n|]{0,60}?\b${STATE}\b|\b${STATE}\b[^\n|]{0,40}?${ID}`, 'i')

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    return statSync(path).isDirectory() ? walk(path) : [path]
  })
}

const files = [
  ...readdirSync(docsDir).filter((f) => f.endsWith('.md') && f !== 'status.md').map((f) => join(docsDir, f)),
  ...walk(join(root, 'src')).filter((f) => /\.(vue|ts)$/.test(f)),
]
const errors = []
for (const file of files) {
  readFileSync(file, 'utf8').split('\n').forEach((line, i) => {
    const m = NEAR.exec(line)
    if (m) errors.push(`${relative(resolve(root, '..'), file)}:${i + 1}: "${m[0]}"`)
  })
}
if (existsSync(join(root, 'src/data/status.ts'))) errors.push('.website/src/data/status.ts must not exist: status lives in docs/status.md')

console.log(`Checked ${files.length} files for milestone states outside docs/status.md.`)
if (errors.length) {
  console.error(`\n${errors.length} milestone state(s) found outside docs/status.md:`)
  for (const e of errors) console.error(`  ✗ ${e}`)
  process.exit(1)
}
console.log('Milestone states appear only in docs/status.md.')
