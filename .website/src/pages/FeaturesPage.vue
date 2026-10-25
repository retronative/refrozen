<script setup lang="ts">
// A campaign-style panel: a selection list (tabs) and a detail plate. Every plate is in the
// prerendered HTML; without JavaScript they are all shown in sequence.
import { nextTick, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PageHero from '../components/PageHero.vue'
import CarvedFrame from '../components/CarvedFrame.vue'
import Glyph from '../components/Glyph.vue'
import { features } from '../data/features'
import { milestone, stateLabel } from '../docs'

const items = features.map((f) => ({ ...f, status: milestone(f.milestone) }))
const active = ref(0)
const tabs = ref<HTMLButtonElement[]>([])

function select(i: number, focus = false) {
  active.value = (i + items.length) % items.length
  if (focus) nextTick(() => tabs.value[active.value]?.focus())
}

function onKey(event: KeyboardEvent, i: number) {
  const moves: Record<string, number> = { ArrowDown: i + 1, ArrowRight: i + 1, ArrowUp: i - 1, ArrowLeft: i - 1, Home: 0, End: items.length - 1 }
  if (!(event.key in moves)) return
  event.preventDefault()
  select(moves[event.key], true)
}

const pillClass = (state: string) => (state === 'in-progress' ? 'text-frost' : state === 'future' ? 'text-dusk' : 'text-verdant')
</script>

<template>
  <div>
    <PageHero
      eyebrow="The tavern board"
      title="Features"
      lore="Choose a scroll from the board. Each states what already answers the call on Apple Silicon, and which milestone proved it."
    />

    <section class="fog-edge mx-auto max-w-6xl px-4 sm:px-8 py-24" aria-labelledby="campaign-title">
      <CarvedFrame>
        <div class="campaign__title wood">
          <p class="eyebrow">Inscribed at the tavern</p>
          <h2 id="campaign-title" class="display gilded mt-1 text-[clamp(1.5rem,3vw,2.1rem)]">What runs natively</h2>
        </div>
        <div class="gilt-line" aria-hidden="true" />

        <div class="grid md:grid-cols-[minmax(15rem,20rem)_1fr]">
          <div class="campaign__list" role="tablist" aria-orientation="vertical" aria-label="Features">
            <button
              v-for="(f, i) in items"
              :id="`tab-${f.id}`"
              :key="f.id"
              ref="tabs"
              type="button"
              role="tab"
              class="campaign__tab"
              :aria-selected="active === i"
              :aria-controls="`panel-${f.id}`"
              :tabindex="active === i ? 0 : -1"
              @click="select(i)"
              @keydown="onKey($event, i)"
            >
              <span class="campaign__socket"><Glyph :name="f.glyph" :size="18" /></span>
              <span>
                <span class="block font-display text-[.92rem] font-semibold tracking-[.04em]">{{ f.title }}</span>
                <span v-if="f.status.state === 'in-progress' || f.status.state === 'future'" class="mt-0.5 block text-[.72rem] uppercase tracking-[.2em]" :class="pillClass(f.status.state)">
                  {{ stateLabel[f.status.state] }}
                </span>
              </span>
            </button>
          </div>

          <div class="relative min-w-0 bg-[radial-gradient(90%_70%_at_20%_0%,rgba(216,184,104,.07),transparent_70%)]">
            <article
              v-for="(f, i) in items"
              :id="`panel-${f.id}`"
              :key="f.id"
              role="tabpanel"
              :aria-labelledby="`tab-${f.id}`"
              tabindex="0"
              class="campaign__panel campaign__plate"
              :class="{ 'is-active': active === i }"
            >
              <div class="flex flex-wrap items-center gap-8">
                <span class="campaign__emblem shrink-0"><Glyph :name="f.glyph" :size="34" /></span>
                <div class="min-w-0">
                  <p class="eyebrow">{{ f.status.id }} &middot; {{ f.status.title }}</p>
                  <h3 class="display mt-2 text-[clamp(1.5rem,3vw,2.2rem)] text-bone">{{ f.title }}</h3>
                </div>
              </div>
              <div class="gilt-line my-7 max-w-md opacity-60" aria-hidden="true" />
              <p class="m-0 max-w-[58ch] text-[1.08rem] text-bone/90">{{ f.text }}</p>
              <p class="mt-6 mb-0 text-[.9rem] text-ash">
                Milestone state:
                <span class="status-pill !ml-1" :class="pillClass(f.status.state)">{{ f.status.stateText }}</span>
              </p>
            </article>
          </div>
        </div>
      </CarvedFrame>

      <p class="mt-14 text-center text-ash">
        Online play is not part of the first release. See
        <RouterLink to="/compatibility/">Compatibility</RouterLink> and <RouterLink to="/releases/">Releases</RouterLink>.
      </p>
    </section>
  </div>
</template>
