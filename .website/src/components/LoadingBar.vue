<script setup lang="ts">
// A floating, slim loading bar recreating the classic loading bar's behaviour with original CSS
// (reference: the game's own LoadBar model, studied, not copied): a thin dark-iron frame with
// pointed end caps; one continuous fill, violet-blue at its edges and bright cyan through its
// middle; an additive comet of light (a bright round core at the fill's tip, a tapering tail
// inside it) that is dark until about 43% and brightens to full by the end; at completion the
// fill breathes once. The label sits above and the completion message below, over the artwork.
// It only draws: the owner passes `progress` (0..1) and `complete`; nothing here runs on a timer.
// The fill, tail and core move by transform, sizes are fixed (no layout shift), and after the
// completion breath the whole element fades away (its space stays reserved).
// Styles are styles/loading-bar.css, loaded with the main stylesheet so a prerendered bar is
// styled from the first paint. Decorative to assistive technology: the owner keeps the meaningful
// controls (skip, continue) as real buttons outside it.
const props = withDefaults(
  defineProps<{
    progress: number
    complete?: boolean
    label?: string
    completeLabel?: string
  }>(),
  { complete: false, label: 'Loading…', completeLabel: 'Ready' },
)
</script>

<template>
  <div class="lbar" :class="{ 'lbar--complete': props.complete }" :style="{ '--p': Math.min(1, Math.max(0, props.progress)) }" aria-hidden="true">
    <p class="lbar__label">{{ props.label }}</p>
    <div class="lbar__frame">
      <span class="lbar__cap lbar__cap--l" />
      <span class="lbar__cap lbar__cap--r" />
      <div class="lbar__track">
        <div class="lbar__fill" />
        <div class="lbar__wisprail"><div class="lbar__wisps" /></div>
        <div class="lbar__tail" />
      </div>
      <!-- The comet's core: an unclipped overlay riding the fill's tip, washing over the frame. -->
      <div class="lbar__corerail"><span class="lbar__core" /></div>
    </div>
    <p class="lbar__done">{{ props.completeLabel }}</p>
  </div>
</template>
