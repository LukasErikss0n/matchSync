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
            :selected="sport === s.id"
            @click="selectSport(s.id)"
          />
          <button
            :disabled="!sport"
            class="col-span-2 sm:col-span-3 btn ms-btn-primary rounded-full mt-2 font-semibold disabled:opacity-40"
            @click="step = 2"
          >
            Continue →
          </button>
        </div>

        <!-- Step 2: League -->
        <div v-else-if="step === 2 && selectedSport">
          <button
            class="text-sm text-slate-400 hover:text-slate-700 mb-4 flex items-center gap-1"
            @click="step = 1"
          >
            ← Back
          </button>
          <div class="grid grid-cols-1 gap-2 mb-4">
            <button
              v-for="l in selectedSport.leagues"
              :key="l"
              class="team-card rounded-xl border-2 border-slate-200 px-5 py-3 text-left font-medium text-slate-700 transition-all"
              :class="{ selected: league === l }"
              @click="selectLeague(l)"
            >
              {{ l }}
            </button>
          </div>
          <button
            :disabled="!league"
            class="btn ms-btn-primary rounded-full w-full font-semibold disabled:opacity-40"
            @click="goToTeams"
          >
            Continue →
          </button>
        </div>

        <!-- Step 3: Team -->
        <div v-else-if="step === 3">
          <button
            class="text-sm text-slate-400 hover:text-slate-700 mb-4 flex items-center gap-1"
            @click="step = 2"
          >
            ← Back
          </button>
          <input
            v-model="search"
            class="input input-bordered w-full mb-3 rounded-xl text-sm"
            :placeholder="`Search ${league} teams…`"
            autofocus
          />
          <div
            class="grid grid-cols-1 gap-1.5 mb-4"
            style="max-height: 260px; overflow-y: auto"
          >
            <div
              v-if="filteredTeams.length === 0"
              class="text-slate-400 text-sm py-4 text-center"
            >
              No teams found
            </div>
            <button
              v-for="t in filteredTeams"
              :key="t"
              class="team-card rounded-xl border-2 border-slate-200 px-4 py-2.5 text-left text-sm font-medium text-slate-700 transition-all"
              :class="{ selected: team === t }"
              @click="team = t"
            >
              {{ t }}
            </button>
          </div>
          <button
            :disabled="!team"
            class="btn ms-btn-primary rounded-full w-full font-semibold disabled:opacity-40"
            @click="goToLink"
          >
            Get my calendar link →
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
              Subscribe to <strong>{{ team }}</strong> ({{ league }}) — every match syncs
              automatically.
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Sport, CalendarLink } from '@/types'
import { fetchSports, fetchTeams, fetchCalendarLink } from '@/services/sports'
import SportCard from './SportCard.vue'
import Icon from './Icon.vue'

const emit = defineEmits<{ close: [] }>()

const step = ref(1)
const sport = ref<string | null>(null)
const league = ref<string | null>(null)
const team = ref<string | null>(null)
const search = ref('')
const copied = ref(false)

const sports = ref<Sport[]>([])
const teams = ref<string[]>([])
const calLink = ref<CalendarLink | null>(null)

const stepLabels = ['Sport', 'League', 'Team', 'Your link']

const selectedSport = computed(() => sports.value.find(s => s.id === sport.value) ?? null)
const filteredTeams = computed(() =>
  teams.value.filter(t => t.toLowerCase().includes(search.value.toLowerCase()))
)

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  document.body.style.overflow = 'hidden'
  sports.value = await fetchSports()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})

function selectSport(id: string) {
  sport.value = id
  league.value = null
  team.value = null
}

function selectLeague(l: string) {
  league.value = l
  team.value = null
}

async function goToTeams() {
  if (!league.value) return
  search.value = ''
  teams.value = await fetchTeams(league.value)
  step.value = 3
}

async function goToLink() {
  if (!team.value || !league.value) return
  calLink.value = await fetchCalendarLink(team.value, league.value)
  step.value = 4
}

function handleCopy() {
  if (!calLink.value) return
  navigator.clipboard.writeText(calLink.value.url).catch(() => {})
  copied.value = true
  setTimeout(() => (copied.value = false), 2200)
}

function reset() {
  sport.value = null
  league.value = null
  team.value = null
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
