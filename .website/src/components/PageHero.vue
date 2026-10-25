<script setup lang="ts">
defineProps<{ eyebrow: string; title: string; lore?: string }>()
</script>

<template>
  <header class="relative isolate overflow-hidden border-b border-seam">
    <div class="hero__sky" aria-hidden="true" />
    <div class="hero__river opacity-60" aria-hidden="true" />
    <div class="hero__vignette" aria-hidden="true" />
    <div class="relative mx-auto max-w-6xl px-4 sm:px-8 py-16 sm:py-24 text-center">
      <p class="eyebrow rise">{{ eyebrow }}</p>
      <h1 class="display frost-text rise rise-1 mt-4 text-[clamp(2.4rem,7vw,4.5rem)]">{{ title }}</h1>
      <p v-if="lore" class="lore rise rise-2 mt-5 text-[clamp(1.2rem,2.4vw,1.55rem)] text-bone/90 max-w-2xl mx-auto">{{ lore }}</p>
      <slot />
    </div>
  </header>
</template>
