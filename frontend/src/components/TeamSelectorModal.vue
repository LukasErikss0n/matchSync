<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop"
    :class="{ 'is-closing': closing }"
    style="background: rgba(5, 8, 14, 0.6); backdrop-filter: blur(8px)"
    @click.self="handleClose"
  >
    <div
      class="glass-panel relative rounded-[30px] w-full max-w-xl modal-panel overflow-hidden"
      :class="{ 'is-closing': closing }"
      style="max-height: 90vh; overflow-y: auto; background: rgba(22,32,52,.9); backdrop-filter: blur(32px) saturate(150%); border: 1px solid rgba(255,255,255,.2)"
    >
      <div
        class="absolute inset-0 pointer-events-none"
        style="background: linear-gradient(100deg, rgba(142,205,242,.03) 0 50%, transparent 50%)"
      ></div>

      <!-- Header -->
      <div class="relative flex items-center justify-between px-7 pt-7 pb-5 border-b border-white/10">
        <div>
          <div class="text-[11.5px] font-bold uppercase mb-1 ms-text-accent" style="letter-spacing: 1.8px">Step {{ step }} of 4</div>
          <h2 class="text-2xl font-extrabold" style="letter-spacing: -0.5px">{{ stepLabels[step - 1] }}</h2>
        </div>
        <button
          class="xcl-btn-1 w-8 h-8 rounded-full flex items-center justify-center"
          :class="{ 'xcl-closing-1': closing }"
          @click="handleClose"
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
      <div ref="stepViewport" class="relative step-viewport">
      <Transition
        :name="stepTransitionName"
        @enter="growViewportTo"
        @after-enter="releaseViewportHeight"
        @enter-cancelled="releaseViewportHeight"
      >
        <!-- Grabbing your calendar link -->
        <div v-if="submitting" key="submitting">
          <div class="py-10 flex flex-col items-center text-center" role="status" aria-live="polite">
            <div class="icl-badge w-16 h-16 rounded-2xl flex items-center justify-center mb-5" style="background: #131c2e">
              <div class="icl-spinner" aria-hidden="true">
                <span class="icl-spinner-bar" style="transform: rotate(0deg); animation-delay: 0s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(30deg); animation-delay: -1.1s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(60deg); animation-delay: -1s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(90deg); animation-delay: -0.9s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(120deg); animation-delay: -0.8s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(150deg); animation-delay: -0.7s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(180deg); animation-delay: -0.6s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(210deg); animation-delay: -0.5s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(240deg); animation-delay: -0.4s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(270deg); animation-delay: -0.3s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(300deg); animation-delay: -0.2s"></span>
                <span class="icl-spinner-bar" style="transform: rotate(330deg); animation-delay: -0.1s"></span>
              </div>
              <svg class="icl-check icl-check-1" viewBox="0 0 24 24" width="26" height="26" fill="none" aria-hidden="true">
                <path d="M5 12.5l4.5 4.5L19 7" stroke="#8ecdf2" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="icl-phases relative h-5 text-sm font-semibold" style="color: rgba(244,247,251,.75); min-width: 220px">
              <span class="icl-phase icl-phase-a">Grabbing fixtures…</span>
              <span class="icl-phase icl-phase-b">Syncing your calendar…</span>
              <span class="icl-phase icl-phase-c">All set!</span>
            </div>
          </div>
        </div>

        <!-- Step 1: Sport -->
        <div v-else-if="step === 1" key="step1">
          <!-- Two columns at every width: at three, the four sports leave a
               lone card orphaned on a second row. Cards get a fixed width and
               the grid shrink-wraps around them, so they stay compact instead
               of stretching to fill the modal. -->
          <div class="grid grid-cols-2 gap-3 w-fit mx-auto mb-5">
            <template v-if="sportsLoading && sports.length === 0">
              <div v-for="n in 4" :key="`sport-skeleton-${n}`" class="w-26">
                <div class="w-full max-w-[180px] mx-auto aspect-square rounded-2xl sm:rounded-[22px] flex flex-col items-center justify-center gap-1.5 sm:gap-2">
                  <span class="ms-skeleton" style="width: 52px; height: 52px; border-radius: 12px"></span>
                  <span class="ms-skeleton" style="width: 56px; height: 13px; margin-top: 4px"></span>
                </div>
              </div>
            </template>
            <template v-else>
              <div v-for="s in sports" :key="s.id" class="w-26">
                <SportCard
                  :sport="s"
                  :selected="sportId === s.id"
                  @click="selectSport(s.id)"
                />
              </div>
            </template>
          </div>
          <!-- Outside the grid: the button spans the modal, not the cards. -->
          <button
            :disabled="!sportId"
            class="ms-btn-primary rounded-2xl w-full py-3.5 font-bold text-[15px] disabled:opacity-40"
            @click="goToTeams"
          >
            Continue
          </button>
        </div>

        <!-- Step 2: Team -->
        <div v-else-if="step === 2" key="step2">
          <button
            class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-4 transition-all"
            style="color: rgba(244,247,251,.6); border: 1px solid rgba(255,255,255,.16)"
            @click="step = 1"
          >
            <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
            Back
          </button>
          <div class="flex items-center gap-2.5 rounded-2xl px-4 mb-3.5" style="border: 1px solid rgba(255,255,255,.16)">
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
            </template>
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
        <div v-else-if="step === 3 && selectedTeam" key="step3">

          <button
            class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-3 transition-all"
            style="color: rgba(244,247,251,.6); border: 1px solid rgba(255,255,255,.16)"
            @click="goBackToTeams"
          >
            <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
            Back
          </button>
          <p class="text-sm font-medium mb-4" style="color: rgba(244,247,251,.65)">
            Select leagues for <strong style="color: var(--ms-text)">{{ selectedTeam.name }}</strong>
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
            <label
              v-for="l in selectedTeam.leagues"
              :key="l.slug"
              class="lgd-card-1 rounded-2xl border-2 px-4 py-3 cursor-pointer flex items-center gap-3"
              :class="chosenLeagues.includes(l.slug) ? 'lgd-card-1-on border-[rgba(142,205,242,.5)]' : 'border-white/[0.14]'"
            >
              <input type="checkbox" :value="l.slug" v-model="chosenLeagues" class="hidden" />
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
            @click="goToLink"
          >
            Get my link
          </button>

        </div>

        <!-- Step 4: Link -->
        <div v-else-if="step === 4 && calLink" key="step4">
          <button
            class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-4 transition-all"
            style="color: rgba(244,247,251,.6);  border: 1px solid rgba(255,255,255,.16)"
            @click="step = 3"
          >
            <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
            Back
          </button>
          <div class="text-center mb-7">
            <div
              class="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style="background: #131c2e"
            >
              <img
                src="/logo.svg"
                alt="MatchCalender"
                class="w-full h-full object-contain"
              />
            </div>
            <h3 class="text-xl font-extrabold mb-1" style="letter-spacing: -0.3px">Your calendar is ready!</h3>
            <p class="text-sm font-medium" style="color: rgba(244,247,251,.6)">
              <strong style="color: var(--ms-text)">{{ calLink.team }}</strong> , {{ calLink.leagues.map(l => l.name).join(', ') }}.
              Every match syncs automatically.
            </p>
          </div>
          <div class="mb-4">
            <div class="text-[10.5px] font-bold uppercase tracking-widest mb-2" style="color: rgba(244,247,251,.45)">
              Your personal calendar link
            </div>
            <button
              type="button"
              class="link-box rounded-2xl px-4 py-3 break-all mb-2 text-left w-full cursor-pointer"
              title="Click to copy"
              @click="handleCopy"
            >{{ calLink.url }}</button>
            <div class="flex items-center gap-2">
              <button
                class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 transition-all"
                style="background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.16); color: var(--ms-text)"
                @click="handleCopy"
              >
                <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4.5" y="4.5" width="9" height="9" rx="1.5"/><path d="M2.5 10V3a1 1 0 0 1 1-1h7"/></svg>
                Copy link
              </button>
              <button
                class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 transition-all"
                style="background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.16); color: var(--ms-text)"
                @click="togglePreview"
              >
                <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M1 8s2.5-4.5 7-4.5S15 8 15 8s-2.5 4.5-7 4.5S1 8 1 8Z"/><circle cx="8" cy="8" r="2"/></svg>
                {{ showPreview ? 'Hide preview' : 'Preview all matches' }}
              </button>
            </div>
          </div>

          <Transition name="preview">
            <div v-if="showPreview" class="rounded-2xl overflow-hidden mb-5" style="background: rgba(0,0,0,.2); border: 1px solid rgba(255,255,255,.12)">
              <!-- Mirrors the real preview rows (date column + title/league)
                   so the panel doesn't resize as the fixtures arrive. -->
              <div v-if="previewLoading" aria-hidden="true">
                <div
                  v-for="n in 4"
                  :key="`preview-skeleton-${n}`"
                  class="flex items-start gap-3 px-4 py-3 border-b border-white/[0.06] last:border-b-0"
                >
                  <span class="ms-skeleton flex-shrink-0" style="width: 44px; height: 12px; margin-top: 2px"></span>
                  <div class="flex-1 min-w-0">
                    <span class="ms-skeleton block" style="width: 66%; height: 13px"></span>
                    <span class="ms-skeleton block" style="width: 38%; height: 11px; margin-top: 6px"></span>
                  </div>
                </div>
              </div>
              <div v-else-if="previewMatches.length === 0" class="py-6 text-center text-sm" style="color: rgba(244,247,251,.5)">
                No upcoming matches found.
              </div>
              <div v-else style="max-height: 260px; overflow-y: auto">
                <div
                  v-for="m in previewMatches"
                  :key="m.id"
                  class="flex items-start gap-3 px-4 py-3 border-b border-white/[0.06] last:border-b-0"
                >
                  <div class="w-11 flex-shrink-0 pt-px text-xs font-bold" style="color: rgba(244,247,251,.4)">
                    {{ formatMatchDate(m.start_time) }}
                  </div>
                  <div class="flex-1 min-w-0 text-sm font-semibold break-words">
                    <template v-if="m.sport === 'motorsport'">
                      {{ m.home_team }} <span style="color: rgba(244,247,251,.45)">·</span> {{ m.away_team }}
                    </template>
                    <template v-else>
                      {{ m.home_team }} <span style="color: rgba(244,247,251,.45)">vs</span> {{ m.away_team }}
                    </template>
                    <div class="text-xs font-bold ms-text-accent mt-0.5">{{ m.league.name }}</div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>

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
            this link automatically. Every reschedule and playoff round appears instantly, nothing
            to do on your end.
          </div>
          <button
            class="mt-4 w-full text-sm font-semibold py-2"
            style="color: rgba(244,247,251,.45)"
            @click="reset"
          >
            Pick a diffrent team
          </button>
        </div>

        <!-- No step matched: restoring a reload whose data is still loading
             (e.g. step 3 before fetchTeam resolves). Without this the body
             is simply empty for the whole round-trip. -->
        <div v-else key="step-loading" class="py-12 text-center text-sm" style="color: rgba(244,247,251,.5)">
          Loading…
        </div>
      </Transition>
      </div>
    </div>

    <Transition name="toast">
      <div v-if="copied" class="copied-toast">✓ Link copied to clipboard</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { CalendarLink, Match, Sport, Team } from '@/types'
