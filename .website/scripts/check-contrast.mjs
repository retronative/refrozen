// WCAG contrast audit on rendered colours: each surface is composited from its CSS layer values
// (the lightest point text can sit on) and checked against the text colours used on it.

const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
const lin = (c) => ((c /= 255) <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
const lum = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
const ratio = (a, b) => {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p)
  return (x + 0.05) / (y + 0.05)
}
const over = (top, alpha, bottom) => top.map((c, i) => c * alpha + bottom[i] * (1 - alpha))

const text = {
  bone: hex('#ece6d8'), ash: hex('#a7afbc'), gold: hex('#d8b868'), goldBright: hex('#f0d996'),
  frost: hex('#9ad8ff'), dusk: hex('#b1a4f4'), verdant: hex('#a3d58c'), chatTime: hex('#7f8896'),
  ember: hex('#e59a5b'),
}
const abyss = hex('#06080c')
const panel = hex('#10151d')
// Brightest point of a stone panel: warm highlight + upper-left radial over the base.
const panelLit = over([255, 236, 200], 0.045, hex('#18202b'))
const wood = over([255, 220, 160], 0.1, hex('#3b2a19'))
const list = hex('#0b0e13')
const bannerWarm = over([214, 168, 92], 0.2, hex('#10140e'))
const bannerCold = over([110, 96, 210], 0.22, hex('#08091a'))
const tabSelected = over(hex('#d8b868'), 0.14, list)

const checks = [
  ['body text (bone) on page', text.bone, abyss, 4.5],
  ['muted text (ash) on page', text.ash, abyss, 4.5],
  ['muted text (ash) on lit stone', text.ash, panelLit, 4.5],
  ['body text (bone) on lit stone', text.bone, panelLit, 4.5],
  ['eyebrow (gold) on lit stone', text.gold, panelLit, 4.5],
  ['eyebrow (gold) on wood header', text.gold, wood, 4.5],
  ['heading (gold-bright) on wood header', text.goldBright, wood, 3],
  ['tab text (ash) on selection list', text.ash, list, 4.5],
  ['selected tab (gold-bright) on highlight', text.goldBright, tabSelected, 4.5],
  ['link (frost) on page', text.frost, abyss, 4.5],
  ['link (frost) on lit stone', text.frost, panelLit, 4.5],
  ['status (dusk) on lit stone', text.dusk, panelLit, 4.5],
  ['status (verdant) on lit stone', text.verdant, panelLit, 4.5],
  ['chat timestamp on chat log', text.chatTime, over([0, 0, 0], 0.55, abyss), 4.5],
  ['muted text (ash) on warm banner', text.ash, bannerWarm, 4.5],
  ['muted text (ash) on cold banner', text.ash, bannerCold, 4.5],
  // Installation guide: the tinted callouts at their strongest tint, the disabled download
  // button's lighter stripe and the gilded Next plate's top edge.
  ['install: unverified/danger (ember) on ember callout', text.ember, over(hex('#e59a5b'), 0.12, hex('#0d1118')), 4.5],
  ['install: body (bone) on ember callout', text.bone, over(hex('#e59a5b'), 0.12, hex('#0d1118')), 4.5],
  ['install: planned (dusk) on preview callout', text.dusk, over([110, 96, 210], 0.12, hex('#0d1118')), 4.5],
  ['install: muted (ash) on preview callout', text.ash, over([110, 96, 210], 0.12, hex('#0d1118')), 4.5],
  ['install: disabled button (ash) on stripe', text.ash, hex('#10151d'), 4.5],
  ['install: Next label (gold) on gilded plate', text.gold, hex('#4a3b22'), 4.5],
  ['install: Next text (bone) on gilded plate', text.bone, hex('#4a3b22'), 4.5],
  ['install: current step (gold-bright) on highlight', text.goldBright, over(hex('#d8b868'), 0.12, abyss), 4.5],
]

// Home hero and page banners (.hero__sky + .hero__river): the lightest points text can sit on
// are the warm and cold corners and the thin river line through the centre.
const riverLine = over([154, 216, 255], 0.32, hex('#0b0e12'))
const heroChecks = [
  ['hero lead text (bone) on warm corner', ratio(text.bone, bannerWarm), 4.5],
  ['hero lead text (bone) on river line', ratio(text.bone, riverLine), 4.5],
  ['hero eyebrow (gold) on warm corner', ratio(text.gold, bannerWarm), 4.5],
  ['hero loading label (ash) on plate', ratio(text.ash, over(hex('#0a0c11'), 0.9, riverLine)), 4.5],
  ['"Dawn" label (verdant) on banner', ratio(text.verdant, hex('#10140e')), 4.5],
  ['"Dusk" label (dusk) on cold corner', ratio(text.dusk, bannerCold), 4.5],
]

let failed = 0
console.log('WCAG contrast (minimum required in brackets):')
for (const [name, fg, bg, min] of checks) {
  const r = ratio(fg, bg)
  if (r < min) failed++
  console.log(`  ${r >= min ? '✓' : '✗'} ${r.toFixed(2).padStart(5)}:1 [${min}]  ${name}`)
}
for (const [name, r, min] of heroChecks) {
  if (r < min) failed++
  console.log(`  ${r >= min ? '✓' : '✗'} ${r.toFixed(2).padStart(5)}:1 [${min}]  ${name}`)
}
if (failed) {
  console.error(`\n${failed} contrast check(s) below WCAG AA.`)
  process.exit(1)
}
console.log('All measured text meets WCAG AA.')
