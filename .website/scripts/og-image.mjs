// RETIRED: renders the old provisional Open Graph image (1200×630 PNG: the site's dawn/dusk
// river-split backdrop and an original stroke-drawn wordmark, no font involved). The published
// image is now the owner's artwork in public/og.jpg, so this script is kept for reference only:
// it has no npm script, needs an explicit output path and refuses to write into public/.
//   node scripts/og-image.mjs <output.png>
import { writeFileSync } from 'node:fs'
import { relative, resolve } from 'node:path'

const out = process.argv[2]
const publicDir = resolve(import.meta.dirname, '../public')
if (!out || !relative(publicDir, resolve(out)).startsWith('..')) {
  console.error('Usage: node scripts/og-image.mjs <output.png> (outside public/; public/og.jpg is the owner\'s image)')
  process.exit(1)
}
import { Resvg } from '@resvg/resvg-js'

const OW = 1200
const OH = 630

// Geometric capitals on a 100-unit cap height: [advance width, stroke path].
const GLYPHS = {
  A: [60, 'M0 100 L30 0 L60 100 M12 64 H48'],
  C: [58, 'M58 16 A44 50 0 1 0 58 84'],
  E: [48, 'M48 0 H0 V100 H48 M0 50 H38'],
  F: [46, 'M46 0 H0 V100 M0 50 H36'],
  I: [10, 'M5 0 V100'],
  L: [44, 'M0 0 V100 H44'],
  N: [58, 'M0 100 V0 L58 100 V0'],
  O: [72, 'M36 0 A36 50 0 1 0 36.01 0 Z'],
  P: [52, 'M0 100 V0 H30 A22 25 0 0 1 30 50 H0'],
  R: [56, 'M0 100 V0 H30 A22 25 0 0 1 30 50 H0 M22 50 L56 100'],
  S: [54, 'M52 14 C44 2 30 0 22 2 C6 6 2 22 10 34 C18 46 44 48 50 62 C58 80 44 98 26 98 C14 98 4 92 0 84'],
  T: [60, 'M0 0 H60 M30 0 V100'],
  V: [60, 'M0 0 L30 100 L60 0'],
  Z: [56, 'M2 0 H56 L2 100 H58'],
  ' ': [34, ''],
  M: [70, 'M0 100 V0 L35 70 L70 0 V100'],
  U: [56, 'M0 0 V64 A28 36 0 0 0 56 64 V0'],
  W: [84, 'M0 0 L20 100 L42 30 L64 100 L84 0'],
  '·': [20, 'M10 48 V52'],
}

function word(text, { x, y, size, tracking, stroke, colors }) {
  const scale = size / 100
  let cursor = 0
  const widths = [...text].map((ch) => GLYPHS[ch][0] + tracking)
  const total = widths.reduce((a, b) => a + b, 0) - tracking
  const start = x - (total * scale) / 2
  const parts = [...text].map((ch, i) => {
    const [, d] = GLYPHS[ch]
    const el = d
      ? `<path d="${d}" transform="translate(${(start + cursor * scale).toFixed(1)} ${y}) scale(${scale})" stroke="${colors(i)}" stroke-width="${stroke / scale}" fill="none" stroke-linecap="square" stroke-linejoin="miter"/>`
      : ''
    cursor += widths[i]
    return el
  })
  return parts.join('')
}


const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${OW}" height="${OH}" viewBox="0 0 ${OW} ${OH}">
<defs>
  <linearGradient id="split" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#10140e"/><stop offset=".496" stop-color="#0b0e12"/><stop offset=".504" stop-color="#0b0d17"/><stop offset="1" stop-color="#08091a"/></linearGradient>
  <radialGradient id="dawn" cx="0" cy="0" r="1"><stop offset="0" stop-color="#d6a85c" stop-opacity=".28"/><stop offset=".7" stop-color="#d6a85c" stop-opacity="0"/></radialGradient>
  <radialGradient id="dusk" cx="1" cy="1" r="1"><stop offset="0" stop-color="#6e60d2" stop-opacity=".3"/><stop offset=".7" stop-color="#6e60d2" stop-opacity="0"/></radialGradient>
  <radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".7"/></radialGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff3c8"/><stop offset=".5" stop-color="#f0d996"/><stop offset="1" stop-color="#b58f45"/></linearGradient>
  <linearGradient id="ice" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4fbff"/><stop offset="1" stop-color="#8fcaf0"/></linearGradient>
</defs>
<rect width="${OW}" height="${OH}" fill="url(#split)"/>
<rect width="${OW}" height="${OH}" fill="url(#dawn)"/>
<rect width="${OW}" height="${OH}" fill="url(#dusk)"/>
<path d="M${OW * 0.02} ${-OH * 0.5} L${OW * 0.98} ${OH * 1.5}" stroke="#9ad8ff" stroke-opacity=".45" stroke-width="1.5" transform="rotate(0)"/>
<rect width="${OW}" height="${OH}" fill="url(#vig)"/>
<rect x="12" y="12" width="${OW - 24}" height="${OH - 24}" fill="none" stroke="#d8b868" stroke-opacity=".45" stroke-width="1.5"/>
<path d="M${OW / 2 - 150} 118 H${OW / 2 - 22} M${OW / 2 + 22} 118 H${OW / 2 + 150}" stroke="#d8b868" stroke-opacity=".7" stroke-width="1.5"/>
<path d="M${OW / 2} 108 L${OW / 2 + 10} 118 L${OW / 2} 128 L${OW / 2 - 10} 118 Z" fill="#d8b868"/>
${word('REFROZEN', { x: OW / 2, y: 168, size: 112, tracking: 30, stroke: 11, colors: (i) => (i < 2 ? 'url(#ice)' : 'url(#gold)') })}
${word('NATIVE ON APPLE SILICON', { x: OW / 2, y: 330, size: 26, tracking: 26, stroke: 3.2, colors: () => '#ece6d8' })}
${word('NOT AN EMULATOR · NOT WINE', { x: OW / 2, y: 384, size: 18, tracking: 26, stroke: 2.4, colors: () => '#9ad8ff' })}
</svg>`

const png = new Resvg(svg, { fitTo: { mode: 'width', value: OW } }).render().asPng()
const file = resolve(out)
writeFileSync(file, png)
console.log(`Wrote ${file} (${png.length} bytes)`)
