<script setup lang="ts">
// The hero artwork's responsive files (public/hero/), under the site's base path.
const heroBase = `${import.meta.env.BASE_URL}hero/`
const heroSet = (ext: string) =>
  [640, 960, 1280, 1920, 2560, 2880, 3840].map((w) => `${heroBase}hero-b-${w}.${ext} ${w}w`).join(', ')

import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import FrostField from '../components/FrostField.vue'
import Divider from '../components/Divider.vue'
import ChatLog from '../components/ChatLog.vue'
import Minimap from '../components/Minimap.vue'
import Glyph from '../components/Glyph.vue'
import LoadingBar from '../components/LoadingBar.vue'
import ReleaseCta from '../components/ReleaseCta.vue'
import { landmarks } from '../data/lanes'
import { milestone, status } from '../docs'
import { createIntro, initialIntroState, introSession, outroTimingStyle, type IntroState } from '../intro'

const hot = ref<string | null>(null)
const current = status.milestones.find((m) => m.state === 'in-progress')
const m5 = milestone('M5')

// The loading-screen entrance (timeline in ../intro.ts): plays once per page load, is skippable at
// once by the Skip control, a click/tap on the hero or a character key, and never captures Space,
// arrows, Tab or paging keys. Under reduced motion, or when the page is revisited within the site,
// it starts in its final state.
const NAV_KEYS = new Set(['Tab', 'Shift', 'Control', 'Alt', 'Meta', 'CapsLock', ' ', 'Spacebar', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'PageUp', 'PageDown', 'Home', 'End'])
const intro = ref<IntroState>(initialIntroState(introSession.played))
const introDone = computed(() => intro.value.phase !== 'playing')
let controller: ReturnType<typeof createIntro> | null = null

function finishIntro(moveFocus = false) {
  if (introDone.value) return
  controller?.skip()
  // The download button takes the place the loading bar had.
  if (moveFocus) requestAnimationFrame(() => document.querySelector<HTMLElement>('.hero-cta')?.focus())
}

// Real loading the bar waits on (up to a cap): the hero artwork decoding, on screens that show it,
// and the web fonts.
function heroArtReady(): Promise<void> {
  const img = document.querySelector<HTMLImageElement>('.hero__art img')
  if (!img || getComputedStyle(img.closest('picture') ?? img).display === 'none') return Promise.resolve()
  if (img.complete && img.naturalWidth > 0) return img.decode().catch(() => undefined)
  return new Promise((resolve) => {
    img.addEventListener('load', () => img.decode().catch(() => undefined).then(() => resolve()), { once: true })
    img.addEventListener('error', () => resolve(), { once: true })
  })
}

function onKey(event: KeyboardEvent) {
  if (introDone.value) return
  if (event.metaKey || event.ctrlKey || event.altKey || NAV_KEYS.has(event.key) || event.key.startsWith('F')) return
  if ((event.target as HTMLElement).closest('input, textarea, select, [contenteditable]')) return
  finishIntro()
}

function onHeroClick(event: MouseEvent) {
  if (!(event.target as HTMLElement).closest('a, button')) finishIntro()
}

onMounted(() => {
  controller = createIntro({
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    assetsReady: Promise.all([heroArtReady(), document.fonts ? document.fonts.ready : undefined]),
    onChange: (state) => (intro.value = state),
    frame: (callback) => requestAnimationFrame(callback),
    cancelFrame: (id) => cancelAnimationFrame(id),
  })
  controller.start()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  controller?.stop()
  window.removeEventListener('keydown', onKey)
})

const steps = [
  {
    numeral: 'I',
    title: 'Translate once',
    text: 'The game’s 32-bit x86 code, read from your own copy, is lifted to C++ and compiled to native arm64 — ahead of time, on your Mac.',
  },
  {
    numeral: 'II',
    title: 'Replace the realm',
    text: 'A native runtime on SDL3 stands in for Windows: windows and input, graphics, DirectSound and the game’s audio, files.',
  },
  {
    numeral: 'III',
    title: 'Run as a native',
    text: 'What launches is an ordinary Apple Silicon process. Nothing is interpreted underneath it.',
  },
]
</script>

