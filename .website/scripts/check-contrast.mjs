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
  bone: hex('#ece6d8'), ash: hex('#a7afbc'), gold: hex('#d4ae7a'), goldBright: hex('#eed2a7'),
  frost: hex('#88d3f9'), dusk: hex('#b1a4f4'), verdant: hex('#a3d58c'), chatTime: hex('#7f8896'),
  ember: hex('#e59a5b'),
}
// Non-text UI colours (WCAG 1.4.11: 3:1 against the adjacent surface).
const ui = { goldDeep: hex('#ab7f52'), ice: hex('#6bc4f4') }
const abyss = hex('#05080e')
const slab = hex('#0b121b')
// Brightest point of a stone panel: warm highlight + upper-left radial over the base.
const panelLit = over([255, 236, 200], 0.045, hex('#152030'))
const wood = over([255, 220, 160], 0.1, hex('#3b2a19'))
const list = hex('#09101a')
const bannerWarm = over([214, 168, 92], 0.2, hex('#10140e'))
const bannerCold = over([110, 96, 210], 0.22, hex('#08091a'))
const tabSelected = over(hex('#d4ae7a'), 0.14, list)
// Status pills: an 8% tint of their own colour over lit stone.
const pill = (c) => over(c, 0.08, panelLit)
// Frost button face (top of its gradient, hover state).
const frostButton = hex('#183150')

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
  ['install: unverified/danger (ember) on ember callout', text.ember, over(hex('#e59a5b'), 0.12, slab), 4.5],
  ['install: body (bone) on ember callout', text.bone, over(hex('#e59a5b'), 0.12, slab), 4.5],
  ['install: planned (dusk) on preview callout', text.dusk, over([110, 96, 210], 0.12, slab), 4.5],
  ['install: muted (ash) on preview callout', text.ash, over([110, 96, 210], 0.12, slab), 4.5],
  ['install: disabled button (ash) on stripe', text.ash, hex('#0d151f'), 4.5],
  ['install: Next label (gold) on gilded plate', text.gold, hex('#563b25'), 4.5],
  ['install: Next text (bone) on gilded plate', text.bone, hex('#563b25'), 4.5],
  ['install: current step (gold-bright) on highlight', text.goldBright, over(hex('#d4ae7a'), 0.12, abyss), 4.5],
  // Icon-language states: tinted status pills, buttons, the focus ring and ornaments.
  ['status pill (verdant) on its tint', text.verdant, pill(text.verdant), 4.5],
  ['status pill (frost) on its tint', text.frost, pill(text.frost), 4.5],
  ['status pill (dusk) on its tint', text.dusk, pill(text.dusk), 4.5],
  ['frost button label (bone) on hover face', text.bone, frostButton, 4.5],
  ['button label (bone) on stone button hover', text.bone, hex('#1e2d42'), 4.5],
  ['UI: focus ring (frost) on page', text.frost, abyss, 3],
  ['UI: focus ring (frost) on frost button', text.frost, frostButton, 3],
  ['UI: ornament gold (gold-deep) on page', ui.goldDeep, abyss, 3],
  ['UI: ornament gold (gold-deep) on lit stone', ui.goldDeep, panelLit, 3],
  ['UI: ice ornament on page', ui.ice, abyss, 3],
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
