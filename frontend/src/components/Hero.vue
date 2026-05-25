<template>
  <section class="py-16 md:py-24 px-4 bg-white">
    <div class="ms-gradient-hero rounded-3xl max-w-2xl mx-auto p-6 md:p-10 shadow-sm">
      <div class="text-center">
        <p
          class="text-xs font-bold uppercase mb-4 ms-text-accent"
          style="letter-spacing: 0.18em"
        >
          Always up to date &nbsp;·&nbsp; Auto-sync
        </p>
        <h1
          class="text-3xl md:text-4xl font-black text-slate-900 leading-tight mb-3"
          style="letter-spacing: -0.02em"
        >
          Your team's schedule in your calendar.
        </h1>
        
      </div>

      <!-- Sport tabs -->
      <div class="flex justify-center gap-2 mb-4">
        <button
          v-for="s in sports"
          :key="s.id"
          class="px-5 py-2 rounded-full text-sm font-semibold border transition-all"
          :class="
            sportFilter === s.id
              ? 'bg-slate-900 text-white border-slate-900'
              : 'bg-white text-slate-700 border-slate-200 hover:border-slate-400'
          "
          @click="onSportTabClick(s.id)"
        >
          {{ s.label }}
        </button>
      </div>

      <!-- Search -->
      <div class="relative mb-4">
        <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
          <Icon name="search" />
        </span>
        <input
          v-model="search"
          type="text"
          placeholder="Search team…"
          class="w-full bg-slate-800 text-white placeholder-slate-400 rounded-xl pl-11 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
        />
      </div>

      <!-- Team grid -->
      <div class="grid grid-cols-2 gap-3 mb-5">
        <button
          v-for="t in teams"
          :key="`${t.sport}-${t.slug}`"
          class="team-card rounded-xl border-2 border-slate-200 bg-white px-4 py-3 text-left transition-all"
          :class="{ selected: selectedTeam?.slug === t.slug && selectedTeam?.sport === t.sport }"
          @click="onTeamClick(t)"
        >
          <div class="font-semibold text-slate-800 text-sm mb-0.5 line-clamp-2">{{ t.name }}</div>
          <div class="text-xs text-slate-400 line-clamp-1">
            {{ t.leagues.map(l => l.name).join(' · ') }}
          </div>
        </button>
        <div
          v-if="!loading && teams.length === 0"
          class="col-span-2 flex items-center justify-center text-sm text-slate-400 py-8"
        >
          {{ search ? `No teams match "${search}"` : 'No teams available' }}
        </div>
      </div>

      <button
        class="btn ms-btn-primary rounded-full w-full font-semibold disabled:opacity-50"
        :disabled="!selectedTeam"
        @click="onPrimaryClick"
      >
        Get my calendar link
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import type { Sport, Team } from '@/types'
import { fetchSports, fetchTeams } from '@/services/sports'
import Icon from './Icon.vue'

const emit = defineEmits<{
  getStarted: []
  pickTeam: [{ sport: string; team: Team }]
  pickSport: [sportId: string]
}>()

const sports = ref<Sport[]>([])
const teams = ref<Team[]>([])
const loading = ref(false)
const search = ref('')
const sportFilter = ref<string | null>(null)
const selectedTeam = ref<Team | null>(null)

let searchTimer: number | null = null

async function loadTeams() {
  loading.value = true
  try {
    teams.value = await fetchTeams({
      sport: sportFilter.value ?? undefined,
      q: search.value.trim() || undefined,
      limit: 8,
    })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  sports.value = await fetchSports()
  if (sports.value.length > 0) sportFilter.value = sports.value[0].id
  await loadTeams()
})

watch(sportFilter, () => {
  selectedTeam.value = null
  loadTeams()
})

watch(search, () => {
  if (searchTimer !== null) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadTeams, 200)
})

function onSportTabClick(id: string) {
  sportFilter.value = id
}

function onTeamClick(t: Team) {
  // Toggle selection; only the button opens the modal
  selectedTeam.value = selectedTeam.value?.slug === t.slug && selectedTeam.value?.sport === t.sport ? null : t
}

function onPrimaryClick() {
  if (selectedTeam.value) {
    emit('pickTeam', { sport: selectedTeam.value.sport, team: selectedTeam.value })
  } else if (sportFilter.value) {
    emit('pickSport', sportFilter.value)
  } else {
    emit('getStarted')
  }
}
</script>
