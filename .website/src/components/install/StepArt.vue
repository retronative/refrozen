<script setup lang="ts">
// Schematic drawings for the installation guide, one per step, drawn for this site. They are
// illustrations, not screenshots: macOS's windows look different and their wording varies by
// version, and reFrozen's own screens are not built yet, so labels are placeholder bars.
defineProps<{ step: number }>()
const labels = [
  'A disk image with a download arrow above it. Its file name is a blank bar: it has not been announced.',
  'A disk image window with the reFrozen app, and an arrow dragging it onto the Applications folder.',
  'A sketch of a settings window with a security shield and one highlighted button, the kind of place macOS asks you to allow an app.',
  'Three installer files, each with a check mark, a key for your CD keys, then a progress bar while the game is built on your Mac.',
  'A wide display showing the game\'s 4:3 picture between dark bars, above the keys Control, Command and F.',
]
</script>

<template>
  <figure class="install-art">
    <svg viewBox="0 0 320 180" role="img" :aria-label="labels[step - 1]">
      <g v-if="step === 1">
        <path class="frost-line" d="M160 14v40M146 42l14 14 14-14" />
        <path class="stone" d="M128 66h50l16 16v70h-66z" />
        <path class="line" d="M178 66v16h16" />
        <path class="shard" d="M161 92l9 15-9 24-9-24z" />
        <path class="seam" d="M161 92v39M152 107h18" />
        <rect class="placeholder" x="116" y="162" width="90" height="8" rx="2" />
      </g>

      <g v-else-if="step === 2">
        <rect class="stone" x="16" y="18" width="288" height="144" rx="6" />
        <path class="line" d="M16 40h288" />
        <circle class="dot" cx="32" cy="29" r="4" />
        <circle class="dot" cx="45" cy="29" r="4" />
        <circle class="dot" cx="58" cy="29" r="4" />
        <rect class="app" x="58" y="64" width="54" height="54" rx="12" />
        <path class="shard" d="M85 72l10 16-10 24-10-24z" />
        <rect class="bar" x="62" y="130" width="46" height="7" rx="2" />
        <path class="drag" d="M122 92c28-26 56-26 84-2" />
        <path class="gold-line" d="M196 80l12 12-16 5" />
        <path class="folder" d="M212 70h20l6 8h34v44h-60z" />
        <rect class="bar" x="216" y="130" width="54" height="7" rx="2" />
      </g>

      <g v-else-if="step === 3">
        <rect class="stone" x="16" y="12" width="288" height="156" rx="6" />
        <path class="line" d="M98 12v156" />
        <circle class="dot" cx="32" cy="26" r="4" />
        <circle class="dot" cx="45" cy="26" r="4" />
        <circle class="dot" cx="58" cy="26" r="4" />
        <rect class="bar" x="28" y="46" width="56" height="7" rx="2" />
        <rect class="bar" x="28" y="62" width="44" height="7" rx="2" />
        <rect class="bar bar--on" x="24" y="76" width="68" height="16" rx="3" />
        <rect class="bar" x="28" y="100" width="50" height="7" rx="2" />
        <rect class="bar" x="28" y="116" width="40" height="7" rx="2" />
        <path class="gold-line" d="M126 38l14-6 14 6v12c0 10-6 16-14 20-8-4-14-10-14-20z" />
        <rect class="bar" x="166" y="40" width="100" height="8" rx="2" />
        <rect class="bar" x="112" y="84" width="150" height="7" rx="2" />
        <rect class="bar" x="112" y="98" width="110" height="7" rx="2" />
        <rect class="button" x="190" y="120" width="96" height="26" rx="4" />
        <rect class="bar bar--frost" x="208" y="130" width="60" height="6" rx="2" />
        <path class="pointer" d="M270 138v22l6-6 5 10 4-2-5-10h8z" />
      </g>

      <g v-else-if="step === 4">
        <g v-for="(y, i) in [26, 70, 114]" :key="y">
          <path class="stone" :d="`M18 ${y}h40l10 10v30h-50z`" />
          <text class="numeral" x="38" :y="y + 28" text-anchor="middle">{{ ['I', 'II', 'III'][i] }}</text>
          <path class="check" :d="`M76 ${y + 22}l6 6 12-14`" />
        </g>
        <path class="gold-line" d="M108 90h22M122 82l8 8-8 8" />
        <circle class="gold-line" cx="152" cy="90" r="9" />
        <path class="gold-line" d="M161 90h20v8M174 90v6" />
        <rect class="track" x="196" y="84" width="104" height="12" rx="2" />
        <rect class="fill" x="196" y="84" width="58" height="12" rx="2" />
        <path class="shard" d="M248 40l9 15-9 22-9-22z" />
        <rect class="placeholder" x="196" y="110" width="70" height="8" rx="2" />
      </g>

      <g v-else>
        <rect class="stone" x="34" y="10" width="252" height="120" rx="4" />
        <rect class="screen" x="42" y="18" width="236" height="104" />
        <rect class="picture" x="91" y="18" width="138" height="104" />
        <path class="shard" d="M160 40l14 22-14 38-14-38z" />
        <path class="seam" d="M160 40v60M146 62h28" />
        <path class="line" d="M140 130l-6 12h52l-6-12" />
        <g v-for="(key, i) in ['ctrl', '⌘', 'F']" :key="key">
          <rect class="key" :x="98 + i * 44" y="148" width="36" height="26" rx="3" />
          <text class="key-text" :x="116 + i * 44" y="166" text-anchor="middle">{{ key }}</text>
        </g>
      </g>
    </svg>
    <figcaption>Illustration, not a screenshot</figcaption>
  </figure>
</template>
