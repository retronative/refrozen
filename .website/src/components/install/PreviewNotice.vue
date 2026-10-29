<script setup lang="ts">
import { RouterLink } from 'vue-router'
import StatusTag from './StatusTag.vue'
import { release } from '../../data/release'
</script>

<template>
  <aside class="install-preview" aria-labelledby="install-preview-title">
    <p id="install-preview-title" class="eyebrow">reFrozen {{ release.version }}</p>
    <p class="mt-2 mb-0">
      <strong>{{ release.headline }}.</strong> This guide installs the {{ release.released }} release. Its
      <a :href="release.page ?? undefined">release notes</a> list the known issues.
      <RouterLink to="/releases/">Release status</RouterLink>.
    </p>
    <ul class="install-legend" aria-label="Labels used in this guide">
      <li><StatusTag kind="verified" /> tested on the release</li>
      <li><StatusTag kind="unverified" /> not yet tested or measured for reFrozen</li>
    </ul>
  </aside>
</template>