import { fetchSports, fetchTeams, fetchTeam, fetchCalendarLink, fetchMatches } from '@/services/sports'
import SportCard from './SportCard.vue'
import TeamBadge from './TeamBadge.vue'

const props = defineProps<{
  initialSport?: string | null
  initialTeam?: Team | null
}>()

const emit = defineEmits<{ close: [] }>()

const route = useRoute()
const router = useRouter()
// Mirror the wizard's position into the URL (?wstep=&wsport=&wteam=) so a page
// reload while the modal is open restores it instead of dropping to the page
// behind it. Guarded until the initial restore finishes so the watcher below
// doesn't fire mid-setup.
const urlSyncReady = ref(false)

function syncUrl() {
  if (!urlSyncReady.value) return
  const query: Record<string, string> = { ...(route.query as Record<string, string>) }
  query.wstep = String(step.value)
  if (sportId.value) query.wsport = sportId.value
  else delete query.wsport
  if (teamSlug.value) query.wteam = teamSlug.value
  else delete query.wteam
  router.replace({ query })
}

// The wizard's URL params, parsed once for every consumer below (the step
// seed, the ref seeds, and onMounted's restore) so the coercion rules can't
// drift apart. vue-router yields string[] for a repeated param — treat
// anything that isn't a plain non-empty string as absent.
function firstParam(v: unknown): string | null {
  const raw = Array.isArray(v) ? v[0] : v
  return typeof raw === 'string' && raw ? raw : null
}
const urlParams = {
  step: Number(firstParam(route.query.wstep) ?? NaN),
  sport: firstParam(route.query.wsport),
  team: firstParam(route.query.wteam),
}

