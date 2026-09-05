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

      <div class="relative flex items-center justify-between px-7 pt-7 pb-5 border-b border-white/10">
        <div>
          <div class="text-[11.5px] font-bold uppercase mb-1 ms-text-accent" style="letter-spacing: 1.8px">Step {{ step }} of 4</div>
          <h2 class="text-2xl font-extrabold" style="letter-spacing: -0.5px">{{ stepLabels[step - 1] }}</h2>
        </div>
        <button
          class="xcl-btn-1 w-11 h-11 rounded-full flex items-center justify-center"
          :class="{ 'xcl-closing-1': closing }"
          @click="handleClose"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round">
            <path class="xcl-cross-a" d="M6 6 18 18"/>
            <path class="xcl-cross-b" d="M18 6 6 18"/>
          </svg>
        </button>
      </div>

      <StepIndicator :current-step="step" :labels="stepLabels" />

      <div ref="stepViewport" class="relative step-viewport" :class="{ 'is-revealing': revealTransition }">
      <Transition
        :name="stepTransitionName"
        @enter="growViewportTo"
        @after-enter="releaseViewportHeight"
        @enter-cancelled="releaseViewportHeight"
      >
        <CalendarLinkLoading v-if="submitting" key="submitting" />

        <SportStep
          v-else-if="step === 1"
          key="step1"
          :sports="sports"
          :sports-loading="sportsLoading"
          :selected-sport-id="sportId"
          @select="selectSport"
          @continue="goToTeams"
        />

        <TeamStep
          v-else-if="step === 2"
          key="step2"
          :sport-label="sportLabel"
          :search="search"
          :teams-loading="teamsLoading"
          :team-results="teamResults"
          :selected-team-slug="teamSlug"
          @back="step = 1"
          @update:search="search = $event"
          @select="selectTeam"
          @continue="goToLeagues"
        />

        <LeaguesStep
          v-else-if="step === 3 && selectedTeam"
          key="step3"
          :team="selectedTeam"
          :chosen-leagues="chosenLeagues"
          @back="goBackToTeams"
          @update:chosen-leagues="chosenLeagues = $event"
          @continue="goToLink"
        />

        <LinkStep
          v-else-if="step === 4 && calLink"
          key="step4"
          :cal-link="calLink"
          :show-preview="showPreview"
          :preview-loading="previewLoading"
          :preview-matches="previewMatches"
          @back="step = 3"
          @copy="handleCopy"
          @toggle-preview="togglePreview"
          @reset="reset"
        />

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
import StepIndicator from './team-selector/StepIndicator.vue'
import CalendarLinkLoading from './team-selector/CalendarLinkLoading.vue'
import SportStep from './team-selector/SportStep.vue'
import TeamStep from './team-selector/TeamStep.vue'
import LeaguesStep from './team-selector/LeaguesStep.vue'
import LinkStep from './team-selector/LinkStep.vue'

const props = defineProps<{
  initialSport?: string | null
  initialTeam?: Team | null
}>()

const emit = defineEmits<{ close: [] }>()

const route = useRoute()
const router = useRouter()
const urlSyncReady = ref(false)

function syncWizardStateToUrl() {
  if (!urlSyncReady.value) return
  const query: Record<string, string> = { ...(route.query as Record<string, string>) }
  query.wstep = String(step.value)
  if (sportId.value) query.wsport = sportId.value
  else delete query.wsport
  if (teamSlug.value) query.wteam = teamSlug.value
  else delete query.wteam
  router.replace({ query })
}

function firstQueryParam(v: unknown): string | null {
  const raw = Array.isArray(v) ? v[0] : v
  return typeof raw === 'string' && raw ? raw : null
}
const urlParams = {
  step: Number(firstQueryParam(route.query.wstep) ?? NaN),
  sport: firstQueryParam(route.query.wsport),
  team: firstQueryParam(route.query.wteam),
}

function resolveInitialStep(): number {
  if (props.initialTeam) return 3
  if (props.initialSport) return 2
  if (urlParams.sport && urlParams.team) return urlParams.step === 2 ? 2 : 3
  if (urlParams.sport) return 2
  return 1
}

const step = ref(resolveInitialStep())
const stepDirection = ref<'forward' | 'back'>('forward')
const revealTransition = ref(false)
const stepTransitionName = computed(() =>
  revealTransition.value ? 'step-reveal' : `step-${stepDirection.value}`,
)
watch(step, (next, prev) => {
  stepDirection.value = next >= prev ? 'forward' : 'back'
}, { flush: 'sync' })

const closing = ref(false)
const CLOSE_ANIMATION_MS = 180
function handleClose() {
  if (closing.value) return
  closing.value = true
  setTimeout(() => emit('close'), CLOSE_ANIMATION_MS)
}

