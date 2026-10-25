<script setup lang="ts">
// Original mark: a faceted ice shard inside a gilt diamond.
import { useId } from 'vue'

defineProps<{ size?: number }>()
const uid = useId()
const gold = `bm-gold-${uid}`
const ice = `bm-ice-${uid}`
</script>

<template>
  <svg :width="size ?? 34" :height="size ?? 34" viewBox="0 0 40 40" aria-hidden="true" focusable="false">
    <defs>
      <linearGradient :id="gold" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#f0d996" />
        <stop offset="1" stop-color="#8f6f2f" />
      </linearGradient>
      <linearGradient :id="ice" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#eaf8ff" />
        <stop offset=".55" stop-color="#8fd0fb" />
        <stop offset="1" stop-color="#2f6aa3" />
      </linearGradient>
    </defs>
    <path d="M20 1.5L38.5 20 20 38.5 1.5 20z" fill="#0b0f16" :stroke="`url(#${gold})`" stroke-width="1.6" />
    <path d="M20 6.5L33.5 20 20 33.5 6.5 20z" fill="none" stroke="#d8b868" stroke-opacity=".35" />
    <path d="M20 8l5.5 9L20 32l-5.5-15z" :fill="`url(#${ice})`" />
    <path d="M20 8v24M14.5 17h11" stroke="#06080c" stroke-opacity=".45" stroke-width=".8" />
  </svg>
</template>