// Which step to open on, decided before the first render. `step` drives the
// template, so defaulting to 1 and correcting inside onMounted (after an
// await) paints the Sport step for a frame and then animates away from it —
// the flash you get on every deep link from a sport card or a team.
function initialStep(): number {
  if (props.initialTeam) return 3
  if (props.initialSport) return 2
  // Restoring a reload: trust the URL only as far as the params each step
  // needs, so we never open on a step that can't render. wstep itself is
  // secondary — a team link with the step missing still belongs on step 3.
  if (urlParams.sport && urlParams.team) return urlParams.step === 2 ? 2 : 3
  if (urlParams.sport) return 2
  return 1
}

const step = ref(initialStep())
// Direction the wizard is currently moving, so the step-swap transition
// slides the right way (forward → new content enters from the right;
// back → from the left) instead of always sliding one direction.
const stepDirection = ref<'forward' | 'back'>('forward')
const stepTransitionName = computed(() => `step-${stepDirection.value}`)
// flush: 'sync' matters. A default (post) watcher updates the direction only
// *after* the re-render that swaps the step, so the Transition starts with
// the previous step's name and then has it changed mid-flight — Vue strips
// the old enter classes and applies the new ones, leaving the element with
// no transition class for a frame, painted at its final position and full
// opacity. That one-frame flash showed on 3 → 4 whenever the direction was
// still 'back' from a previous Back click. Resolving it synchronously means
// the swap renders with the correct name the first time.
watch(step, (next, prev) => {
  stepDirection.value = next >= prev ? 'forward' : 'back'
}, { flush: 'sync' })

