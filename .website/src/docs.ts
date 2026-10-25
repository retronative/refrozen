import docs, { status, type Doc, type Milestone, type MilestoneState } from 'virtual:docs'

export { docs, status }
export type { Doc, Milestone, MilestoneState }

export const stateLabel: Record<MilestoneState, string> = {
  'signed-off': 'Passed',
  delegated: 'Passed',
  'in-progress': 'In progress',
  future: 'Future',
}

export function milestone(id: string): Milestone {
  const m = status.milestones.find((x) => x.id === id)
  if (!m) throw new Error(`docs/status.md has no milestone ${id}`)
  return m
}

export function findDoc(slug: string): Doc | undefined {
  return docs.find((doc) => doc.slug === slug)
}

export function requireDoc(slug: string): Doc {
  const doc = findDoc(slug)
  if (!doc) throw new Error(`docs/${slug}.md is missing`)
  return doc
}