const sportId = ref<string | null>(
  props.initialTeam?.sport ?? props.initialSport ?? urlParams.sport,
)
const teamSlug = ref<string | null>(props.initialTeam?.slug ?? null)
const selectedTeam = ref<Team | null>(props.initialTeam ?? null)
const chosenLeagues = ref<string[]>(props.initialTeam?.leagues.map((l) => l.slug) ?? [])
const search = ref('')
const copied = ref(false)

const sports = ref<Sport[]>([])
const sportsLoading = ref(true)
const teamResults = ref<Team[]>([])
const teamsLoading = ref(!props.initialTeam && !!sportId.value)
const calLink = ref<CalendarLink | null>(null)
const submitting = ref(false)

const stepViewport = ref<HTMLElement | null>(null)

watch([step, submitting], () => {
  const vp = stepViewport.value
  if (vp) vp.style.height = `${vp.offsetHeight}px`
}, { flush: 'sync' })

function growViewportTo(el: Element) {
  const vp = stepViewport.value
  if (!vp) return
  const style = getComputedStyle(vp)
  const pad = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom)
  void vp.offsetHeight
  vp.style.height = `${(el as HTMLElement).offsetHeight + pad}px`
}

function releaseViewportHeight() {
  const vp = stepViewport.value
  if (vp) vp.style.height = ''
  revealTransition.value = false
}

const showPreview = ref(false)
const previewMatches = ref<Match[]>([])
const previewLoading = ref(false)
let previewAlreadyLoaded = false

const stepLabels = ['Sport', 'Team', 'Leagues', 'Link']

const sportLabel = computed(
  () => sports.value.find(s => s.id === sportId.value)?.label ?? '',
)

let searchDebounceTimer: number | null = null

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') handleClose()
}

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
  window.addEventListener('keydown', onKeydown)
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
  document.body.style.overflow = 'hidden'
  if (scrollbarWidth > 0) document.body.style.paddingRight = `${scrollbarWidth}px`
  fetchSports()
    .then((s) => { sports.value = s })
    .catch(() => {})
    .finally(() => { sportsLoading.value = false })

  try {
    if (!props.initialTeam && !props.initialSport && urlParams.sport && urlParams.team) {
      try {
        const team = await fetchTeam(urlParams.team, urlParams.sport)
        selectedTeam.value = team
        teamSlug.value = urlParams.team
        chosenLeagues.value = team.leagues.map((l) => l.slug)
      } catch {
        step.value = 2
      }
    }

    if (sportId.value && !props.initialTeam) await loadTeams()
  } catch {
    // step 2 shows its own empty state
  } finally {
    urlSyncReady.value = true
    syncWizardStateToUrl()
  }
})

watch([step, sportId, teamSlug], syncWizardStateToUrl)

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
  document.body.style.paddingRight = ''
  if (searchDebounceTimer !== null) window.clearTimeout(searchDebounceTimer)
})

watch(search, () => {
  if (step.value !== 2) return
  if (searchDebounceTimer !== null) window.clearTimeout(searchDebounceTimer)
  searchDebounceTimer = window.setTimeout(loadTeams, 200)
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
  if (teamResults.value.length === 0 && sportId.value) {
    await loadTeams()
  }
  step.value = 2
}

async function goToLeagues() {
  if (!teamSlug.value || !sportId.value) return
  if (!selectedTeam.value || selectedTeam.value.slug !== teamSlug.value) {
    selectedTeam.value = await fetchTeam(teamSlug.value, sportId.value)
    chosenLeagues.value = selectedTeam.value.leagues.map(l => l.slug)
  }
  step.value = 3
}

// Matches CalendarLinkLoading.css's checkmark-settle timing (1.75s + 0.4s).
const MIN_LOADING_ANIMATION_MS = 2200

async function goToLink() {
  if (!sportId.value || !teamSlug.value || chosenLeagues.value.length === 0) return
  submitting.value = true
  try {
    const [link] = await Promise.all([
      fetchCalendarLink(sportId.value, teamSlug.value, chosenLeagues.value),
      new Promise((resolve) => setTimeout(resolve, MIN_LOADING_ANIMATION_MS)),
    ])
    calLink.value = link
    revealTransition.value = true
    step.value = 4
  } finally {
    submitting.value = false
  }
}

async function togglePreview() {
  showPreview.value = !showPreview.value
  if (!showPreview.value || previewAlreadyLoaded) return

  previewAlreadyLoaded = true
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
  previewAlreadyLoaded = false
  step.value = 1
}
</script>

<style scoped src="./TeamSelectorModal.css"></style>
