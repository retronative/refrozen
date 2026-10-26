<script setup lang="ts">
// The app icon (assets/icon/; resized by scripts/make_icons.sh). Decorative: the link around it
// carries the name.
defineProps<{ size?: number }>()
const base = `${import.meta.env.BASE_URL}brand/`
</script>

<template>
  <img
    class="brand-mark"
    :src="`${base}mark-96.png`"
    :srcset="`${base}mark-96.png 2x, ${base}mark-144.png 3x`"
    :width="size ?? 40"
    :height="size ?? 40"
    alt=""
    decoding="async"
  />
</template>
