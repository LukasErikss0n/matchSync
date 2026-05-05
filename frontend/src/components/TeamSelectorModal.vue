<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    style="background: rgba(15, 23, 42, 0.55); backdrop-filter: blur(4px)"
    @click.self="emit('close')"
  >
    <div
      class="bg-white rounded-3xl shadow-2xl w-full max-w-xl fade-up"
      style="max-height: 90vh; overflow-y: auto"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-7 pt-7 pb-5 border-b border-slate-100">
        <div>
          <div class="section-label mb-0.5">Step {{ step }} of 4</div>
          <h2 class="text-xl font-black text-slate-900">{{ stepLabels[step - 1] }}</h2>
        </div>
        <button
          class="btn btn-ghost btn-sm btn-circle text-slate-400"
          @click="emit('close')"
        >
          ✕
        </button>
      </div>

      <!-- Step indicator -->
      <div class="flex items-center gap-2 px-7 py-4">
        <template v-for="(l, i) in stepLabels" :key="l">
          <div class="flex items-center gap-1.5">
            <span
              class="step-indicator w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
              :class="i + 1 < step ? 'done' : i + 1 === step ? 'active' : 'idle'"
            >
              {{ i + 1 < step ? '✓' : i + 1 }}
            </span>
            <span
              class="text-xs font-medium"
              :class="i + 1 === step ? 'text-slate-800' : 'text-slate-400'"
            >
              {{ l }}
            </span>
          </div>
          <div
            v-if="i < 3"
            class="flex-1 h-px"
            :class="i + 1 < step ? 'bg-green-400' : 'bg-slate-200'"
          />
        </template>
      </div>

      <!-- Body -->
      <div class="px-7 pb-7">
        <!-- Step 1: Sport -->
        <div v-if="step === 1" class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <SportCard
            v-for="s in sports"
            :key="s.id"
            :sport="s"
            :selected="sportId === s.id"
            @click="selectSport(s.id)"
          />
          <button
            :disabled="!sportId"
            class="col-span-2 sm:col-span-3 btn ms-btn-primary rounded-full mt-2 font-semibold disabled:opacity-40"
            @click="goToTeams"
          >
            Continue
          </button>
        </div>

        <!-- Step 2: Team -->
        <div v-else-if="step === 2">
          <button
            class="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-full px-3 py-1.5 mb-4 transition-all"
            @click="step = 1"
          >
            <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
            Back
          </button>
          <input
            v-model="search"
            class="input input-bordered w-full mb-3 rounded-xl text-sm"
            :placeholder="`Search ${sportLabel} teams…`"
            autofocus
          />
          <div
            class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4"
            style="max-height: 320px; overflow-y: auto"
          >
            <div
              v-if="!teamsLoading && teamResults.length === 0"
              class="col-span-full flex flex-col items-center gap-2 py-6 text-center"
            >
              <span class="text-2xl">📅</span>
              <p class="text-slate-700 font-semibold text-sm">
                {{ search ? `No teams match "${search}"` : 'No teams available yet' }}
              </p>
            </div>
            <button
              v-for="t in teamResults"
              :key="`${t.sport}-${t.slug}`"
              class="team-card rounded-xl border-2 border-slate-200 px-4 py-3 text-left transition-all"
              :class="{ selected: teamSlug === t.slug }"
              @click="selectTeam(t)"
            >
              <div class="font-semibold text-slate-800 text-sm mb-0.5 truncate">{{ t.name }}</div>
              <div class="text-xs text-slate-400 truncate">
                {{ t.leagues.map(l => l.name).join(' · ') }}
              </div>
            </button>
          </div>
          <button
            :disabled="!teamSlug"
            class="btn ms-btn-primary rounded-full w-full font-semibold disabled:opacity-40"
            @click="goToLeagues"
          >
            Continue
          </button>
        </div>

        <!-- Step 3: Leagues -->
        <div v-else-if="step === 3 && selectedTeam">
          <button
            class="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-full px-3 py-1.5 mb-3 transition-all"
            @click="goBackToTeams"
          >
            <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
            Back
          </button>
          <p class="text-sm text-slate-500 mb-4">
            <strong class="text-slate-700">{{ selectedTeam.name }}</strong> — select leagues
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
            <label
              v-for="l in selectedTeam.leagues"
              :key="l.slug"
              class="rounded-xl border-2 px-4 py-3 cursor-pointer flex items-center gap-3 transition-all"
              :class="chosenLeagues.includes(l.slug)
                ? 'border-[var(--ms-blue)] bg-sky-50'
                : 'border-slate-200 bg-white hover:border-slate-300'"
            >
              <input
                type="checkbox"
                :value="l.slug"
                v-model="chosenLeagues"
                class="hidden"
              />
              <!-- Custom checkbox -->
              <span
                class="w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all"
                :class="chosenLeagues.includes(l.slug)
                  ? 'bg-[var(--ms-blue)] border-[var(--ms-blue)]'
                  : 'border-slate-300 bg-white'"
              >
                <svg v-if="chosenLeagues.includes(l.slug)" viewBox="0 0 12 12" class="w-3 h-3" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 6l3 3 5-5"/>
                </svg>
              </span>
              <span class="text-sm font-medium text-slate-700">{{ l.name }}</span>
            </label>
          </div>
          <button
            :disabled="chosenLeagues.length === 0"
            class="btn ms-btn-primary rounded-full w-full font-semibold disabled:opacity-40"
            @click="goToLink"
          >
            Get my link
          </button>
        </div>

        <!-- Step 4: Link -->
        <div v-else-if="step === 4 && calLink" class="fade-up">
          <div class="text-center mb-7">
            <div class="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4 feature-icon">
              <Icon name="calendar" />
            </div>
            <h3 class="text-xl font-black text-slate-900 mb-1">Your calendar is ready!</h3>
            <p class="text-slate-500 text-sm">
              <strong>{{ calLink.team }}</strong> — {{ calLink.leagues.map(l => l.name).join(', ') }}.
              Every match syncs automatically.
            </p>
          </div>
          <div class="mb-4">
            <div class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">
              Your personal calendar link
            </div>
            <div class="link-box rounded-xl px-4 py-3 break-all mb-2">{{ calLink.url }}</div>
            <button
              class="btn btn-sm btn-outline rounded-full text-xs border-slate-300 text-slate-600"
              @click="handleCopy"
            >
              Copy link
            </button>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
            <a
              :href="calLink.url"
              class="btn ms-btn-primary rounded-full flex items-center gap-2 justify-center font-semibold text-sm"
            >
              Add to Apple Calendar
            </a>
            <a
              :href="`https://calendar.google.com/calendar/r?cid=${encodeURIComponent(calLink.url)}`"
              target="_blank"
              rel="noreferrer"
              class="btn btn-outline rounded-full border-slate-300 text-slate-700 flex items-center gap-2 justify-center font-semibold text-sm hover:bg-slate-50"
            >
              Add to Google Calendar
            </a>
          </div>
          <div
            class="rounded-2xl bg-slate-50 border border-slate-100 p-4 text-sm text-slate-500 leading-relaxed"
          >
            <strong class="text-slate-700">How it stays updated:</strong> Your calendar app checks
            this link automatically. Every reschedule and playoff round appears instantly — nothing
            to do on your end.
          </div>
          <button class="btn btn-ghost btn-sm text-slate-400 mt-4 w-full" @click="reset">
            Add another team
          </button>
        </div>
      </div>
    </div>

    <Transition name="toast">
      <div v-if="copied" class="copied-toast">✓ Link copied to clipboard</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import type { CalendarLink, Sport, Team } from '@/types'
