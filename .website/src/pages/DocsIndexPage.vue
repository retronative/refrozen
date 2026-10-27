<script setup lang="ts">
import { RouterLink } from 'vue-router'
import PageHero from '../components/PageHero.vue'
import { docs } from '../docs'
import { installPath } from '../data/release'

const numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
</script>

<template>
  <div>
    <PageHero eyebrow="The library" title="Documentation" lore="Read before you march." art="library" art-position="50% 45%" />
    <section class="mx-auto max-w-4xl px-4 sm:px-8 py-20" aria-labelledby="docs-list-title">
      <h2 id="docs-list-title" class="sr-only">All documents</h2>
      <RouterLink :to="installPath()" class="install-feature group mb-10 no-underline">
        <span class="eyebrow">Installation guide</span>
        <span class="display mt-2 block text-[1.4rem] text-bone group-hover:text-gold-bright transition-colors">Installing reFrozen, step by step</span>
        <span class="mt-1 block text-ash text-[.97rem]">Installing reFrozen 0.1.0: download, Applications, first launch, preparing your own game and playing.</span>
      </RouterLink>
      <ol class="slab slab--rim list-none m-0 p-0">
        <li v-for="(doc, i) in docs" :key="doc.slug" class="border-t border-white/5 first:border-0">
          <RouterLink :to="doc.route" class="group grid grid-cols-[3.5rem_1fr_auto] items-center gap-4 px-6 sm:px-8 py-7 no-underline text-bone hover:bg-white/[.02]">
            <span class="display gilded text-[1.8rem]" aria-hidden="true">{{ numerals[i] }}</span>
            <span>
              <span class="display block text-[1.25rem] group-hover:text-gold-bright transition-colors">{{ doc.title }}</span>
              <span class="mt-1 block text-ash text-[.97rem]">{{ doc.description }}</span>
            </span>
            <span class="text-gold transition-transform duration-300 group-hover:translate-x-1" aria-hidden="true">&rarr;</span>
          </RouterLink>
        </li>
      </ol>
    </section>
  </div>
</template>
