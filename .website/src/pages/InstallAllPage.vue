<script setup lang="ts">
// All five installation steps on one page; the same content as the step pages (StepBody).
import { RouterLink } from 'vue-router'
import CarvedFrame from '../components/CarvedFrame.vue'
import Divider from '../components/Divider.vue'
import PageHero from '../components/PageHero.vue'
import PreviewNotice from '../components/install/PreviewNotice.vue'
import StepBody from '../components/install/StepBody.vue'
import { installPath, installSteps } from '../data/release'

const banner = `${import.meta.env.BASE_URL}banners/icegate`
</script>

<template>
  <div>
    <PageHero eyebrow="Installation guide" title="Installing reFrozen" lore="Five steps, from download to the Custom Game screen." art="candlelit" art-position="50% 55%">
      <p class="rise rise-3 mt-8">
        <RouterLink class="btn btn--frost" :to="installPath(installSteps[0])">Go step by step</RouterLink>
      </p>
    </PageHero>

    <div class="mx-auto max-w-4xl px-4 sm:px-8 py-12 sm:py-16">
      <PreviewNotice />

      <nav class="mt-10" aria-labelledby="install-contents">
        <h2 id="install-contents" class="eyebrow">The steps</h2>
        <ol class="install-toc">
          <li v-for="(s, i) in installSteps" :key="s.slug">
            <a :href="`#${s.slug}`"><span class="install-track__num" aria-hidden="true">{{ i + 1 }}</span> {{ s.title }}</a>
          </li>
        </ol>
      </nav>

      <section v-for="(s, i) in installSteps" :key="s.slug" class="install-section" :aria-labelledby="s.slug">
        <p class="eyebrow">Step {{ i + 1 }} of {{ installSteps.length }}</p>
        <h2 :id="s.slug" class="install-section__title">{{ s.title }}</h2>
        <StepBody :index="i" :level="3" :id-prefix="`${s.slug}-`" />
        <p class="install-more">
          <RouterLink :to="installPath(s)">Open step {{ i + 1 }} on its own page</RouterLink>
        </p>
      </section>

      <Divider />

      <CarvedFrame class="mt-12">
        <picture class="install-closing" aria-hidden="true">
          <source type="image/avif" :srcset="`${banner}-640.avif 640w, ${banner}-1280.avif 1280w`" sizes="(min-width: 56rem) 52rem, 100vw" />
          <source type="image/webp" :srcset="`${banner}-640.webp 640w, ${banner}-1280.webp 1280w`" sizes="(min-width: 56rem) 52rem, 100vw" />
          <img :src="`${banner}-1280.webp`" alt="" width="1280" height="814" loading="lazy" decoding="async" />
        </picture>
      </CarvedFrame>
      <p class="mt-8 text-center text-ash">
        The gates are open with v0.2.0. <RouterLink to="/releases/">Follow the release status</RouterLink> or read the
        <RouterLink to="/faq/">FAQ</RouterLink>.
      </p>
    </div>
  </div>
</template>
