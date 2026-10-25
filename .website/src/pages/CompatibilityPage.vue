<script setup lang="ts">
import DocLayout from '../components/DocLayout.vue'
import { requireDoc } from '../docs'

const doc = requireDoc('compatibility')
</script>

<template>
  <DocLayout :doc="doc" eyebrow="Know your battlefield" />
</template>
