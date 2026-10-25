<script setup lang="ts">
// Renders build-time HTML from docs/ (escaped by markdown-it, html: false) and routes
// internal links through the router instead of reloading the page.
import { useRouter } from 'vue-router'

defineProps<{ html: string }>()
const router = useRouter()
const base = import.meta.env.BASE_URL

function onClick(event: MouseEvent) {
  if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  const anchor = (event.target as HTMLElement).closest('a')
  const href = anchor?.getAttribute('href')
  if (!href || !href.startsWith(base) || anchor?.target) return
  event.preventDefault()
  router.push('/' + href.slice(base.length))
}
</script>

<template>
  <div class="prose" @click="onClick" v-html="html" />
</template>