// Closing plays a short reverse animation before the parent actually
// unmounts the modal — closing the panel by simply vanishing looked abrupt
// next to its animated entrance.
const closing = ref(false)
const CLOSE_ANIMATION_MS = 180
function handleClose() {
  if (closing.value) return
  closing.value = true
  setTimeout(() => emit('close'), CLOSE_ANIMATION_MS)
}

// Seeded from props for the same reason as `step`: a team deep-link already
// carries everything step 3 renders, so waiting for onMounted would leave the
// step momentarily unrenderable.
const sportId = ref<string | null>(
  props.initialTeam?.sport ?? props.initialSport ?? urlParams.sport,
)
const teamSlug = ref<string | null>(props.initialTeam?.slug ?? null)
const selectedTeam = ref<Team | null>(props.initialTeam ?? null)
const chosenLeagues = ref<string[]>(props.initialTeam?.leagues.map((l) => l.slug) ?? [])
const search = ref('')
const copied = ref(false)

const sports = ref<Sport[]>([])
// Sports are always re-fetched on mount (see onMounted below) — true until
// that first response lands, so step 1 shows skeleton cards instead of an
// empty grid for the round-trip.
const sportsLoading = ref(true)
const teamResults = ref<Team[]>([])
// Starts true whenever mount will immediately fetch teams, so step 2 shows the
// loading state instead of flashing "No teams available yet" at an empty list.
const teamsLoading = ref(!props.initialTeam && !!sportId.value)
const calLink = ref<CalendarLink | null>(null)
// Drives the "grabbing data" loading state while goToLink's fetch is in
// flight — step stays 3 the whole time, so this is a separate flag rather
// than an extra numeric step.
const submitting = ref(false)

// The body animates its own height across a step swap. Without it the panel
// snapped from the outgoing step's height to the incoming one's, and because
// the swap used mode="out-in" the tall, empty step-3 box stayed on screen for
// the length of the leave — the flash before the "grabbing data" state.
const stepViewport = ref<HTMLElement | null>(null)

// Locked synchronously, at the moment the step changes and before Vue
// re-renders, so `height` still holds the outgoing step's size when the
// transition below starts. A post-flush watcher would measure after the swap
// and animate from the wrong value.
watch([step, submitting], () => {
  const vp = stepViewport.value
  if (vp) vp.style.height = `${vp.offsetHeight}px`
}, { flush: 'sync' })

