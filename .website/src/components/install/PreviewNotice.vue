<script setup lang="ts">
import { RouterLink } from 'vue-router'
import StatusTag from './StatusTag.vue'
import { release } from '../../data/release'
</script>

<template>
  <aside class="install-preview" aria-labelledby="install-preview-title">
    <p id="install-preview-title" class="eyebrow">Preview of the planned flow</p>
    <p class="mt-2 mb-0">
      <strong>{{ release.headline }}.</strong> This guide shows how installing {{ release.planned.replace(/ planned$/, '') }} is
      meant to work. Nothing can be downloaded yet, and the steps will be confirmed or corrected before the release.
      <RouterLink to="/releases/">Follow the release status</RouterLink>.
    </p>
    <ul class="install-legend" aria-label="Labels used in this guide">
      <li><StatusTag kind="verified" /> works in reFrozen today</li>
      <li><StatusTag kind="planned" /> designed, not built yet</li>
      <li><StatusTag kind="unverified" /> not yet tested or measured for reFrozen</li>
    </ul>
  </aside>
</template>
