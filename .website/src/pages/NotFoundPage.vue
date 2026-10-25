<script setup lang="ts">
import { RouterLink } from 'vue-router'
import PageHero from '../components/PageHero.vue'
</script>

<template>
  <PageHero eyebrow="404" title="Lost in the fog of war" lore="No scout has ever reported this place.">
    <div class="mt-10 flex flex-wrap justify-center gap-4">
      <RouterLink to="/" class="btn btn--frost">Return to base</RouterLink>
      <RouterLink to="/docs/" class="btn">Documentation</RouterLink>
    </div>
  </PageHero>
</template>
