<script setup lang="ts">
import { RouterLink } from 'vue-router'
import BrandMark from './BrandMark.vue'
import Divider from './Divider.vue'
import { SHOW_SCREENSHOTS } from '../data/flags'
import { ISSUES_URL, ORG, REPO_URL } from '../data/links'
</script>

<template>
  <footer class="relative mt-auto border-t border-seam bg-black/60">
    <div class="mx-auto max-w-6xl px-4 sm:px-8 py-14">
      <Divider class="mb-10" />
      <div class="grid gap-10 md:grid-cols-[1.3fr_1fr_1fr]">
        <div>
          <div class="flex items-center gap-3">
            <BrandMark :size="36" />
            <span class="display text-lg"><span class="lore text-frost">re</span>Frozen</span>
          </div>
          <p class="mt-4 text-ash text-[.95rem] max-w-md">
            A native Apple Silicon recompilation of Warcraft III: The Frozen Throne 1.26a, for offline DotA.
            Not an emulator. Not Wine.
          </p>
          <ul class="list-none m-0 mt-4 p-0 flex flex-wrap gap-x-5 gap-y-1.5 text-[.95rem]">
            <li>
              <a :href="REPO_URL" class="inline-flex items-center gap-2">
                <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
                </svg>
                Source on GitHub
              </a>
            </li>
            <li><a :href="ISSUES_URL" aria-label="Issues on GitHub">Issues</a></li>
          </ul>
          <p class="mt-3 mb-0 text-ash text-[.9rem]">A <a :href="ORG.url">{{ ORG.name }}</a> project.</p>
        </div>
        <nav aria-label="Footer">
          <p class="eyebrow mb-3">The map</p>
          <ul class="list-none m-0 p-0 space-y-1.5 text-[.95rem]">
            <li><RouterLink to="/features/">Features</RouterLink></li>
            <li v-if="SHOW_SCREENSHOTS"><RouterLink to="/screenshots/">Screenshots</RouterLink></li>
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
          The Frozen Throne. Original artwork, including AI-generated illustrations.
        </p>
      </div>
    </div>
  </footer>
</template>
