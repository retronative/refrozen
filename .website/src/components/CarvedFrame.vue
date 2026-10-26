<script setup lang="ts">
// Gilded, carved frame with original corner ornaments after the app icon's frame: a curved spike
// and a four-point stud (one SVG, mirrored per corner); mid-edge studs come from the CSS.
const corners = ['tl', 'tr', 'bl', 'br'] as const
</script>

<template>
  <div class="frame">
    <svg
      v-for="c in corners"
      :key="c"
      :class="['frame__corner', `frame__corner--${c}`]"
      viewBox="0 0 34 34"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M1 1h24c-8 1.5-13.5 4-16.5 7.5S2.5 17 1 25z" fill="currentColor" />
      <path d="M1 1h24c-8 1.5-13.5 4-16.5 7.5S2.5 17 1 25z" fill="none" stroke="#0d0905" stroke-opacity=".6" stroke-width=".8" />
      <path d="M8 2.5l1.5 4L13.5 8l-4 1.5L8 13.5l-1.5-4L2.5 8l4-1.5z" fill="#eed2a7" stroke="#0d0905" stroke-width=".8" />
    </svg>
    <div class="frame__inner">
      <slot />
    </div>
  </div>
</template>