// Measured off the incoming step itself rather than the container: the
// outgoing one is still in the DOM at this point (it leaves out of flow, see
// .step-*-leave-active) and would inflate a container measurement.
function growViewportTo(el: Element) {
  const vp = stepViewport.value
  if (!vp) return
  const style = getComputedStyle(vp)
  const pad = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom)
  void vp.offsetHeight // flush the locked height so it becomes the start value
  vp.style.height = `${(el as HTMLElement).offsetHeight + pad}px`
}

// Back to auto once the swap is done, so content that resizes in place (the
// step-4 match preview) isn't pinned to the height it entered at.
function releaseViewportHeight() {
  const vp = stepViewport.value
  if (vp) vp.style.height = ''
}

const showPreview = ref(false)
const previewMatches = ref<Match[]>([])
const previewLoading = ref(false)
let previewLoaded = false

const stepLabels = ['Sport', 'Team', 'Leagues', 'Link']

const sportLabel = computed(
  () => sports.value.find(s => s.id === sportId.value)?.label ?? '',
)

let searchTimer: number | null = null

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') handleClose()
}

// Monotonic id per loadTeams call: the mount-time unfiltered load can race
// the search-debounced one (step 2 renders, and is typable, before the mount
// fetch resolves), and whichever *started* last must win regardless of which
// response arrives last.
let teamsRequestSeq = 0

async function loadTeams() {
  if (!sportId.value) return
  const seq = ++teamsRequestSeq
  teamsLoading.value = true
  try {
    const results = await fetchTeams({
      sport: sportId.value,
      q: search.value.trim() || undefined,
      limit: 30,
    })
    if (seq === teamsRequestSeq) teamResults.value = results
  } finally {
    if (seq === teamsRequestSeq) teamsLoading.value = false
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  // Locking scroll removes the scrollbar, which shrinks the viewport and
  // shifts everything left of it — pad the gap back in so nothing jumps.
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
  document.body.style.overflow = 'hidden'
  if (scrollbarWidth > 0) document.body.style.paddingRight = `${scrollbarWidth}px`
  // Sports load independently of everything below — assigned on arrival so
  // step 1 and step 2's "Search <sport> teams…" placeholder fill in as soon
  // as possible, and a failure here can't take the rest of the mount down
  // (nor surface as an unhandled rejection).
  fetchSports()
    .then((s) => { sports.value = s })
    .catch(() => { /* step 1 renders without cards; recovers on next open */ })
    .finally(() => { sportsLoading.value = false })

  try {
    if (!props.initialTeam && !props.initialSport && urlParams.sport && urlParams.team) {
      // Restoring a reload: `step`/`sportId` are already seeded from the
      // URL; this fills in the team object the seeded step renders.
      try {
        const team = await fetchTeam(urlParams.team, urlParams.sport)
        selectedTeam.value = team
        teamSlug.value = urlParams.team
        chosenLeagues.value = team.leagues.map((l) => l.slug)
      } catch {
        // Team no longer resolvable — drop back to picking one.
        step.value = 2
      }
    }

    if (sportId.value && !props.initialTeam) await loadTeams()
  } catch {
    // Teams fetch failed — step 2 shows its empty state; the wizard stays usable.
  } finally {
    // URL sync must come alive even when a fetch above failed, or the wizard
    // params in the URL go stale for the rest of the session.
    urlSyncReady.value = true
    syncUrl()
  }
})

watch([step, sportId, teamSlug], syncUrl)

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  document.body.style.paddingRight = ''
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
  submitting.value = true
  try {
    // Floors the loading state at the authored animation's length (spin +
    // phase copy + checkmark settle, see .icl-* in <style>) so a fast local
    // API can't cut the "grabbing data" moment short via the out-in
    // Transition — a fetch that resolves before the leave transition even
    // finishes would otherwise skip the loading branch entirely. Errors
    // still reject immediately; only the success path waits on this floor.
    const MIN_VISIBLE_MS = 2200
    const [link] = await Promise.all([
      fetchCalendarLink(sportId.value, teamSlug.value, chosenLeagues.value),
      new Promise((resolve) => setTimeout(resolve, MIN_VISIBLE_MS)),
    ])
    calLink.value = link
    step.value = 4
  } finally {
    submitting.value = false
  }
}

