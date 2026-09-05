<template>
  <div>
    <button
      class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-4 transition-all"
      style="color: rgba(244,247,251,.6); border: 1px solid rgba(255,255,255,.16)"
      @click="emit('back')"
    >
      <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
      Back
    </button>
    <div class="flex items-center gap-2.5 rounded-2xl px-4 mb-3.5" style="border: 1px solid rgba(255,255,255,.16)">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="color: rgba(244,247,251,.5)"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input
        :value="search"
        class="flex-1 bg-transparent border-none outline-none text-[15px] py-3.5"
        style="color: var(--ms-text)"
        :placeholder="`Search ${sportLabel} teams…`"
        autofocus
        @input="emit('update:search', ($event.target as HTMLInputElement).value)"
      />
    </div>
    <div
      class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4"
      style="max-height: 320px; overflow-y: auto"
    >
      <template v-if="teamsLoading">
        <div
          v-for="n in 4"
          :key="`team-skeleton-${n}`"
          class="rounded-2xl border-2 border-transparent px-4 py-3 flex items-center gap-3"
        >
          <span class="ms-skeleton flex-shrink-0" style="width: 32px; height: 32px; border-radius: 999px"></span>
          <div class="min-w-0 flex-1">
            <span class="ms-skeleton block" style="width: 70%; height: 13px"></span>
            <span class="ms-skeleton block" style="width: 45%; height: 11px; margin-top: 6px"></span>
          </div>
        </div>
      </template>
      <div
        v-else-if="teamResults.length === 0"
        class="col-span-full flex flex-col items-center gap-2 py-6 text-center"
      >
        <span class="text-2xl">📅</span>
        <p class="font-semibold text-sm">
          {{ search ? `No teams match "${search}"` : 'No teams available yet' }}
        </p>
      </div>
      <template v-else>
        <button
          v-for="t in teamResults"
          :key="`${t.sport}-${t.slug}`"
          class="team-card rounded-2xl border-2 px-4 py-3 text-left transition-all flex items-center gap-3"
          :class="{ selected: selectedTeamSlug === t.slug }"
          @click="emit('select', t)"
        >
          <TeamBadge :name="t.name" :icon="t.icon" :size="32" />
          <div class="min-w-0">
            <div class="font-bold text-sm truncate">{{ t.name }}</div>
            <div class="text-xs font-semibold mt-0.5 truncate" style="color: rgba(244,247,251,.5)">
              {{ t.leagues.map(l => l.name).join(' · ') }}
            </div>
          </div>
        </button>
      </template>
    </div>
    <button
      :disabled="!selectedTeamSlug"
      class="ms-btn-primary rounded-2xl w-full py-3.5 font-bold text-[15px] disabled:opacity-40"
      @click="emit('continue')"
    >
      Continue
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Team } from '@/types'
import TeamBadge from '../TeamBadge.vue'

defineProps<{
  sportLabel: string
  search: string
  teamsLoading: boolean
  teamResults: Team[]
  selectedTeamSlug: string | null
}>()

const emit = defineEmits<{
  back: []
  'update:search': [value: string]
  select: [team: Team]
  continue: []
}>()
</script>
