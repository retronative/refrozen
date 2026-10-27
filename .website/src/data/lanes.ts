// Landmarks on the original minimap motif, each leading to a section of the site.
import { SHOW_SCREENSHOTS } from './flags'

export interface Landmark {
  id: string
  to: string
  label: string
  hint: string
  x: number
  y: number
  side: 'sentinel' | 'scourge' | 'river'
}

const allLandmarks: Landmark[] = [
  { id: 'releases', to: '/releases/', label: 'Releases', hint: 'Where every run begins: status and reFrozen 0.1.0.', x: 30, y: 170, side: 'sentinel' },
  { id: 'features', to: '/features/', label: 'Features', hint: 'Top lane: what already runs natively.', x: 22, y: 60, side: 'sentinel' },
  { id: 'docs', to: '/docs/', label: 'Documentation', hint: 'Mid, across the river: how it works.', x: 100, y: 100, side: 'river' },
  { id: 'screenshots', to: '/screenshots/', label: 'Screenshots', hint: 'The rune spot: plates awaiting approval.', x: 62, y: 66, side: 'river' },
  { id: 'compatibility', to: '/compatibility/', label: 'Compatibility', hint: 'Bottom lane: versions, maps and Macs.', x: 140, y: 178, side: 'scourge' },
  { id: 'faq', to: '/faq/', label: 'FAQ', hint: 'The far throne: every question answered.', x: 170, y: 30, side: 'scourge' },
]

export const landmarks = allLandmarks.filter((l) => SHOW_SCREENSHOTS || l.id !== 'screenshots')
