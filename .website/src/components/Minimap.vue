<script setup lang="ts">
// Original, abstract three-lane map: dawn side lower-left, dusk side upper-right,
// a river on the opposite diagonal. Interactive mode turns landmarks into links.
import { RouterLink } from 'vue-router'
import { landmarks } from '../data/lanes'

defineProps<{ interactive?: boolean; hot?: string | null }>()
const emit = defineEmits<{ hover: [id: string | null] }>()

// Deterministic tree clusters on both banks.
const trees = Array.from({ length: 70 }, (_, i) => {
  const r = (n: number) => ((i * 7919 + n * 104729) % 1000) / 1000
  const x = 20 + r(1) * 160
  const y = 20 + r(2) * 160
  return { x, y, r: 2.2 + r(3) * 2.6, dusk: x + (200 - y) > 200 }
}).filter((t) => {
  const nearMid = Math.abs(t.x - (200 - t.y)) < 16
  const nearRiver = Math.abs(t.x - t.y) < 12
  const nearEdge = t.x < 30 || t.y < 30 || t.x > 170 || t.y > 170
  return !nearMid && !nearRiver && !nearEdge
})

const color = (side: string) =>
  side === 'sentinel' ? '#a3d58c' : side === 'scourge' ? '#b1a4f4' : '#88d3f9'
</script>

<template>
  <svg
    class="minimap block w-full h-auto"
    viewBox="0 0 200 200"
    :role="interactive ? 'group' : 'img'"
    :aria-label="interactive ? 'Site map drawn as a three-lane battlefield' : undefined"
    :aria-hidden="interactive ? undefined : 'true'"
  >
    <defs>
      <linearGradient id="mm-land" x1="0" y1="1" x2="1" y2="0">
        <stop offset="0" stop-color="#1d2b17" />
        <stop offset=".48" stop-color="#151d16" />
        <stop offset=".52" stop-color="#161827" />
        <stop offset="1" stop-color="#1b1733" />
      </linearGradient>
      <linearGradient id="mm-river" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#2d6ea8" stop-opacity=".2" />
        <stop offset=".5" stop-color="#88d3f9" stop-opacity=".75" />
        <stop offset="1" stop-color="#2d6ea8" stop-opacity=".2" />
      </linearGradient>
      <radialGradient id="mm-glow-dawn"><stop offset="0" stop-color="#d4ae7a" stop-opacity=".55" /><stop offset="1" stop-color="#d4ae7a" stop-opacity="0" /></radialGradient>
      <radialGradient id="mm-glow-dusk"><stop offset="0" stop-color="#8a7be0" stop-opacity=".55" /><stop offset="1" stop-color="#8a7be0" stop-opacity="0" /></radialGradient>
    </defs>

    <rect width="200" height="200" fill="url(#mm-land)" />
    <circle cx="26" cy="174" r="46" fill="url(#mm-glow-dawn)" />
    <circle cx="174" cy="26" r="46" fill="url(#mm-glow-dusk)" />

    <!-- River, upper-left to lower-right -->
    <path d="M-5 -5 C 40 30, 70 60, 100 100 S 160 170, 205 205" stroke="url(#mm-river)" stroke-width="9" fill="none" />
    <path d="M-5 -5 C 40 30, 70 60, 100 100 S 160 170, 205 205" stroke="#dff3ff" stroke-opacity=".35" stroke-width="1" fill="none" />

    <!-- Trees -->
    <g>
      <circle v-for="(t, i) in trees" :key="i" :cx="t.x" :cy="t.y" :r="t.r" :fill="t.dusk ? '#25203f' : '#22361c'" :stroke="t.dusk ? '#3a3266' : '#35522b'" stroke-width=".6" />
    </g>

    <!-- Lanes -->
    <g fill="none" stroke="#c7b28a" stroke-opacity=".55" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M30 170 L22 26 Q22 20 28 20 L172 26" />
      <path d="M30 170 L174 178 Q180 178 180 172 L172 26" />
      <path d="M30 170 L172 26" />
    </g>
    <g fill="none" stroke="#000" stroke-opacity=".35" stroke-width=".8">
      <path d="M30 170 L22 26 Q22 20 28 20 L172 26" />
      <path d="M30 170 L174 178 Q180 178 180 172 L172 26" />
      <path d="M30 170 L172 26" />
    </g>

    <!-- Ancients: an original verdant spire and a frost crown -->
    <g transform="translate(28 172)">
      <path d="M0 -14 L7 0 L0 9 L-7 0 Z" fill="#a3d58c" stroke="#eed2a7" stroke-width="1.2" />
      <path d="M0 -14 V9 M-7 0 H7" stroke="#1d2b17" stroke-width=".8" />
    </g>
    <g transform="translate(172 28)">
      <path d="M-8 6 L-5 -8 L-2 0 L0 -12 L2 0 L5 -8 L8 6 Z" fill="#b1a4f4" stroke="#dff3ff" stroke-width="1" />
    </g>

    <!-- Towers along the lanes -->
    <g fill="#d4ae7a" stroke="#000" stroke-width=".6">
      <rect v-for="(p, i) in [[24,120],[24,72],[60,22],[110,24],[78,174],[128,176],[178,80],[176,128],[58,142],[86,114],[114,86],[142,58]]" :key="i" :x="p[0] - 2.2" :y="p[1] - 2.2" width="4.4" height="4.4" transform-origin="center" />
    </g>

    <template v-if="interactive">
      <component
        :is="RouterLink"
        v-for="l in landmarks"
        :key="l.id"
        :to="l.to"
        :class="{ 'is-hot': hot === l.id }"
        :aria-label="l.label"
        @mouseenter="emit('hover', l.id)"
        @mouseleave="emit('hover', null)"
        @focus="emit('hover', l.id)"
        @blur="emit('hover', null)"
      >
        <circle class="beacon" :cx="l.x" :cy="l.y" r="10" :fill="color(l.side)" opacity=".18" />
        <circle class="ping" :cx="l.x" :cy="l.y" r="5" fill="none" :stroke="color(l.side)" stroke-width="1" />
        <circle class="marker" :cx="l.x" :cy="l.y" r="4.2" :fill="color(l.side)" stroke="#06080c" stroke-width="1.4" />
        <title>{{ l.label }}</title>
      </component>
    </template>
    <rect width="200" height="200" fill="none" stroke="#000" stroke-width="2" />
  </svg>
</template>
