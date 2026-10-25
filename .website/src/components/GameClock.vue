<script setup lang="ts">
// An in-game style clock: counts the time spent on the site and flips day/night
// every four minutes (a light ambient wash, see .night-wash). Decorative only.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const CYCLE_SECONDS = 240
const seconds = ref(0)
let timer: number | undefined

const night = computed(() => Math.floor(seconds.value / CYCLE_SECONDS) % 2 === 1)
const label = computed(() => {
  const m = Math.floor(seconds.value / 60)
  const s = seconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

onMounted(() => {
  const start = Date.now()
  timer = window.setInterval(() => {
    seconds.value = Math.floor((Date.now() - start) / 1000)
    document.documentElement.dataset.cycle = night.value ? 'night' : 'day'
  }, 1000)
})
onBeforeUnmount(() => window.clearInterval(timer))
</script>

<template>
  <div
    class="hidden sm:flex items-center gap-2 pl-3 pr-3.5 py-1 border border-seam bg-black/50 font-mono text-[.8rem] text-ash"
    aria-hidden="true"
    :title="night ? 'Night' : 'Day'"
  >
    <svg width="16" height="16" viewBox="0 0 16 16" class="transition-colors duration-700" :class="night ? 'text-dusk' : 'text-gold'">
      <g v-if="!night" fill="currentColor">
        <circle cx="8" cy="8" r="3.2" />
        <path d="M8 .5v2.5M8 13v2.5M.5 8H3M13 8h2.5M2.7 2.7l1.8 1.8M11.5 11.5l1.8 1.8M2.7 13.3l1.8-1.8M11.5 4.5l1.8-1.8" stroke="currentColor" stroke-width="1.2" />
      </g>
      <path v-else d="M10.5 1.5a6.5 6.5 0 1 0 4 11.5A6 6 0 0 1 10.5 1.5z" fill="currentColor" />
    </svg>
    <span class="tabular-nums text-bone">{{ label }}</span>
  </div>
</template>
