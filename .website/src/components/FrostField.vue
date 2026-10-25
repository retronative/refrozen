<script setup lang="ts">
// Deterministic (hydration-safe) drifting frost motes. Hidden under reduced motion.
const props = withDefaults(defineProps<{ count?: number }>(), { count: 22 })
const motes = Array.from({ length: props.count }, (_, i) => {
  const r = (n: number) => ((i * 9301 + n * 49297) % 233280) / 233280
  return {
    left: `${(r(1) * 100).toFixed(2)}%`,
    '--s': `${(2 + r(2) * 4).toFixed(1)}px`,
    '--d': `${(14 + r(3) * 18).toFixed(1)}s`,
    '--delay': `${(-r(4) * 30).toFixed(1)}s`,
    '--x': `${((r(5) - 0.5) * 160).toFixed(0)}px`,
    '--o': (0.25 + r(6) * 0.6).toFixed(2),
  }
})
</script>

<template>
  <div class="frost-field" aria-hidden="true">
    <span v-for="(style, i) in motes" :key="i" :style="style" />
  </div>
</template>
