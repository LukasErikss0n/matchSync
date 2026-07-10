<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    style="background: rgba(5, 8, 14, 0.6); backdrop-filter: blur(8px)"
    @click.self="emit('close')"
  >
    <div
      class="glass-panel relative rounded-[30px] w-full max-w-xl fade-up overflow-hidden"
      style="max-height: 90vh; overflow-y: auto; background: rgba(22,32,52,.9); backdrop-filter: blur(32px) saturate(150%); border: 1px solid rgba(255,255,255,.2)"
    >
      <div
        class="absolute inset-0 pointer-events-none"
        style="background: linear-gradient(115deg, rgba(255,255,255,.08) 0 34%, transparent 34%)"
      ></div>

      <!-- Header -->
      <div class="relative flex items-center justify-between px-7 pt-7 pb-5 border-b border-white/10">
        <div>
          <div class="text-[11.5px] font-bold uppercase mb-1 ms-text-accent" style="letter-spacing: 1.8px">Step {{ step }} of 4</div>
          <h2 class="text-2xl font-extrabold" style="letter-spacing: -0.5px">{{ stepLabels[step - 1] }}</h2>
        </div>
        <button
          class="w-8 h-8 rounded-full flex items-center justify-center transition-colors"
          style="background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.16)"
          @click="emit('close')"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M6 6l12 12M18 6 6 18"/></svg>
        </button>
      </div>

      <!-- Step indicator -->
      <div class="relative flex items-center gap-2 px-7 py-4">
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
              :style="i + 1 === step ? 'color: var(--ms-text)' : 'color: var(--ms-muted-dim)'"
            >
              {{ l }}
            </span>
          </div>
          <div
            v-if="i < 3"
            class="flex-1 h-px"
            :style="i + 1 < step ? 'background: var(--ms-green)' : 'background: rgba(255,255,255,.14)'"
          />
        </template>
      </div>

      <!-- Body -->
      <div class="relative px-7 pb-7">
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
            class="col-span-2 sm:col-span-3 ms-btn-primary rounded-2xl mt-2 py-3.5 font-bold text-[15px] disabled:opacity-40"
            @click="goToTeams"
          >
            Continue
          </button>
        </div>

        <!-- Step 2: Team -->
        <div v-else-if="step === 2">
          <button
            class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-4 transition-all"
            style="color: rgba(244,247,251,.6); background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.16)"
            @click="step = 1"
          >
            <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
            Back
          </button>
          <div class="flex items-center gap-2.5 rounded-2xl px-4 mb-3.5" style="background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.16)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="color: rgba(244,247,251,.5)"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
            <input
              v-model="search"
              class="flex-1 bg-transparent border-none outline-none text-[15px] py-3.5"
              style="color: var(--ms-text)"
              :placeholder="`Search ${sportLabel} teams…`"
              autofocus
            />
          </div>
          <div
            class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4"
            style="max-height: 320px; overflow-y: auto"
          >
            <div
              v-if="!teamsLoading && teamResults.length === 0"
              class="col-span-full flex flex-col items-center gap-2 py-6 text-center"
            >
              <span class="text-2xl">📅</span>
              <p class="font-semibold text-sm">
                {{ search ? `No teams match "${search}"` : 'No teams available yet' }}
              </p>
            </div>
            <button
              v-for="t in teamResults"
              :key="`${t.sport}-${t.slug}`"
              class="team-card rounded-2xl border-2 px-4 py-3 text-left transition-all flex items-center gap-3"
              :class="{ selected: teamSlug === t.slug }"
              @click="selectTeam(t)"
            >
              <TeamBadge :name="t.name" :icon="t.icon" :size="32" />
              <div class="min-w-0">
                <div class="font-bold text-sm truncate">{{ t.name }}</div>
                <div class="text-xs font-semibold mt-0.5 truncate" style="color: rgba(244,247,251,.5)">
                  {{ t.leagues.map(l => l.name).join(' · ') }}
                </div>
              </div>
            </button>
          </div>
          <button
            :disabled="!teamSlug"
            class="ms-btn-primary rounded-2xl w-full py-3.5 font-bold text-[15px] disabled:opacity-40"
            @click="goToLeagues"
          >
            Continue
          </button>
        </div>

        <!-- Step 3: Leagues -->
        <div v-else-if="step === 3 && selectedTeam">
          <button
            class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-3 transition-all"
            style="color: rgba(244,247,251,.6); background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.16)"
            @click="goBackToTeams"
          >
            <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
            Back
          </button>
          <p class="text-sm font-medium mb-4" style="color: rgba(244,247,251,.65)">
            <strong style="color: var(--ms-text)">{{ selectedTeam.name }}</strong> — select leagues
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
            <label
              v-for="l in selectedTeam.leagues"
              :key="l.slug"
              class="rounded-2xl border-2 px-4 py-3 cursor-pointer flex items-center gap-3 transition-all"
              :class="chosenLeagues.includes(l.slug) ? 'border-[rgba(142,205,242,.5)]' : 'border-white/[0.14]'"
              :style="chosenLeagues.includes(l.slug) ? 'background: rgba(142,205,242,.14)' : 'background: rgba(255,255,255,.05)'"
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
                  ? 'border-[var(--ms-blue)]'
                  : 'border-white/25'"
                :style="chosenLeagues.includes(l.slug) ? 'background: linear-gradient(160deg, var(--ms-blue), var(--ms-blue-dark))' : 'background: transparent'"
              >
                <svg v-if="chosenLeagues.includes(l.slug)" viewBox="0 0 12 12" class="w-3 h-3" fill="none" stroke="#08131f" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 6l3 3 5-5"/>
                </svg>
              </span>
              <span class="text-sm font-semibold" style="color: rgba(244,247,251,.85)">{{ l.name }}</span>
            </label>
          </div>
          <button
            :disabled="chosenLeagues.length === 0"
            class="ms-btn-primary rounded-2xl w-full py-3.5 font-bold text-[15px] disabled:opacity-40"
            @click="goToLink"
          >
            Get my link
          </button>
        </div>

        <!-- Step 4: Link -->
        <div v-else-if="step === 4 && calLink" class="fade-up">
          <button
            class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-4 transition-all"
            style="color: rgba(244,247,251,.6); background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.16)"
            @click="step = 3"
          >
            <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
            Back
          </button>
          <div class="text-center mb-7">
            <div
              class="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style="background: linear-gradient(160deg, var(--ms-blue), var(--ms-blue-dark)); box-shadow: 0 20px 36px -14px rgba(94,178,230,.6)"
            >
              <img
                src="/matchSync_bg.png"
                alt="MatchCalender"
                class="w-full h-full rounded-2xl object-cover"
              />
            </div>
            <h3 class="text-xl font-extrabold mb-1" style="letter-spacing: -0.3px">Your calendar is ready!</h3>
            <p class="text-sm font-medium" style="color: rgba(244,247,251,.6)">
              <strong style="color: var(--ms-text)">{{ calLink.team }}</strong> — {{ calLink.leagues.map(l => l.name).join(', ') }}.
              Every match syncs automatically.
            </p>
          </div>
          <div class="mb-4">
            <div class="text-[10.5px] font-bold uppercase tracking-widest mb-2" style="color: rgba(244,247,251,.45)">
              Your personal calendar link
            </div>
            <div class="link-box rounded-2xl px-4 py-3 break-all mb-2">{{ calLink.url }}</div>
            <button
              class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 transition-all"
              style="background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.16); color: var(--ms-text)"
              @click="handleCopy"
            >
              Copy link
            </button>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
            <a
              :href="calLink.url"
              class="ms-btn-primary rounded-2xl flex items-center gap-2 justify-center py-3.5 font-bold text-sm"
            >
              Add to Apple Calendar
            </a>
            <a
              :href="`https://calendar.google.com/calendar/r?cid=${encodeURIComponent(calLink.url)}`"
              target="_blank"
              rel="noreferrer"
              class="ms-btn-secondary rounded-2xl flex items-center gap-2 justify-center py-3.5 font-bold text-sm"
            >
              Add to Google Calendar
            </a>
          </div>
          <div
            class="rounded-2xl p-4 text-sm leading-relaxed"
            style="background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1); color: rgba(244,247,251,.6)"
          >
            <strong style="color: var(--ms-text)">How it stays updated:</strong> Your calendar app checks
            this link automatically. Every reschedule and playoff round appears instantly — nothing
            to do on your end.
          </div>
          <button
            class="mt-4 w-full text-sm font-semibold py-2"
            style="color: rgba(244,247,251,.45)"
            @click="reset"
          >
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
import TeamBadge from './TeamBadge.vue'

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
