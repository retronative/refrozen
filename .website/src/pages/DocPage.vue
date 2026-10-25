<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DocLayout from '../components/DocLayout.vue'
import { requireDoc } from '../docs'

const route = useRoute()
const doc = computed(() => requireDoc(String(route.params.slug)))
</script>

<template>
  <DocLayout :key="doc.slug" :doc="doc" eyebrow="Documentation" art="library" art-position="50% 45%" />
</template>
