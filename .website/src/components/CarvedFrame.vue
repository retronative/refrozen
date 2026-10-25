<script setup lang="ts">
// Gilded, carved frame with original corner ornaments (one SVG, mirrored per corner).
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
      <path d="M1 1h20l-4 4H5v12l-4 4z" fill="currentColor" />
      <path d="M8 8h8l-8 8z" fill="#0d0a06" stroke="currentColor" stroke-width="1" />
      <circle cx="26" cy="3" r="2" fill="currentColor" />
      <circle cx="3" cy="26" r="2" fill="currentColor" />
    </svg>
    <div class="frame__inner">
      <slot />
    </div>
  </div>
</template>
