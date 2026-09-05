<template>
  <div>
    <button
      class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-3 transition-all"
      style="color: rgba(244,247,251,.6); border: 1px solid rgba(255,255,255,.16)"
      @click="emit('back')"
    >
      <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
      Back
    </button>
    <p class="text-sm font-medium mb-4" style="color: rgba(244,247,251,.65)">
      Select leagues for <strong style="color: var(--ms-text)">{{ team.name }}</strong>
    </p>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
      <label
        v-for="l in team.leagues"
        :key="l.slug"
        class="lgd-card-1 rounded-2xl border-2 px-4 py-3 cursor-pointer flex items-center gap-3"
        :class="chosenLeagues.includes(l.slug) ? 'lgd-card-1-on border-[rgba(142,205,242,.5)]' : 'border-white/[0.14]'"
      >
        <input
          type="checkbox"
          :value="l.slug"
          :checked="chosenLeagues.includes(l.slug)"
          class="hidden"
          @change="toggleLeague(l.slug)"
        />
        <span
          class="lgd-check-1 w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0"
          :class="chosenLeagues.includes(l.slug) ? 'lgd-check-1-on border-[var(--ms-blue)]' : 'border-white/50'"
          :style="chosenLeagues.includes(l.slug) ? 'background: linear-gradient(160deg, var(--ms-blue), var(--ms-blue-dark))' : 'background: transparent'"
        >
          <svg v-if="chosenLeagues.includes(l.slug)" class="lgd-check-mark-1" viewBox="0 0 12 12" width="12" height="12" fill="none" stroke="#08131f" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 6l3 3 5-5"/>
          </svg>
        </span>
        <span class="text-sm font-semibold" style="color: rgba(244,247,251,.85)">{{ l.name }}</span>
      </label>
    </div>
    <button
      :disabled="chosenLeagues.length === 0"
      class="ms-btn-primary rounded-2xl w-full py-3.5 font-bold text-[15px] disabled:opacity-40"
      @click="emit('continue')"
    >
      Get my link
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Team } from '@/types'

const props = defineProps<{
  team: Team
  chosenLeagues: string[]
}>()

const emit = defineEmits<{
  back: []
  'update:chosenLeagues': [slugs: string[]]
  continue: []
}>()

function toggleLeague(slug: string) {
  const next = props.chosenLeagues.includes(slug)
    ? props.chosenLeagues.filter((s) => s !== slug)
    : [...props.chosenLeagues, slug]
  emit('update:chosenLeagues', next)
}
</script>

<style scoped src="./LeaguesStep.css"></style>
