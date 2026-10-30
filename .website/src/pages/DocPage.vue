<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import DocLayout from '../components/DocLayout.vue'
import Prose from '../components/Prose.vue'
import { installPath } from '../data/release'
import { requireDoc } from '../docs'

const route = useRoute()
const doc = computed(() => requireDoc(String(route.params.slug)))
</script>

<template>
  <DocLayout :key="doc.slug" :doc="doc" eyebrow="Documentation" art="library" art-position="50% 45%">
    <p v-if="doc.slug === 'getting-started'" class="install-feature install-feature--inline mb-10">
      <span class="eyebrow">Installation guide</span>
      <span class="mt-1 block">
        Installing reFrozen 0.2.1 in five steps:
        <RouterLink :to="installPath()">the installation guide</RouterLink>.
      </span>
    </p>
    <Prose :html="doc.html" />
  </DocLayout>
</template>
