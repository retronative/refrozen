// Renders the DMG background from dmg-background.html for a packaging step (the outputs are not
// committed). No npm packages: Node 22+ (global WebSocket), Google Chrome, and macOS sips/tiffutil.
//
//   node assets/dmg/render.mjs [--out DIR] [--art painted|vector] [--mock]
//
// Writes into DIR (default: build/dmg under the repository root):
//   dmg-background.png      660 x 400 px, 72 dpi
//   dmg-background@2x.png   1320 x 800 px, 144 dpi
//   dmg-background.tiff     both representations (give this one to Finder)
// With --mock it writes dmg-mockup-dark@2x.png and dmg-mockup-light@2x.png instead, with the
// icons and labels Finder would draw (for review only).
//
// It then measures the 1x render: the contrast of white and black label text (Finder uses white in
// Dark appearance, black in Light) against the lightest and darkest pixel of each label plate, and
// the mean luminance behind each icon. It exits with status 1 if a label falls below 4.5:1.
//
// Rendering goes through the DevTools protocol at an exact 660 x 400 viewport; Chrome's
// --screenshot flag is not used because in new headless mode --window-size includes the frame.
import { spawn, execFileSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const args = process.argv.slice(2)
const opt = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback)
const here = import.meta.dirname
const out = resolve(opt('--out', join(here, '..', '..', 'build', 'dmg')))
const art = opt('--art', 'painted')
const mock = args.includes('--mock')
const chromePath = process.env.CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
// Finder layout (dmg-design.md): icon centres and label plates, in points.
const ICONS = [[185, 250], [475, 250]]
const PLATES = ICONS.map(([x]) => ({ x: x - 68, y: 315, w: 136, h: 24 }))

mkdirSync(out, { recursive: true })
const profile = mkdtempSync(join(tmpdir(), 'refrozen-dmg-'))
const port = 9400 + Math.floor(Math.random() * 400)
const chrome = spawn(chromePath, ['--headless=new', `--remote-debugging-port=${port}`, '--hide-scrollbars', '--force-color-profile=srgb', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

let ws
for (let i = 0; i < 75 && !ws; i++) {
  await sleep(200)
  try {
    const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === 'page')
    if (target) ws = new WebSocket(target.webSocketDebuggerUrl)
  } catch {}
}
if (!ws) throw new Error(`Chrome did not start (${chromePath})`)
await new Promise((r) => ws.addEventListener('open', r))
let id = 0
const pending = new Map()
ws.addEventListener('message', (e) => {
  const m = JSON.parse(e.data)
  if (pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id) }
})
const send = (method, params = {}) => new Promise((resolveSend, reject) => {
  pending.set(++id, (m) => (m.error ? reject(new Error(`${method}: ${m.error.message}`)) : resolveSend(m.result)))
  ws.send(JSON.stringify({ id, method, params }))
})
const evaluate = async (expression) => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result.value

async function shoot(query, scale) {
  await send('Emulation.setDeviceMetricsOverride', { width: 660, height: 400, deviceScaleFactor: scale, mobile: false })
  await send('Page.navigate', { url: `${pathToFileURL(join(here, 'dmg-background.html')).href}?${query}` })
  await sleep(1000)
  await evaluate('document.fonts.ready.then(() => Promise.all([...document.images].map((i) => i.decode().catch(() => {}))))')
  await sleep(300)
  return (await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: 660, height: 400, scale: 1 } })).data
}

await send('Page.enable')
let measured
if (mock) {
  for (const appearance of ['dark', 'light']) {
    writeFileSync(join(out, `dmg-mockup-${appearance}@2x.png`), Buffer.from(await shoot(`art=${art}&mock=1&appearance=${appearance}`, 2), 'base64'))
    console.log(`wrote ${join(out, `dmg-mockup-${appearance}@2x.png`)}`)
  }
} else {
  const one = await shoot(`art=${art}`, 1)
  writeFileSync(join(out, 'dmg-background.png'), Buffer.from(one, 'base64'))
  writeFileSync(join(out, 'dmg-background@2x.png'), Buffer.from(await shoot(`art=${art}`, 2), 'base64'))
  execFileSync('sips', ['-s', 'dpiWidth', '144', '-s', 'dpiHeight', '144', join(out, 'dmg-background@2x.png')], { stdio: 'ignore' })
  execFileSync('tiffutil', ['-cathidpicheck', join(out, 'dmg-background.png'), join(out, 'dmg-background@2x.png'), '-out', join(out, 'dmg-background.tiff')], { stdio: 'ignore' })
  for (const f of ['dmg-background.png', 'dmg-background@2x.png', 'dmg-background.tiff']) console.log(`wrote ${join(out, f)}`)
  // Measure in the browser: decode the 1x render onto a canvas and read the pixels back.
  measured = await evaluate(`(async () => {
    const img = new Image(); img.src = 'data:image/png;base64,${one}'; await img.decode()
    const c = document.createElement('canvas'); c.width = 660; c.height = 400
    const x = c.getContext('2d'); x.drawImage(img, 0, 0)
    const lin = (v) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)
    const lum = (d, i) => 0.2126 * lin(d[i]) + 0.7152 * lin(d[i + 1]) + 0.0722 * lin(d[i + 2])
    const stats = (rx, ry, rw, rh) => {
      const d = x.getImageData(rx, ry, rw, rh).data; let min = 1, max = 0, sum = 0
      for (let i = 0; i < d.length; i += 4) { const l = lum(d, i); min = Math.min(min, l); max = Math.max(max, l); sum += l }
      return { min, max, mean: sum / (d.length / 4) }
    }
    // Plates inset by 3 px (the rounded corners and the gilt ring are not under the text).
    const plates = ${JSON.stringify(PLATES)}.map((p) => stats(p.x + 3, p.y + 3, p.w - 6, p.h - 6))
    // Behind each icon: the 128 pt well plus an 8 pt ring (where the icon's edge meets the art).
    const wells = ${JSON.stringify(ICONS)}.map(([cx, cy]) => stats(cx - 72, cy - 72, 144, 144))
    return { plates, wells }
  })()`)
}
ws.close()
await new Promise((r) => { chrome.once('exit', r); chrome.kill() })
rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })

if (measured) {
  const ratio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
  const lin = (v) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)
  const goldDeep = 0.2126 * lin(0xab) + 0.7152 * lin(0x7f) + 0.0722 * lin(0x52)
  let failed = false
  measured.plates.forEach((p, i) => {
    const white = ratio(1, p.max), black = ratio(0, p.min)
    if (white < 4.5 || black < 4.5) failed = true
    console.log(`label plate ${i + 1}: luminance ${p.min.toFixed(4)}-${p.max.toFixed(4)}; white text ${white.toFixed(2)}:1, black text ${black.toFixed(2)}:1`)
  })
  measured.wells.forEach((w, i) => {
    console.log(`icon well ${i + 1}: mean luminance ${w.mean.toFixed(4)} (max ${w.max.toFixed(4)}); gold frame #ab7f52 ${ratio(goldDeep, w.mean).toFixed(2)}:1 against the mean`)
  })
  if (failed) { console.error('A label plate is below 4.5:1 for white or black text.'); process.exit(1) }
}
