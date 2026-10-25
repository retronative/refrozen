// Regression tests for the home page intro timeline (src/intro.ts), on a simulated frame clock:
// progress is monotonic and smooth (no jump on a late first frame), it completes, a skip ends it at
// once, a remount within the page load does not replay it, and reduced motion starts in the final
// state. Run with Node's own test runner (Node strips the TypeScript types).
import assert from 'node:assert/strict'
import { beforeEach, test } from 'node:test'
import { HOLD_AT, INTRO_MS, MAX_STEP_MS, MAX_WAIT_MS, createIntro, introSession } from '../src/intro.ts'

// A frame clock the test advances by hand.
function clock() {
  let now = 0
  let next = 1
  const queue = new Map()
  return {
    frame: (callback) => (queue.set(next, callback), next++),
    cancelFrame: (id) => queue.delete(id),
    pending: () => queue.size,
    tick(ms) {
      now += ms
      const due = [...queue.values()]
      queue.clear()
      for (const callback of due) callback(now)
    },
  }
}

function setup({ reducedMotion = false, assetsReady = Promise.resolve() } = {}) {
  const c = clock()
  const states = []
  const intro = createIntro({ reducedMotion, assetsReady, onChange: (s) => states.push(s), ...c })
  return { c, states, intro }
}

const settle = () => new Promise((resolve) => setImmediate(resolve))
const run = (c, frames, ms = 16) => {
  for (let i = 0; i < frames; i++) c.tick(ms)
}

beforeEach(() => {
  introSession.played = false
})

test('progress starts at 0, rises monotonically and completes at 1', async () => {
  const { c, states, intro } = setup()
  await settle()
  assert.equal(intro.state.progress, 0)
  intro.start()
  run(c, Math.ceil(INTRO_MS / 16) + 5)
  const progress = states.map((s) => s.progress)
  for (let i = 1; i < progress.length; i++) assert.ok(progress[i] >= progress[i - 1], `frame ${i} went back`)
  assert.equal(states.at(-1).phase, 'complete')
  assert.equal(states.at(-1).progress, 1)
  assert.equal(states.filter((s) => s.phase === 'complete').length, 1, 'completes once')
  assert.equal(c.pending(), 0, 'no frames after completion')
})

test('the bar passes visibly through 25, 50 and 75 percent', async () => {
  const { c, states, intro } = setup()
  await settle()
  intro.start()
  run(c, Math.ceil(INTRO_MS / 16) + 5)
  const playing = states.filter((s) => s.phase === 'playing').map((s) => s.progress)
  for (const mark of [0.25, 0.5, 0.75]) assert.ok(playing.some((p) => Math.abs(p - mark) < 0.03), `no frame near ${mark}`)
  assert.ok(playing.length > 60, 'progress spans many frames')
})

test('a late first frame or a stalled frame does not make the bar jump', async () => {
  const { c, states, intro } = setup()
  await settle()
  intro.start()
  c.tick(300) // the first frame arrives late (hydration)
  assert.equal(states.at(-1).progress, 0)
  c.tick(16)
  c.tick(700) // a long stall mid-way
  const progress = states.map((s) => s.progress)
  const maxStep = Math.max(...progress.slice(1).map((p, i) => p - progress[i]))
  assert.ok(maxStep <= (1.5 * MAX_STEP_MS) / INTRO_MS + 1e-9, `step ${maxStep} too large`)
})

test('cached assets do not shorten the cinematic timeline', async () => {
  const { c, states, intro } = setup({ assetsReady: Promise.resolve() })
  await settle()
  intro.start()
  run(c, Math.floor((INTRO_MS * 0.5) / 16))
  assert.equal(states.at(-1).phase, 'playing')
  assert.ok(states.at(-1).progress < 0.6)
})

test('until the assets are ready the bar holds below 100%, then completes', async () => {
  let resolve
  const { c, states, intro } = setup({ assetsReady: new Promise((r) => (resolve = r)) })
  intro.start()
  run(c, Math.ceil(INTRO_MS / 16) + 20)
  assert.equal(states.at(-1).phase, 'playing')
  assert.ok(states.at(-1).progress <= HOLD_AT)
  resolve()
  await settle()
  run(c, 3)
  assert.equal(states.at(-1).phase, 'complete')
})

test('a slow asset never holds the intro beyond the cap', async () => {
  const { c, states, intro } = setup({ assetsReady: new Promise(() => {}) })
  intro.start()
  run(c, Math.ceil(MAX_WAIT_MS / 16) + 5)
  assert.equal(states.at(-1).phase, 'complete')
})

test('a skip ends the intro at once, in its final state', async () => {
  const { c, states, intro } = setup()
  await settle()
  intro.start()
  run(c, 20)
  intro.skip()
  assert.deepEqual(states.at(-1), { progress: 1, phase: 'skipped' })
  assert.equal(c.pending(), 0, 'no frames after a skip')
  intro.skip()
  run(c, 10)
  assert.equal(states.at(-1).phase, 'skipped')
  assert.equal(states.filter((s) => s.phase !== 'playing').length, 1, 'one final state')
})

test('a remount within the same page load does not replay the intro', async () => {
  const first = setup()
  first.intro.start()
  run(first.c, 30)
  first.intro.stop() // unmounted mid-intro
  const second = setup()
  assert.deepEqual(second.intro.state, { progress: 1, phase: 'skipped' })
  second.intro.start()
  assert.deepEqual(second.states.at(-1), { progress: 1, phase: 'skipped' })
  assert.equal(second.c.pending(), 0)
})

test('reduced motion starts in the final state and stays usable', async () => {
  const { c, states, intro } = setup({ reducedMotion: true })
  intro.start()
  assert.deepEqual(states.at(-1), { progress: 1, phase: 'skipped' })
  assert.equal(c.pending(), 0, 'no animation frames')
  intro.skip() // the skip control and keys stay harmless
  assert.equal(states.length, 1)
})
