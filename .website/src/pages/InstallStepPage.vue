<script setup lang="ts">
// One installation step per prerendered page (/docs/installation/step-N/), so the guide works
// without JavaScript: every step, Back and Next are plain links. With JavaScript the router swaps
// steps in place, and focus moves to the step counter so screen readers announce the new step.
import { computed, nextTick, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import PageHero from '../components/PageHero.vue'
import PreviewNotice from '../components/install/PreviewNotice.vue'
import StepBody from '../components/install/StepBody.vue'
import { installPath, installSteps } from '../data/release'

const props = defineProps<{ index: number }>()
const step = computed(() => installSteps[props.index])
const prev = computed(() => installSteps[props.index - 1])
const next = computed(() => installSteps[props.index + 1])
const total = installSteps.length
const counter = ref<HTMLElement>()

watch(
  () => props.index,
  async () => {
    await nextTick()
    counter.value?.focus({ preventScroll: true })
  },
)
</script>

<template>
  <div>
    <PageHero
      eyebrow="Installation guide · Preview"
      :title="step.title"
      :lore="`Step ${index + 1} of ${total}`"
      :art="index === total - 1 ? 'icegate' : 'candlelit'"
      :art-position="index === total - 1 ? '50% 70%' : '50% 55%'"
    />

    <div class="mx-auto max-w-4xl px-4 sm:px-8 py-12 sm:py-16">
      <nav class="install-track" aria-label="Installation steps">
        <p ref="counter" class="install-track__count" tabindex="-1">
          Step {{ index + 1 }} of {{ total }}<span class="sr-only">: {{ step.title }}</span>
        </p>
        <ol>
          <li v-for="(s, j) in installSteps" :key="s.slug" :class="{ 'is-done': j < index, 'is-current': j === index }">
            <RouterLink :to="installPath(s)" :aria-current="j === index ? 'step' : undefined">
              <span class="install-track__num" aria-hidden="true">{{ j + 1 }}</span>
              <span class="install-track__name"><span class="sr-only">Step {{ j + 1 }}: </span>{{ s.short }}</span>
            </RouterLink>
          </li>
        </ol>
      </nav>

      <PreviewNotice class="mt-8" />

      <article class="mt-10" :aria-label="`Step ${index + 1}: ${step.title}`">
        <StepBody :key="step.slug" :index="index" :level="2" />
      </article>

      <nav class="install-pager" aria-label="Back and next step">
        <RouterLink v-if="prev" class="install-pager__btn" :to="installPath(prev)" rel="prev">
          <span class="install-pager__dir">&larr; Back</span>
          <span class="install-pager__what">Step {{ index }}: {{ prev.short }}</span>
        </RouterLink>
        <span v-else class="install-pager__btn is-disabled" aria-disabled="true">
          <span class="install-pager__dir">&larr; Back</span>
          <span class="install-pager__what">This is the first step</span>
        </span>
        <RouterLink v-if="next" class="install-pager__btn install-pager__btn--next" :to="installPath(next)" rel="next">
          <span class="install-pager__dir">Next step &rarr;</span>
          <span class="install-pager__what">Step {{ index + 2 }}: {{ next.short }}</span>
        </RouterLink>
        <RouterLink v-else class="install-pager__btn install-pager__btn--next" to="/releases/">
          <span class="install-pager__dir">End of the preview</span>
          <span class="install-pager__what">Follow the release status &rarr;</span>
        </RouterLink>
      </nav>

      <p class="install-more">
        <RouterLink :to="installPath()">View all steps on one page</RouterLink>
        <span aria-hidden="true">·</span>
        <RouterLink to="/docs/getting-started/">Getting started</RouterLink>
        <span aria-hidden="true">·</span>
        <RouterLink to="/docs/">All documentation</RouterLink>
      </p>
    </div>
  </div>
</template>
