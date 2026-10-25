<script setup lang="ts">
import { RouterLink } from 'vue-router'
import BrandMark from './BrandMark.vue'
import Divider from './Divider.vue'
</script>

<template>
  <footer class="relative mt-auto border-t border-seam bg-black/60">
    <div class="mx-auto max-w-6xl px-4 sm:px-8 py-14">
      <Divider class="mb-10" />
      <div class="grid gap-10 md:grid-cols-[1.3fr_1fr_1fr]">
        <div>
          <div class="flex items-center gap-3">
            <BrandMark :size="30" />
            <span class="display text-lg"><span class="lore text-frost">re</span>Frozen</span>
          </div>
          <p class="mt-4 text-ash text-[.95rem] max-w-md">
            A native Apple Silicon recompilation of Warcraft III: The Frozen Throne 1.26a, for offline DotA.
            Not an emulator. Not Wine.
          </p>
        </div>
        <nav aria-label="Footer">
          <p class="eyebrow mb-3">The map</p>
          <ul class="list-none m-0 p-0 space-y-1.5 text-[.95rem]">
            <li><RouterLink to="/features/">Features</RouterLink></li>
            <li><RouterLink to="/screenshots/">Screenshots</RouterLink></li>
            <li><RouterLink to="/docs/">Documentation</RouterLink></li>
            <li><RouterLink to="/compatibility/">Compatibility</RouterLink></li>
            <li><RouterLink to="/faq/">FAQ</RouterLink></li>
            <li><RouterLink to="/releases/">Releases</RouterLink></li>
          </ul>
        </nav>
        <div>
          <p class="eyebrow mb-3">Fine print</p>
          <ul class="list-none m-0 p-0 space-y-1.5 text-[.95rem]">
            <li><RouterLink to="/docs/disclaimer/">Disclaimer and credits</RouterLink></li>
            <li><RouterLink to="/docs/getting-started/">Getting started</RouterLink></li>
            <li><RouterLink to="/docs/how-it-works/">How it works</RouterLink></li>
          </ul>
        </div>
      </div>

      <div class="mt-12 border border-gold/30 bg-black/50 p-5 text-[.9rem] leading-relaxed text-ash" role="note" aria-label="Disclaimer">
        <p class="m-0">
          <strong class="text-bone">reFrozen is an unofficial fan project. It is not affiliated with, endorsed by or sponsored by
          Blizzard Entertainment, Inc.</strong> Warcraft and The Frozen Throne are trademarks of Blizzard Entertainment, Inc. and
          are used only to describe the game. DotA Allstars is a community map by its respective authors. All trademarks belong
          to their owners.
        </p>
        <p class="mt-3 mb-0">
          No game files are included or distributed. You need your own legally obtained copy of Warcraft III: Reign of Chaos and
          The Frozen Throne. All artwork on this site is original.
        </p>
      </div>
    </div>
  </footer>
</template>