function formatMatchDate(iso: string): string {
  return new Date(iso).toLocaleDateString([], { month: 'short', day: 'numeric' })
}

async function togglePreview() {
  showPreview.value = !showPreview.value
  if (!showPreview.value || previewLoaded) return

  previewLoaded = true
  previewLoading.value = true
  try {
    const perLeague = await Promise.all(
      chosenLeagues.value.map((league) =>
        fetchMatches({ sport: sportId.value ?? undefined, league, team: teamSlug.value ?? undefined }),
      ),
    )
    const now = Date.now()
    previewMatches.value = perLeague
      .flat()
      .filter((m) => new Date(m.start_time).getTime() >= now)
      .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  } finally {
    previewLoading.value = false
  }
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
  showPreview.value = false
  previewMatches.value = []
  previewLoaded = false
  step.value = 1
}
</script>

<style scoped>
.modal-backdrop {
  /* Chromium quirk: an element with any active CSS `animation` stops
     correctly inheriting `color` (computes as transparent) unless it's set
     explicitly here — even though the animation itself only touches
     opacity. Reproduces mid-animation too, not just once "forwards" freezes
     it. Setting `color: inherit` sidesteps it. */
  color: inherit;
  animation: backdropIn 0.22s ease forwards;
}
.modal-backdrop.is-closing {
  animation: backdropIn 0.18s ease reverse forwards;
}
@keyframes backdropIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-panel {
  color: inherit; /* see .modal-backdrop comment above */
  animation: panelIn 0.32s cubic-bezier(0.2, 0.9, 0.3, 1) forwards;
}
.modal-panel.is-closing {
  animation: panelIn 0.18s ease reverse forwards;
}
@keyframes panelIn {
  from { opacity: 0; transform: translateY(14px) scale(0.98); }
  to { opacity: 1; transform: none; }
}

/* Steps cross-fade: the outgoing one leaves out of flow while the incoming one
   enters, and the viewport animates between their heights. mode="out-in" was
   the alternative and it showed — the body sat empty at the old step's height
   for the whole leave before the next step appeared. */
.step-viewport {
  /* One source for the body's inset: the leaving step is positioned against
     the padding box, so it has to re-apply the horizontal padding to stay
     aligned with the step that's replacing it. */
  --step-pad: 1.75rem;
  padding: 0 var(--step-pad) var(--step-pad);
  overflow: hidden;
  transition: height 0.28s cubic-bezier(0.77, 0, 0.175, 1);
}
/* Asymmetric on purpose. Enter and leave used to share one 0.2s ease, which
   read as a flash: the outgoing step and the incoming one moved at the same
   speed, so neither registered. The old step now clears quickly (accelerating
   away), and the new one takes noticeably longer on a decelerating curve —
   that's the half the eye actually tracks. */
.step-forward-leave-active,
.step-back-leave-active {
  position: absolute;
  top: 0;
  left: var(--step-pad);
  right: var(--step-pad);
  transition: opacity 0.16s ease-in, transform 0.16s ease-in;
}
.step-forward-enter-active,
.step-back-enter-active {
  transition:
    opacity 0.38s ease-out,
    transform 0.38s cubic-bezier(0.16, 0.84, 0.32, 1);
}
.step-forward-enter-from { opacity: 0; transform: translateX(36px); }
.step-forward-leave-to { opacity: 0; transform: translateX(-24px); }
.step-back-enter-from { opacity: 0; transform: translateX(-36px); }
.step-back-leave-to { opacity: 0; transform: translateX(24px); }

@media (prefers-reduced-motion: reduce) {
  .modal-backdrop,
  .modal-panel {
    animation: none;
  }
  .step-viewport,
  .step-forward-enter-active,
  .step-forward-leave-active,
  .step-back-enter-active,
  .step-back-leave-active {
    transition: none;
  }
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
}

.preview-enter-active,
.preview-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.preview-enter-from,
.preview-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── "Grabbing data" loading state (goToLink in flight) ─────────────────── */
.icl-badge {
  position: relative;
}

.icl-phases {
  position: relative;
}

.icl-check {
  position: absolute;
  inset: 0;
  margin: auto;
  opacity: 0;
}

