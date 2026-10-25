<script setup lang="ts">
// FAQ content comes from docs/faq.md; each "## question" becomes a sealed tablet.
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PageHero from '../components/PageHero.vue'
import Prose from '../components/Prose.vue'
import { requireDoc } from '../docs'

const doc = requireDoc('faq')
const route = useRoute()
const opened = ref<Record<string, boolean>>({})

function openFromHash() {
  const id = decodeURIComponent(route.hash.slice(1))
  if (!id || !doc.sections.some((s) => s.id === id)) return
  opened.value[id] = true
  nextTick(() => document.getElementById(id)?.scrollIntoView({ block: 'start' }))
}

function onToggle(id: string, event: Event) {
  opened.value[id] = (event.target as HTMLDetailsElement).open
}

onMounted(openFromHash)
watch(() => route.hash, openFromHash)
</script>

<template>
  <div>
    <PageHero eyebrow="Ask the tavern keeper" title="FAQ" :lore="doc.description" art="scholar" art-position="50% 50%" />
    <section class="mx-auto max-w-3xl px-4 sm:px-8 py-16" aria-label="Questions and answers">
      <Prose v-if="doc.intro.trim()" :html="doc.intro" class="mb-8" />
      <details
        v-for="s in doc.sections"
        :id="s.id"
        :key="s.id"
        class="scroll-item"
        :open="opened[s.id]"
        @toggle="onToggle(s.id, $event)"
      >
        <summary>
          <h2 v-html="s.title" />
          <span class="chev" aria-hidden="true" />
        </summary>
        <Prose :html="s.html" />
      </details>
    </section>
  </div>
</template>
