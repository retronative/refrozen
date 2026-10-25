<script setup lang="ts">
import PageHero from '../components/PageHero.vue'
import { screenshots } from '../data/screenshots'

const base = import.meta.env.BASE_URL
const url = (file: string) => `${base}screenshots/${file}`
const srcset = (s: (typeof screenshots)[number]) =>
  s.variants?.length ? [...s.variants.map((v) => `${url(v.file)} ${v.width}w`), `${url(s.file)} ${s.width}w`].join(', ') : undefined

// Abstract placeholder plates, drawn for this site. No game frames are published
// until the maintainer approves specific images.
const plates = [
  { id: 'dawn', numeral: 'I', caption: 'The dawn bank', alt: 'Abstract placeholder: golden light over layered green hills.' },
  { id: 'river', numeral: 'II', caption: 'The river at night', alt: 'Abstract placeholder: a luminous blue diagonal river under stars.' },
  { id: 'dusk', numeral: 'III', caption: 'The frozen spires', alt: 'Abstract placeholder: violet ice spires against a dark sky.' },
  { id: 'tavern', numeral: 'IV', caption: 'Lanterns at the tavern', alt: 'Abstract placeholder: warm lantern glows in darkness.' },
]
</script>

<template>
  <div>
    <PageHero
      eyebrow="The gallery"
      art="portal"
      art-position="50% 50%"
      title="Screenshots"
      lore="The frames are hung. The paintings are still on their way."
    />

    <section class="mx-auto max-w-6xl px-4 sm:px-8 py-20" aria-labelledby="plates-title">
      <h2 id="plates-title" class="sr-only">{{ screenshots.length ? 'Screenshots' : 'Placeholder plates' }}</h2>

      <ul v-if="screenshots.length" class="grid list-none gap-10 p-0 m-0 sm:grid-cols-2">
        <li v-for="(shot, i) in screenshots" :key="shot.file">
          <figure class="m-0">
            <a :href="url(shot.file)" class="plate block" :aria-label="`Open full-size image: ${shot.caption}`">
              <img
                :src="url(shot.file)"
                :srcset="srcset(shot)"
                sizes="(min-width: 640px) 50vw, 100vw"
                :width="shot.width"
                :height="shot.height"
                :alt="shot.alt"
                :loading="i < 2 ? 'eager' : 'lazy'"
                decoding="async"
                class="block h-auto w-full"
              />
            </a>
            <figcaption class="mt-4">
              <span class="lore text-[1.25rem] text-bone">{{ shot.caption }}</span>
              <span class="mt-1 block text-[.85rem] text-ash">{{ shot.captureContext }}</span>
            </figcaption>
          </figure>
        </li>
      </ul>

      <template v-else>
      <div class="mx-auto mb-14 max-w-3xl border border-frost/30 bg-[linear-gradient(90deg,rgba(61,134,198,.14),rgba(61,134,198,.03))] p-5 text-[.98rem]" role="note">
        <strong class="text-bone">Screenshot coming soon.</strong>
        <span class="text-ash">
          Only rights-reviewed screenshots of reFrozen itself will appear here, chosen by the project maintainer. Until then,
          these plates are original abstract artwork — they are not captures of the game.
        </span>
      </div>

      <ul class="grid list-none gap-10 p-0 m-0 sm:grid-cols-2">
        <li v-for="p in plates" :key="p.id">
          <figure class="m-0">
            <div class="plate">
              <div class="plate__art">
                <svg viewBox="0 0 400 300" role="img" :aria-label="p.alt" preserveAspectRatio="xMidYMid slice">
                  <template v-if="p.id === 'dawn'">
                    <defs>
                      <linearGradient id="pl-dawn" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a2a12" /><stop offset=".5" stop-color="#8a6a2c" /><stop offset="1" stop-color="#16200f" /></linearGradient>
                    </defs>
                    <rect width="400" height="300" fill="url(#pl-dawn)" />
                    <circle cx="300" cy="120" r="46" fill="#f0d996" opacity=".55" />
                    <path d="M0 200 Q90 150 180 190 T400 170 V300 H0Z" fill="#2c3d1c" />
                    <path d="M0 235 Q120 190 230 230 T400 215 V300 H0Z" fill="#1a2812" />
                    <path d="M0 270 Q140 240 260 268 T400 260 V300 H0Z" fill="#0e160a" />
                  </template>
                  <template v-else-if="p.id === 'river'">
                    <rect width="400" height="300" fill="#070b16" />
                    <g fill="#dff3ff"><circle cx="40" cy="30" r="1" /><circle cx="120" cy="60" r="1.3" /><circle cx="210" cy="24" r=".9" /><circle cx="330" cy="50" r="1.2" /><circle cx="370" cy="110" r=".8" /><circle cx="80" cy="120" r=".8" /></g>
                    <path d="M-20 60 C 120 110, 200 150, 420 290" stroke="#9ad8ff" stroke-opacity=".25" stroke-width="40" fill="none" />
                    <path d="M-20 60 C 120 110, 200 150, 420 290" stroke="#dff3ff" stroke-opacity=".7" stroke-width="3" fill="none" />
                    <path d="M0 300 L0 210 L60 190 L110 230 L150 300Z" fill="#10180e" />
                    <path d="M400 0 L400 140 L340 120 L300 60 L310 0Z" fill="#141228" />
                  </template>
                  <template v-else-if="p.id === 'dusk'">
                    <defs>
                      <linearGradient id="pl-dusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b0a1e" /><stop offset="1" stop-color="#2a2160" /></linearGradient>
                    </defs>
                    <rect width="400" height="300" fill="url(#pl-dusk)" />
                    <g fill="#b1a4f4" fill-opacity=".55" stroke="#dff3ff" stroke-opacity=".5">
                      <path d="M150 300 L185 90 L200 40 L215 90 L250 300Z" />
                      <path d="M90 300 L115 170 L130 300Z" />
                      <path d="M270 300 L290 150 L310 300Z" />
                    </g>
                    <path d="M200 40 V300" stroke="#dff3ff" stroke-opacity=".4" />
                  </template>
                  <template v-else>
                    <rect width="400" height="300" fill="#0b0805" />
                    <g>
                      <circle cx="110" cy="130" r="70" fill="#e59a5b" opacity=".18" /><circle cx="110" cy="130" r="10" fill="#f0d996" opacity=".85" />
                      <circle cx="290" cy="110" r="60" fill="#e59a5b" opacity=".15" /><circle cx="290" cy="110" r="8" fill="#f0d996" opacity=".8" />
                    </g>
                    <path d="M0 220 H400 V300 H0Z" fill="#1a120a" />
                    <path d="M0 220 H400" stroke="#d8b868" stroke-opacity=".35" />
                  </template>
                </svg>
                <p class="plate__seal m-0" aria-hidden="true">Screenshot coming soon</p>
              </div>
            </div>
            <figcaption class="mt-4 flex items-baseline gap-3">
              <span class="display gilded text-[1.4rem]">{{ p.numeral }}</span>
              <span class="lore text-[1.25rem] text-bone">{{ p.caption }}</span>
              <span class="ml-auto text-[.75rem] uppercase tracking-[.25em] text-ash">Placeholder</span>
            </figcaption>
          </figure>
        </li>
      </ul>
      </template>
    </section>
  </div>
</template>
