<script setup lang="ts">
// Original rune-like glyphs, drawn for this site on a 24-unit grid.
defineProps<{ name: string; size?: number }>()
</script>

<template>
  <svg
    :width="size ?? 22"
    :height="size ?? 22"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="square"
    stroke-linejoin="miter"
    aria-hidden="true"
    focusable="false"
  >
    <template v-if="name === 'gate'">
      <path d="M5 21V9l7-6 7 6v12" /><path d="M9 21v-7h6v7" /><path d="M12 3v4" />
    </template>
    <template v-else-if="name === 'blade'">
      <path d="M12 2l2.5 4v9h-5V6z" /><path d="M7 15h10" /><path d="M12 15v5" /><path d="M10 22h4" />
    </template>
    <template v-else-if="name === 'horn'">
      <path d="M4 10v4h3l6 5V5L7 10z" /><path d="M16.5 8.5c1.5 2 1.5 5 0 7" /><path d="M19 6c3 3.5 3 8.5 0 12" />
    </template>
    <template v-else-if="name === 'hand'">
      <path d="M8 3h8l2 6-6 12L6 9z" /><path d="M6 9h12" /><path d="M12 3v18" />
    </template>
    <template v-else-if="name === 'eye'">
      <path d="M2 12l5-5h10l5 5-5 5H7z" /><path d="M12 9l3 3-3 3-3-3z" />
    </template>
    <template v-else-if="name === 'scroll'">
      <path d="M6 4h12v16H6z" /><path d="M4 4h4M16 20h4" /><path d="M9 9h6M9 12h6M9 15h4" />
    </template>
    <template v-else-if="name === 'forge'">
      <path d="M4 14h16l-2 6H6z" /><path d="M8 14V9l4-5 4 5v5" /><path d="M12 8v6" />
    </template>
    <template v-else-if="name === 'duel'">
      <path d="M4 4l10 10" /><path d="M20 4L10 14" /><path d="M6 16l2 2M18 16l-2 2" /><path d="M3 21l3-3M21 21l-3-3" />
    </template>
    <template v-else-if="name === 'shard'">
      <path d="M12 2l5 7-5 13-5-13z" /><path d="M7 9h10" /><path d="M12 2v20" />
    </template>
    <template v-else>
      <path d="M12 3l9 9-9 9-9-9z" />
    </template>
  </svg>
</template>
