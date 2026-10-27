/// <reference types="vite/client" />

declare module 'virtual:docs' {
  export interface DocSection {
    id: string
    title: string
    html: string
  }
  export interface Doc {
    slug: string
    route: string
    title: string
    description: string
    order: number
    html: string
    intro: string
    sections: DocSection[]
  }
  export type MilestoneState = 'signed-off' | 'delegated' | 'in-progress' | 'future'
  export interface Milestone {
    id: string
    title: string
    state: MilestoneState
    stateText: string
    /** Inline HTML rendered from Markdown. */
    note: string
  }
  export interface ProjectStatus {
    releaseHeadline: string
    releasePlanned: string
    /** The published DMG (docs/status.md `release_url`), or null before the release: "Coming soon". */
    releaseUrl: string | null
    /** e.g. "v0.1.0" (`release_version`), set together with releaseUrl. */
    releaseVersion: string | null
    milestones: Milestone[]
    /** Inline HTML list items. */
    planned: string[]
    /** The release's known limitations. */
    known: string[]
    excluded: string[]
  }
  export const status: ProjectStatus
  const docs: Doc[]
  export default docs
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
