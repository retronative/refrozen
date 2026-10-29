<script setup lang="ts">
// Rendered from docs/status.md: release headline, scope lists and the milestone log.
import PageHero from '../components/PageHero.vue'
import ChatLog from '../components/ChatLog.vue'
import Divider from '../components/Divider.vue'
import Prose from '../components/Prose.vue'
import { requireDoc, status } from '../docs'

const doc = requireDoc('status')
const releasesSection = doc.sections.find((s) => s.id === 'releases')
// The section's first paragraph is the release summary; the lists are rendered as columns below.
const summary = releasesSection?.html.split(/<h3 /)[0] ?? ''
const outro = releasesSection?.html.split(/<\/ul>\n?/).pop() ?? ''
// The lists are headed by the current release (docs/status.md `release_version`), e.g. "In v0.2.0".
const version = status.releaseVersion
const versionId = (version ?? '').replace(/\./g, '')
</script>

<template>
  <div>
    <PageHero eyebrow="The armory" title="Releases" lore="The gates are open." art="forge" art-position="55% 55%" />

    <section class="mx-auto max-w-4xl px-4 sm:px-8 py-20" aria-labelledby="releases">
      <div class="panel panel--carved relative overflow-hidden p-8 sm:p-12 text-center">
        <p class="eyebrow relative">Status</p>
        <h2 id="releases" class="display frost-text relative mt-3 text-[clamp(1.8rem,4.5vw,2.8rem)]">{{ status.releaseHeadline }}</h2>
        <p class="lore relative mt-3 text-[1.4rem] text-bone">{{ status.releasePlanned }}</p>
        <Prose :html="summary" class="relative mx-auto mt-5 text-ash [&_strong]:text-bone" />
      </div>

      <div class="mt-16 grid gap-10 md:grid-cols-2">
        <div>
          <h3 :id="`in-${versionId}`" class="eyebrow !text-verdant">In {{ version }}</h3>
          <ul class="mt-5 list-none space-y-3 p-0 m-0">
            <li v-for="item in status.planned" :key="item" class="grid grid-cols-[1rem_1fr] gap-3">
              <span class="mt-[.55em] h-2 w-2 rotate-45 bg-verdant" aria-hidden="true" />
              <span v-html="item" />
            </li>
          </ul>
        </div>
        <div>
          <h3 :id="`not-part-of-${versionId}`" class="eyebrow !text-dusk">Not part of {{ version }}</h3>
          <ul class="mt-5 list-none space-y-3 p-0 m-0">
            <li v-for="item in status.excluded" :key="item" class="grid grid-cols-[1rem_1fr] gap-3">
              <span class="mt-[.55em] h-2 w-2 rotate-45 bg-dusk" aria-hidden="true" />
              <span v-html="item" />
            </li>
          </ul>
        </div>
      </div>

      <div class="mt-12">
        <h3 id="known-limitations" class="eyebrow !text-ember">Known issues in {{ version }}</h3>
        <ul class="mt-5 list-none space-y-3 p-0 m-0">
          <li v-for="item in status.known" :key="item" class="grid grid-cols-[1rem_1fr] gap-3">
            <span class="mt-[.55em] h-2 w-2 rotate-45 bg-ember" aria-hidden="true" />
            <span v-html="item" />
          </li>
        </ul>
      </div>

      <Prose :html="outro" class="mt-12 border-l-2 border-gold/50 pl-4 text-ash" />
    </section>

    <Divider />

    <section class="mx-auto max-w-4xl px-4 sm:px-8 py-20" aria-labelledby="milestones">
      <div class="section-head">
        <p class="eyebrow">Game log</p>
        <h2 id="milestones" class="gilded">Milestones</h2>
        <Prose :html="doc.intro" class="mx-auto text-ash" />
      </div>
      <ChatLog />
    </section>
  </div>
</template>
