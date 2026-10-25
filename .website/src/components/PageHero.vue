<script setup lang="ts">
// Page banner. With `art`, a responsive background painting (public/banners/) sits behind the
// title under a scrim that keeps the text readable; it is decorative (the title carries the
// meaning). `artPosition` picks the crop (CSS object-position).
const props = defineProps<{
  eyebrow: string
  title: string
  lore?: string
  art?: 'forge' | 'library' | 'portal' | 'tavern' | 'battlefield' | 'fog' | 'ranger' | 'scholar' | 'candlelit' | 'icegate'
  artPosition?: string
}>()
const base = `${import.meta.env.BASE_URL}banners/`
const set = (ext: string) => [640, 1280, 1920].map((w) => `${base}${props.art}-${w}.${ext} ${w}w`).join(', ')
</script>

<template>
  <header class="page-hero relative isolate overflow-hidden border-b border-seam" :class="{ 'page-hero--art': art }">
    <div class="hero__sky" aria-hidden="true" />
    <picture v-if="art" class="page-hero__art" aria-hidden="true">
      <source type="image/avif" :srcset="set('avif')" sizes="100vw" />
      <source type="image/webp" :srcset="set('webp')" sizes="100vw" />
      <img :src="`${base}${art}-1280.webp`" alt="" width="1920" height="1080" decoding="async" fetchpriority="high"
        :style="{ objectPosition: artPosition ?? '50% 50%' }" />
    </picture>
    <div v-if="art" class="page-hero__scrim" aria-hidden="true" />
    <div v-else class="hero__river opacity-60" aria-hidden="true" />
    <div class="hero__vignette" aria-hidden="true" />
    <div class="relative mx-auto max-w-6xl px-4 sm:px-8 py-16 sm:py-24 text-center">
      <p class="eyebrow rise">{{ eyebrow }}</p>
      <h1 class="display frost-text rise rise-1 mt-4 text-[clamp(2.4rem,7vw,4.5rem)]">{{ title }}</h1>
      <p v-if="lore" class="lore rise rise-2 mt-5 text-[clamp(1.2rem,2.4vw,1.55rem)] text-bone/90 max-w-2xl mx-auto">{{ lore }}</p>
      <slot />
    </div>
  </header>
</template>
