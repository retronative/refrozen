// The home page's loading-screen intro as a deterministic timeline, kept free of Vue and the DOM so
// it can be tested on its own (scripts/test-intro.mjs).
//
// The visible progress follows a fixed cinematic curve over INTRO_MS, independent of how fast the
// assets arrive (from cache they are instant). Real loading only holds it: until the assets are
// ready the bar stops at HOLD_AT, and MAX_WAIT_MS caps that so a slow or failed asset never holds
// the intro. Each frame advances the timeline by at most MAX_STEP_MS, so a late first frame (the
// page hydrating) cannot make the bar jump, and progress never decreases.
export const INTRO_MS = 2400
export const HOLD_AT = 0.95
export const MAX_WAIT_MS = 4000
export const MAX_STEP_MS = 50

// After completion (all CSS, keyed on the hero's intro-complete class and timed by these values,
// passed in as custom properties so the timeline lives in one place):
// "The ancients are awake" shows for AWAKE_MS, then the bar fades out over BAR_FADE_MS while the
// download CTA fades in over CTA_FADE_MS from CTA_DELAY_MS, overlapping the bar's fade by
// BAR_FADE_MS - (CTA_DELAY_MS - AWAKE_MS). From the start: complete at 2.4 s, bar fades 3.2-3.6 s,
// CTA fades in 3.4-3.9 s. A skip or reduced motion shows the final state at once.
export const AWAKE_MS = 800
export const BAR_FADE_MS = 400
export const CTA_DELAY_MS = 1000
export const CTA_FADE_MS = 500

export const outroTimingStyle = {
  '--t-awake': `${AWAKE_MS}ms`,
  '--t-bar-fade': `${BAR_FADE_MS}ms`,
  '--t-cta-delay': `${CTA_DELAY_MS}ms`,
  '--t-cta-fade': `${CTA_FADE_MS}ms`,
}

export type IntroPhase = 'playing' | 'complete' | 'skipped'

export interface IntroState {
  progress: number
  phase: IntroPhase
}

// Plays once per page load: navigating back to the home page within the site shows the final state.
export const introSession = { played: false }

// Smoothstep: starts and lands gently, monotonic from 0 to 1.
export function cinematicProgress(elapsed: number): number {
  const t = Math.min(1, Math.max(0, elapsed / INTRO_MS))
  return t * t * (3 - 2 * t)
}

export function initialIntroState(skip: boolean): IntroState {
  return skip ? { progress: 1, phase: 'skipped' } : { progress: 0, phase: 'playing' }
}

export interface IntroOptions {
  reducedMotion: boolean
  assetsReady: Promise<unknown>
  onChange: (state: IntroState) => void
  frame: (callback: (now: number) => void) => number
  cancelFrame: (id: number) => void
}

export function createIntro(options: IntroOptions) {
  const state = initialIntroState(introSession.played || options.reducedMotion)
  let handle = 0
  let ready = false
  options.assetsReady.then(
    () => (ready = true),
    () => (ready = true),
  )

  const set = (progress: number, phase: IntroPhase) => {
    state.progress = progress
    state.phase = phase
    options.onChange({ ...state })
  }

  function start() {
    introSession.played = true
    if (state.phase !== 'playing') {
      options.onChange({ ...state })
      return
    }
    let elapsed = 0
    let waited = 0
    let last: number | null = null
    const step = (now: number) => {
      if (state.phase !== 'playing') return
      const dt = last === null ? 0 : Math.max(0, now - last)
      last = now
      elapsed += Math.min(dt, MAX_STEP_MS)
      waited += dt
      let target = cinematicProgress(elapsed)
      if (!ready && waited < MAX_WAIT_MS) target = Math.min(target, HOLD_AT)
      const progress = Math.max(state.progress, target)
      if (progress >= 1) {
        set(1, 'complete')
        return
      }
      set(progress, 'playing')
      handle = options.frame(step)
    }
    handle = options.frame(step)
  }

  function skip() {
    if (state.phase !== 'playing') return
    options.cancelFrame(handle)
    set(1, 'skipped')
  }

  function stop() {
    options.cancelFrame(handle)
  }

  return { state, start, skip, stop }
}
