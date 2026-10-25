<script setup lang="ts">
// Marks an instruction as verified today, planned (designed, not built) or unverified (not yet
// tested for reFrozen). The word itself carries the meaning; colour only reinforces it.
defineProps<{ kind: 'verified' | 'planned' | 'unverified' }>()
const label = { verified: 'Verified', planned: 'Planned', unverified: 'Unverified' }
</script>

<template>
  <span :class="['install-tag', `install-tag--${kind}`]">{{ label[kind] }}</span>
</template>