<template>
  <div>
    <!-- The loading screen: dawn and dusk, divided by the river. -->
    <section class="hero" :class="{ 'intro-done': introDone, 'intro-complete': intro.phase === 'complete' }" :style="outroTimingStyle" aria-labelledby="hero-title" @click="onHeroClick">
      <div class="hero__sky" aria-hidden="true" />
      <div class="hero__river" aria-hidden="true" />
      <FrostField :count="12" />
      <!-- The broken bridge (AI-generated artwork, see the disclaimer). Screens from 768px; phones keep the
           backdrop above (an empty source, so nothing is downloaded) until a portrait composition exists. -->
      <picture class="hero__art">
        <source media="(max-width: 767px)" srcset="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==" />
        <source media="(min-width: 768px)" type="image/avif" :srcset="heroSet('avif')" sizes="100vw" />
        <source media="(min-width: 768px)" type="image/webp" :srcset="heroSet('webp')" sizes="100vw" />
        <img :src="`${heroBase}hero-b-1280.webp`" width="3840" height="2162" fetchpriority="high" decoding="async"
          alt="An ancient stone bridge broken in the middle over a river at dusk: a sunlit forest with ruins on the left, a blighted wasteland and a gothic citadel on the right" />
      </picture>
      <div class="hero__scrim" aria-hidden="true" />
      <div class="hero__vignette" aria-hidden="true" />

      <div class="hero__content relative z-10 mx-auto w-full max-w-5xl px-4 sm:px-8 py-20 text-center">
        <p class="eyebrow rise">An unofficial fan project &middot; Native arm64 macOS</p>
        <h1 id="hero-title" class="hero__title frost-text rise rise-1 mt-6">
          <span class="re">re</span>Frozen
        </h1>
        <p class="lore rise rise-2 mt-5 text-[clamp(1.35rem,3vw,2rem)] text-bone">
          The Frozen Throne, thawed for Apple Silicon.
        </p>
        <p class="rise rise-2 mx-auto mt-4 max-w-2xl text-[1.05rem] text-bone">
          A static recompilation of Warcraft III: The Frozen Throne 1.26a to native arm64 macOS, built for offline DotA.
          Not an emulator. Not Wine. No virtual machine, no JIT.
        </p>

        <div class="rise rise-3 mt-9 flex flex-wrap items-center justify-center gap-4">
          <RouterLink to="/docs/how-it-works/" class="btn btn--frost">How it works</RouterLink>
          <RouterLink to="/releases/" class="btn">Status and releases</RouterLink>
        </div>

        <div class="loading-plate mx-auto mt-12 flex max-w-md flex-col items-center gap-3">
          <!-- One reserved box: the loading bar, then the download button in the same place. -->
          <div class="hero-cta-slot">
            <LoadingBar
              :progress="intro.progress"
              :complete="intro.phase === 'complete'"
              :skipped="intro.phase === 'skipped'"
              label="Recompiling the ancients…"
              complete-label="The ancients are awake"
            />
            <ReleaseCta />
          </div>
          <div class="relative h-11 w-full">
            <button
              type="button"
              class="intro-skip absolute inset-x-0 mx-auto w-fit min-h-11 px-4 bg-transparent border border-seam font-display text-[.72rem] uppercase tracking-[.28em] text-ash hover:text-bone cursor-pointer"
              @click.stop="finishIntro(true)"
            >
              Skip intro
            </button>
          </div>
        </div>
      </div>

      <div class="pointer-events-none absolute inset-x-0 bottom-0 flex justify-between px-4 sm:px-8 pb-5 font-display text-[.7rem] uppercase tracking-[.3em]" aria-hidden="true">
        <span class="text-verdant">Dawn</span>
        <span class="text-dusk">Dusk</span>
      </div>
    </section>

    <!-- What it is -->
    <section id="chronicle" tabindex="-1" class="fog-edge relative mx-auto max-w-6xl px-4 sm:px-8 py-24 outline-none" aria-labelledby="what-title">
      <div class="section-head">
        <p class="eyebrow">Not an emulator</p>
        <h2 id="what-title" class="gilded">Recompiled, not imitated</h2>
        <p>
          An emulator pretends to be another computer while you play. reFrozen does the translation before the first creep wave:
          the code becomes native, and only a small, purpose-built runtime remains.
        </p>
      </div>

      <ol class="slab slab--rim chamfer grid list-none m-0 p-0 md:grid-cols-3">
        <li v-for="(s, i) in steps" :key="s.numeral" class="relative p-8 sm:p-10" :class="i > 0 ? 'border-t md:border-t-0 md:border-l border-white/5' : ''">
          <span class="display gilded block text-[2.6rem] leading-none" aria-hidden="true">{{ s.numeral }}</span>
          <h3 class="display mt-4 text-[1.25rem] text-bone">{{ s.title }}</h3>
          <p class="mt-3 text-ash m-0">{{ s.text }}</p>
        </li>
      </ol>

      <p class="mt-8 text-center text-[.8rem] uppercase tracking-[.32em] text-frost font-display">
        No Wine &nbsp;&middot;&nbsp; No VM &nbsp;&middot;&nbsp; No JIT
      </p>
    </section>

    <Divider />

    <!-- Status as chat -->
    <section class="mx-auto max-w-4xl px-4 sm:px-8 py-24" aria-labelledby="status-title">
      <div class="section-head">
        <p class="eyebrow">Game log</p>
        <h2 id="status-title" class="gilded">Where the march stands</h2>
        <p>
          Every milestone passes only when its gate is observed. {{ m5.id }}: a full local DotA match plays to the score screen.
          <template v-if="current">Now: {{ current.id }}, {{ current.title.toLowerCase() }}.</template>
        </p>
      </div>
      <ChatLog />
      <div class="mt-8 flex flex-wrap items-center justify-between gap-4">
        <p class="m-0 text-ash">
          <strong class="text-bone">{{ status.releaseHeadline }}.</strong> {{ status.releasePlanned }}.
        </p>
        <RouterLink to="/releases/" class="btn">Releases</RouterLink>
      </div>
    </section>

    <!-- The lane map -->
    <section class="fog-edge relative border-y border-seam bg-black/30 py-28" aria-labelledby="lanes-title">
      <div class="mx-auto max-w-6xl px-4 sm:px-8">
        <div class="section-head">
          <p class="eyebrow">Choose your lane</p>
          <h2 id="lanes-title" class="gilded">The map of this site</h2>
          <p>Three lanes, one river, two ancients. Pick a landmark.</p>
        </div>
        <div class="grid items-center gap-12 md:grid-cols-[minmax(0,26rem)_1fr]">
          <div class="minimap-frame mx-auto w-full max-w-[26rem]">
            <Minimap interactive :hot="hot" @hover="hot = $event" />
          </div>
          <nav aria-label="Site sections" class="legend">
            <ul class="list-none m-0 p-0">
              <li v-for="l in landmarks" :key="l.id">
                <RouterLink
                  :to="l.to"
                  :class="{ 'is-hot': hot === l.id }"
                  @mouseenter="hot = l.id"
                  @mouseleave="hot = null"
                  @focus="hot = l.id"
                  @blur="hot = null"
                >
                  <span
                    aria-hidden="true"
                    class="inline-block w-2.5 h-2.5 rotate-45 translate-y-[-1px]"
                    :class="l.side === 'sentinel' ? 'bg-verdant' : l.side === 'scourge' ? 'bg-dusk' : 'bg-frost'"
                  />
                  <span>
                    <span class="display text-[1.05rem]">{{ l.label }}</span>
                    <small>{{ l.hint }}</small>
                  </span>
                </RouterLink>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </section>

    <!-- Duality: what you bring, what is never shipped -->
    <section class="mx-auto max-w-6xl px-4 sm:px-8 py-24" aria-labelledby="pact-title">
      <div class="section-head">
        <p class="eyebrow">The pact</p>
        <h2 id="pact-title" class="gilded">Your copy. Your Mac. Nothing else.</h2>
        <p>reFrozen ships only its own tools. The game modules are forged on your Mac, from the installers you own.</p>
      </div>
      <div class="grid gap-0 md:grid-cols-2 slab chamfer overflow-hidden">
        <div class="relative p-8 sm:p-10 bg-[radial-gradient(90%_80%_at_0%_0%,rgba(163,213,140,.12),transparent_70%)]">
          <p class="eyebrow !text-verdant flex items-center gap-2"><Glyph name="shard" :size="16" /> You bring</p>
          <ul class="mt-5 space-y-3 list-none p-0 m-0 text-bone">
            <li>An Apple Silicon Mac with macOS 14 or later</li>
            <li>Your own Warcraft III: Reign of Chaos and The Frozen Throne installers and CD keys</li>
            <li>The official 1.26a patch</li>
            <li>The maps you want to play</li>
          </ul>
        </div>
        <div class="relative p-8 sm:p-10 border-t md:border-t-0 md:border-l border-white/5 bg-[radial-gradient(90%_80%_at_100%_100%,rgba(177,164,244,.12),transparent_70%)]">
          <p class="eyebrow !text-dusk flex items-center gap-2"><Glyph name="duel" :size="16" /> Never shipped</p>
          <ul class="mt-5 space-y-3 list-none p-0 m-0 text-bone">
            <li>Blizzard binaries or installers</li>
            <li>Recompiled game code, assets or maps</li>
            <li>CD keys</li>
            <li>iCCup components &mdash; or Wine</li>
          </ul>
        </div>
      </div>
      <p class="mt-8 text-center">
        <RouterLink to="/docs/getting-started/">Read Getting started</RouterLink>
        <span class="text-ash" aria-hidden="true"> &nbsp;&middot;&nbsp; </span>
        <RouterLink to="/faq/#is-it-legal">Is it legal?</RouterLink>
      </p>
    </section>
  </div>
</template>
