<script setup lang="ts">
// Milestone status as an in-game chat log. Data: docs/status.md (via virtual:docs).
import { stateLabel, status, type MilestoneState } from '../docs'

const who: Record<MilestoneState, string> = {
  'signed-off': 'who-sentinel',
  delegated: 'who-sentinel',
  'in-progress': 'who-frost',
  future: 'who-scourge',
}
const pill: Record<MilestoneState, string> = {
  'signed-off': 'text-verdant',
  delegated: 'text-verdant',
  'in-progress': 'text-frost',
  future: 'text-dusk',
}
</script>

<template>
  <ol class="chatlog chat-reveal list-none m-0" aria-label="Milestone status">
    <li v-for="m in status.milestones" :key="m.id">
      <span class="time">[{{ m.id }}]</span>
      <span class="chan">[All]</span>
      <span :class="who[m.state]">{{ m.title }}:</span>
      {{ ' ' + m.stateText + '.' }}
      <span v-if="m.note" class="text-ash" v-html="' ' + m.note" />
      <span class="status-pill" :class="pill[m.state]">{{ stateLabel[m.state] }}</span>
    </li>
  </ol>
</template>
