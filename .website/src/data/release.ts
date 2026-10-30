// The release the installation guide describes: reFrozen 0.2.1, published 30 October 2026. The
// values come from the published release and its tests, as docs/getting-started.md gives them. The
// headline text comes from docs/status.md, the single status source.
import { status } from '../docs'

export const TBA = 'To be announced'

export const release = {
  /** The release headline (docs/status.md front matter). */
  headline: status.releaseHeadline,
  /** The line under the headline (docs/status.md front matter). */
  planned: status.releasePlanned,
  published: true,
  version: status.releaseVersion,
  tag: status.releaseVersion,
  released: '30 October 2026' as string | null,
  page: `https://github.com/retronative/refrozen/releases/tag/${status.releaseVersion}` as string | null,
  dmg: {
    name: 'reFrozen-0.2.1.dmg' as string | null,
    url: status.releaseUrl,
    sha256: '576a1e5836251c23b9751c7dded8922faf280c81de4f56b0fae820990a47a3cc' as string | null,
  },
  minMacos: 'macOS 14' as string | null,
  diskSpace: 'About 2.5 GB free during setup; about 1.2 GB once set up' as string | null,
  buildTime: 'About 3 minutes on an M5, about 5½ minutes on an M1' as string | null,
}

// The guide's steps, in order: one prerendered page each at /docs/installation/<slug>/.
export const installSteps = [
  {
    slug: 'step-1',
    title: 'Download reFrozen',
    short: 'Download',
    description: 'Step 1 of 5 of installing reFrozen 0.2.1: what you will need, the download and its checksum.',
  },
  {
    slug: 'step-2',
    title: 'Move reFrozen to Applications',
    short: 'Install',
    description: 'Step 2 of 5 of installing reFrozen 0.2.1: open the disk image and drag reFrozen to Applications.',
  },
  {
    slug: 'step-3',
    title: 'Open it for the first time',
    short: 'First launch',
    description: 'Step 3 of 5 of installing reFrozen 0.2.1: the first launch, and allowing the app when macOS blocks it.',
  },
  {
    slug: 'step-4',
    title: 'Prepare Warcraft III',
    short: 'Prepare the game',
    description: 'Step 4 of 5 of installing reFrozen 0.2.1: your own installers are checked, then the game is built on your Mac.',
  },
  {
    slug: 'step-5',
    title: 'Play',
    short: 'Play',
    description: 'Step 5 of 5 of installing reFrozen 0.2.1: offline and LAN play, controls, troubleshooting and uninstalling.',
  },
] as const

export type InstallStep = (typeof installSteps)[number]

export const installPath = (step?: InstallStep) => `/docs/installation/${step ? `${step.slug}/` : ''}`
