<script setup lang="ts">
import { RouterView } from 'vue-router'
import SiteHeader from './components/SiteHeader.vue'
import SiteFooter from './components/SiteFooter.vue'
</script>

<template>
  <div class="world">
    <div class="night-wash" aria-hidden="true" />
    <a class="skip-link" href="#main">Skip to content</a>
    <SiteHeader />
    <main id="main" tabindex="-1" class="flex-1 outline-none">
      <RouterView />
    </main>
    <SiteFooter />
  </div>
</template>
