<script setup lang="ts">
// Shared frame for a rendered document: hero, table of contents, prose.
import { RouterLink } from 'vue-router'
import PageHero from './PageHero.vue'
import Prose from './Prose.vue'
import type { Doc } from '../docs'

defineProps<{
  doc: Doc
  eyebrow: string
  art?: 'forge' | 'library' | 'portal' | 'tavern' | 'battlefield' | 'fog' | 'ranger' | 'scholar'
  artPosition?: string
}>()
</script>

<template>
  <div>
    <PageHero :eyebrow="eyebrow" :title="doc.title" :lore="doc.description" :art="art" :art-position="artPosition" />
    <div class="mx-auto grid max-w-6xl gap-12 px-4 sm:px-8 py-16 lg:grid-cols-[15rem_1fr]">
      <aside v-if="doc.sections.length > 1" class="lg:sticky lg:top-[calc(var(--header-h)+2rem)] self-start">
        <nav :aria-label="`On this page: ${doc.title}`">
          <p class="eyebrow mb-3">On this page</p>
          <ul class="list-none m-0 p-0 border-l border-seam">
            <li v-for="s in doc.sections" :key="s.id">
              <a :href="`#${s.id}`" class="block -ml-px border-l border-transparent py-1.5 pl-4 text-[.93rem] text-ash no-underline hover:border-gold hover:text-bone" v-html="s.title" />
            </li>
          </ul>
        </nav>
      </aside>
      <article class="min-w-0" :class="{ 'lg:col-span-2': doc.sections.length <= 1 }">
        <slot :doc="doc">
          <Prose :html="doc.html" />
        </slot>
        <p class="mt-16 border-t border-seam pt-6 text-[.9rem] text-ash">
          <RouterLink to="/docs/">&larr; All documentation</RouterLink>
        </p>
      </article>
    </div>
  </div>
</template>
