<script setup lang="ts">
// The home hero's download button. It links only to the published DMG named in docs/status.md
// (`release_url`, `release_version`); until then it is a disabled "Coming soon" plate that is not a
// link. scripts/check-dist.mjs fails the build if the built page disagrees with docs/status.md.
import { status } from '../docs'

const url = status.releaseUrl
const version = status.releaseVersion
</script>

<template>
  <a v-if="url" class="hero-cta" :href="url" data-release-cta="active" :data-release-version="version ?? undefined">
    <span class="hero-cta__plate">
      <span class="hero-cta__icon" aria-hidden="true">
        <svg viewBox="0 0 20 20" width="20" height="20"><path d="M10 1.5l2.4 6.1L10 18.5 7.6 7.6z" /><path d="M5 13.5h10" /></svg>
      </span>
      <span class="hero-cta__text">
        <span class="hero-cta__label">Download for Apple Silicon</span>
        <span class="hero-cta__meta">reFrozen {{ version }} &middot; macOS disk image</span>
      </span>
    </span>
  </a>
  <button v-else type="button" class="hero-cta hero-cta--soon" aria-disabled="true" aria-label="Download for Apple Silicon: coming soon" data-release-cta="soon" @click.prevent>
    <span class="hero-cta__plate">
      <span class="hero-cta__text">
        <span class="hero-cta__label">Coming soon</span>
        <span class="hero-cta__meta">Download for Apple Silicon</span>
      </span>
    </span>
  </button>
</template>