import { fetchSports, fetchTeams, fetchTeam, fetchCalendarLink } from '@/services/sports'
import SportCard from './SportCard.vue'
import Icon from './Icon.vue'

const props = defineProps<{
  initialSport?: string | null
  initialTeam?: Team | null
}>()

const emit = defineEmits<{ close: [] }>()

const step = ref(1)
const sportId = ref<string | null>(null)
const teamSlug = ref<string | null>(null)
const selectedTeam = ref<Team | null>(null)
const chosenLeagues = ref<string[]>([])
const search = ref('')
const copied = ref(false)

const sports = ref<Sport[]>([])
const teamResults = ref<Team[]>([])
const teamsLoading = ref(false)
const calLink = ref<CalendarLink | null>(null)

const stepLabels = ['Sport', 'Team', 'Leagues', 'Link']

const sportLabel = computed(
  () => sports.value.find(s => s.id === sportId.value)?.label ?? '',
)

let searchTimer: number | null = null

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

async function loadTeams() {
  if (!sportId.value) return
  teamsLoading.value = true
  try {
    teamResults.value = await fetchTeams({
      sport: sportId.value,
      q: search.value.trim() || undefined,
      limit: 30,
    })
  } finally {
    teamsLoading.value = false
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  document.body.style.overflow = 'hidden'
  sports.value = await fetchSports()

  // Apply deep-link state passed from the hero
  if (props.initialSport) sportId.value = props.initialSport
  if (props.initialTeam) {
    selectedTeam.value = props.initialTeam
    teamSlug.value = props.initialTeam.slug
    sportId.value = props.initialTeam.sport
    chosenLeagues.value = props.initialTeam.leagues.map(l => l.slug)
    step.value = 3
  } else if (props.initialSport) {
    await loadTeams()
    step.value = 2
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  if (searchTimer !== null) window.clearTimeout(searchTimer)
})

watch(search, () => {
  if (step.value !== 2) return
  if (searchTimer !== null) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadTeams, 200)
})

function selectSport(id: string) {
  sportId.value = id
  teamSlug.value = null
  selectedTeam.value = null
  chosenLeagues.value = []
}

async function goToTeams() {
  if (!sportId.value) return
  search.value = ''
  await loadTeams()
  step.value = 2
}

function selectTeam(t: Team) {
  teamSlug.value = t.slug
  selectedTeam.value = t
  chosenLeagues.value = t.leagues.map(l => l.slug)
}

async function goBackToTeams() {
  // If teams were never loaded (e.g. modal opened at step 3 from hero), load them first
  if (teamResults.value.length === 0 && sportId.value) {
    await loadTeams()
  }
  step.value = 2
}

async function goToLeagues() {
  if (!teamSlug.value || !sportId.value) return
  // Ensure we have the full team (with leagues) — if missing, fetch it
  if (!selectedTeam.value || selectedTeam.value.slug !== teamSlug.value) {
    selectedTeam.value = await fetchTeam(teamSlug.value, sportId.value)
    chosenLeagues.value = selectedTeam.value.leagues.map(l => l.slug)
  }
  step.value = 3
}

async function goToLink() {
  if (!sportId.value || !teamSlug.value || chosenLeagues.value.length === 0) return
  calLink.value = await fetchCalendarLink(
    sportId.value,
    teamSlug.value,
    chosenLeagues.value,
  )
  step.value = 4
}

function handleCopy() {
  if (!calLink.value) return
  navigator.clipboard.writeText(calLink.value.url).catch(() => {})
  copied.value = true
  setTimeout(() => (copied.value = false), 2200)
}

function reset() {
  sportId.value = null
  teamSlug.value = null
  selectedTeam.value = null
  chosenLeagues.value = []
  search.value = ''
  calLink.value = null
  step.value = 1
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
}
</style>
