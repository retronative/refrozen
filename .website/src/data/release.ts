// The release the installation guide describes. There is no release yet: every value that only a
// published, tested release can supply is null and shown as "to be announced". Fill these in from
// the published release, together with docs/getting-started.md, when it ships. The headline text
// comes from docs/status.md, the single status source.
import { status } from '../docs'

export const TBA = 'To be announced'

export const release = {
  /** "No releases yet" while nothing is published (docs/status.md front matter). */
  headline: status.releaseHeadline,
  /** "v0.1.0 (offline) planned" (docs/status.md front matter). */
  planned: status.releasePlanned,
  published: false,
  version: null as string | null,
  tag: null as string | null,
  page: null as string | null,
  dmg: {
    name: null as string | null,
    url: null as string | null,
    sha256: null as string | null,
  },
  minMacos: null as string | null,
  diskSpace: null as string | null,
  buildTime: null as string | null,
}

// The guide's steps, in order: one prerendered page each at /docs/installation/<slug>/.
export const installSteps = [
  {
    slug: 'step-1',
    title: 'Download reFrozen',
    short: 'Download',
    description: 'Step 1 of 5 of the planned reFrozen installation (preview): what you will need, and the download once v0.1.0 is released.',
  },
  {
    slug: 'step-2',
    title: 'Move reFrozen to Applications',
    short: 'Install',
    description: 'Step 2 of 5 of the planned reFrozen installation (preview): open the disk image and drag reFrozen to Applications.',
  },
  {
    slug: 'step-3',
    title: 'Open it for the first time',
    short: 'First launch',
    description: 'Step 3 of 5 of the planned reFrozen installation (preview): the first launch, and what to do if macOS blocks the app.',
  },
  {
    slug: 'step-4',
    title: 'Prepare Warcraft III',
    short: 'Prepare the game',
    description: 'Step 4 of 5 of the planned reFrozen installation (preview): your own installers are checked, then the game is built on your Mac.',
  },
  {
    slug: 'step-5',
    title: 'Play',
    short: 'Play',
    description: 'Step 5 of 5 of the planned reFrozen installation (preview): offline play, controls, troubleshooting and uninstalling.',
  },
] as const

export type InstallStep = (typeof installSteps)[number]

export const installPath = (step?: InstallStep) => `/docs/installation/${step ? `${step.slug}/` : ''}`