@keyframes icl-check-in {
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes icl-fade-out {
  to {
    opacity: 0;
  }
}

.icl-check-1,
.icl-check-2,
.icl-check-3 {
  transform: scale(0.6);
  animation: icl-check-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) 1.75s forwards;
}

/* Opacity-based phase stack — variants 1 and 2 */
.icl-phase {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  animation: icl-phase-window 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.icl-phase-a {
  animation-delay: 0s;
}
.icl-phase-b {
  animation-delay: 0.85s;
}
.icl-phase-c {
  animation: icl-phase-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) 1.7s both;
}
@keyframes icl-phase-window {
  0% {
    opacity: 0;
    transform: translateY(6px);
  }
  15%,
  80% {
    opacity: 1;
    transform: none;
  }
  100% {
    opacity: 0;
    transform: translateY(-6px);
  }
}
@keyframes icl-phase-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* Radial spinner that settles into a checkmark once the calendar link is
   ready — 12 bars around the badge center, brightness sweeping clockwise via
   staggered negative animation-delays (classic "iOS activity indicator"
   technique), recolored to Signal Blue instead of grayscale. */
.icl-spinner {
  position: relative;
  width: 32px;
  height: 32px;
  animation: icl-fade-out 0.3s ease 1.75s forwards;
}
.icl-spinner-bar {
  position: absolute;
  top: 0;
  left: 50%;
  width: 3px;
  height: 9px;
  margin-left: -1.5px;
  border-radius: 2px;
  background: var(--ms-blue);
  transform-origin: 50% 16px;
  opacity: 0.15;
  animation: icl-spinner-fade 1.2s linear infinite;
}
@keyframes icl-spinner-fade {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0.15;
  }
}

@media (prefers-reduced-motion: reduce) {
  .icl-spinner {
    animation: none;
    opacity: 0.6;
  }
  .icl-spinner-bar {
    animation: none;
    opacity: 0.5;
  }
  .icl-phase-a,
  .icl-phase-b {
    display: none;
  }
  .icl-phase-c {
    position: static;
    animation: icl-phase-in 0.25s ease forwards;
  }
  .icl-check-1 {
    animation: icl-check-in 0.25s ease forwards;
  }
}

/* ── Close button: bare icon that lifts on hover and, in sync with the
   panel's own closing animation (`closing` ref), scales down with a slight
   rotation instead of just vanishing with the panel. ────────────────────── */
.xcl-btn-1 {
  background: transparent;
  border: none;
  transition: transform 0.15s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.15s ease;
}
.xcl-btn-1:hover {
  opacity: 0.7;
  transform: scale(1.08);
}
.xcl-btn-1:active {
  transform: scale(0.92);
}
.xcl-closing-1 {
  animation: xcl-close-1 0.16s cubic-bezier(0.4, 0, 1, 1) forwards;
}
@keyframes xcl-close-1 {
  to {
    transform: scale(0.65) rotate(-90deg);
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .xcl-btn-1:hover,
  .xcl-btn-1:active {
    transform: none;
  }
  .xcl-closing-1 {
    animation: none;
    opacity: 0.4;
  }
}

/* ── League picker delight: picking a league gives the card a satisfying
   overshoot pop (playful intensity) and the checkmark draws in with a
   stroke reveal instead of just popping into existence. ──────────────────── */
.lgd-card-1 {
  transition: transform 0.32s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.15s ease, background-color 0.15s ease;
}
.lgd-card-1-on {
  transform: scale(1.045);
}
.lgd-check-mark-1 {
  stroke-dasharray: 12;
  stroke-dashoffset: 12;
  animation: lgd-check-draw 0.28s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
@keyframes lgd-check-draw {
  to {
    stroke-dashoffset: 0;
  }
}
.lgd-check-1 {
  transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.15s ease, background-color 0.15s ease;
}
.lgd-check-1-on {
  transform: scale(1.15);
}

@media (prefers-reduced-motion: reduce) {
  .lgd-card-1,
  .lgd-card-1-on,
  .lgd-check-1,
  .lgd-check-1-on {
    transform: none !important;
    transition: opacity 0.15s ease, color 0.15s ease !important;
  }
  .lgd-check-mark-1 {
    animation: none;
    stroke-dashoffset: 0;
  }
}

</style>
