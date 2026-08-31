<template>
  <section class="relative px-4 sm:px-6 pt-8 sm:pt-14 pb-6">
    <!-- Stacked below lg, side by side above it. The split only turns on at
         lg because the fixture card has a 26rem floor: at md there isn't
         enough left over for the headline to sit beside it without the
         measure collapsing to a few words a line. -->
    <div class="max-w-5xl mx-auto lg:grid lg:grid-cols-2 lg:gap-12 lg:items-center">
      <!-- While stacked, the headline is capped to the fixture card's own
           26rem and centred, so the two read as one column instead of
           full-width text sitting above a narrow centred card. Phones are
           already narrower than the cap, so it only bites on tablets. The
           cap is dropped at lg, where the headline owns half the grid. -->
      <div class="hero-headline max-w-[26rem] mx-auto lg:max-w-none lg:mx-0 mb-8 sm:mb-10 lg:mb-0">
        <div class="hero-eyebrow">Next kickoff</div>
        <h1 class="hero-title">
          <span>Every match.</span>
          <span>One calendar.</span>
        </h1>
        <p class="hero-subtitle">
          Follow your clubs across every competition, get reminders before kickoff and sync fixtures straight to your calendar for free.
        </p>
      </div>

      <!-- Featured fixture: rotates through the top featured fixtures, or a
           generic promo card when nothing scores high enough. One card at
           every width — it's responsive internally rather than swapped for a
           separate headline+preview split. -->
      <FixtureHeroPanel
        :matches="featuredMatches"
        :loading="featuredLoading"
        @get-started="emit('getStarted')"
      />
    </div>

    <!-- TEAM PICKER PANEL -->
    <!-- Extra top margin once the hero splits into two columns: the picker
         sits under a wider, shorter block there, so the gap that reads as
         "next section" on a phone reads as cramped on a desktop. -->
    <div class="relative flex justify-center mt-10 sm:mt-14 lg:mt-20">
      <div class="glass-panel relative w-full max-w-xl rounded-[28px] p-5 sm:p-6 overflow-hidden">
        <div
          class="absolute inset-0 pointer-events-none"
          style="background: linear-gradient(115deg, rgba(255,255,255,.055) 0%, rgba(255,255,255,.02) 30%, transparent 46%)"
        ></div>

        <!-- Sport tabs — horizontally scrollable so 4+ sports don't get
             squeezed into unreadable equal-width columns on a phone. Scroll-
             snap so a swipe settles on a tab instead of stopping mid-way, and
             a fading chevron on the right hints that it scrolls at all. -->
        <div class="relative mb-3.5">
          <div
            ref="sportTabsScrollEl"
            class="relative flex gap-1 rounded-[14px] p-1.5 overflow-x-auto ms-no-scrollbar"
            :class="showSportsScrollHint ? 'justify-start' : 'justify-center'"
            style="scroll-snap-type: x mandatory"
          >
            <div class="ms-tab-slider ms-tab-slider--outline" :style="sportSliderStyle"></div>
            <button
              v-for="s in sports"
              :key="s.id"
              ref="sportTabRefs"
              class="relative z-[1] flex-shrink-0 whitespace-nowrap text-center text-sm py-2.5 px-4 rounded-[11px] font-semibold transition-colors"
              :class="sportFilter === s.id ? 'text-[var(--ms-text)]' : 'text-[rgba(244,247,251,.55)] hover:text-[var(--ms-text)]'"
              style="scroll-snap-align: start"
              @click="onSportTabClick(s.id)"
            >
              {{ s.label }}
            </button>
          </div>
          <div
            v-if="showSportsScrollHint"
            class="absolute right-0 top-0 bottom-0 w-9 rounded-r-[14px] pointer-events-none flex items-center justify-end pr-1.5"
            style="background: linear-gradient(to right, transparent, rgba(20,28,45,.75) 65%)"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(244,247,251,.6)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 6 15 12 9 18"/></svg>
          </div>
        </div>

        <!-- Search -->
        <div class="relative flex items-center gap-2 rounded-xl px-3.5 mb-3.5">
          <span style="color: rgba(244,247,251,.45)">
            <Icon name="search" class="!w-[15px] !h-[15px]" />
          </span>
          <input
            v-model="search"
            type="text"
            placeholder="Search teams and leagues"
            class="flex-1 bg-transparent border-none outline-none text-[13.5px] py-2.5"
            style="color: var(--ms-text)"
          />
        </div>

        <!-- Team grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-4 max-h-72 overflow-y-auto">
          <!-- Only on the very first load. Re-filtering by sport or search
               keeps the current results on screen instead of blanking the
               grid to skeletons on every keystroke.
               The `!teams.length` half is belt-and-braces: whatever the flag
               says, a placeholder must never sit next to a real result. -->
          <div
            v-for="n in 6"
            v-show="teamsFirstLoad && !teams.length"
            :key="`team-skeleton-${n}`"
            class="rounded-xl border border-white/[0.08] px-3 py-2.5 flex items-center gap-2.5"
            aria-hidden="true"
          >
            <span class="ms-skeleton flex-none" style="width: 30px; height: 30px; border-radius: 9px"></span>
            <div class="min-w-0 flex-1">
              <span class="ms-skeleton block" style="width: 68%; height: 13px"></span>
              <span class="ms-skeleton block" style="width: 45%; height: 10px; margin-top: 6px"></span>
            </div>
          </div>
          <button
            v-for="t in teams"
            :key="`${t.sport}-${t.slug}`"
            class="team-card rounded-xl border px-3 py-2.5 text-left transition-all flex items-center gap-2.5"
            :class="{ selected: selectedTeam?.slug === t.slug && selectedTeam?.sport === t.sport }"
            @click="onTeamClick(t)"
          >
            <TeamBadge :name="t.name" :icon="t.icon" :size="30" />
            <div class="min-w-0">
              <div class="font-bold text-[13.5px] truncate">{{ t.name }}</div>
              <div class="text-[11px] font-semibold mt-0.5 truncate" style="color: rgba(244,247,251,.5)">
                {{ t.leagues.map(l => l.name).join(' · ') }}
              </div>
            </div>
          </button>
          <div
            v-if="!loading && !teamsFirstLoad && teams.length === 0"
            class="col-span-2 flex items-center justify-center text-sm py-8"
            style="color: var(--ms-muted)"
          >
            {{ search ? `No teams match "${search}"` : 'No teams available' }}
          </div>
        </div>

        <button
          class="ms-btn-primary rounded-2xl w-full py-4 font-bold text-[15px] disabled:opacity-40"
          :disabled="!selectedTeam"
          @click="onPrimaryClick"
        >
          Get my calendar link
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import type { Sport, Team } from '@/types'
import { fetchSports, fetchTeams } from '@/services/sports'
import { cachedFeaturedMatches, refreshFeaturedMatch } from '@/services/featuredMatchCache'
import Icon from './Icon.vue'
import TeamBadge from './TeamBadge.vue'
import FixtureHeroPanel from './FixtureHeroPanel.vue'

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

// Featured match, scored server-side (live > imminent kickoff > recent result,
// weighted by league + Swedish-audience boost). Falls back to a generic
// "more matches today" promo card when nothing in the DB scores high enough
// (e.g. dead period, or the request fails). Cached at module scope so
// switching tabs and back doesn't flash the fallback while a fresh fetch resolves.
const featuredMatches = computed(() => cachedFeaturedMatches.value ?? [])
// The cache distinguishes "never fetched" (undefined) from "fetched, nothing
// scored high enough" ([]) — only the former is a loading state. Without this
// the panel briefly renders its "More matches today" fallback on first paint,
// which reads as a real (wrong) answer rather than as pending.
const featuredLoading = computed(() => cachedFeaturedMatches.value === undefined)

let searchTimer: number | null = null

// True only until the first team fetch resolves — see the skeleton in the
// grid for why later fetches don't re-enter this state.
const teamsFirstLoad = ref(true)

async function loadTeams() {
  loading.value = true
  try {
    teams.value = await fetchTeams({
      sport: sportFilter.value ?? undefined,
      q: search.value.trim() || undefined,
      limit: 8,
    })
  } finally {
    teamsFirstLoad.value = false
    loading.value = false
  }
}

const sportTabRefs = ref<HTMLElement[]>([])
const sportTabsScrollEl = ref<HTMLElement | null>(null)
// top/bottom override the shared .ms-tab-slider's 4px inset (tuned for
// Navbar.vue's p-1 container) to match this row's larger p-1.5 padding.
const sportSliderStyle = reactive({ width: '0px', transform: 'translateX(0px)', opacity: '0', top: '6px', bottom: '6px' })
// Only meaningful (and only shown) once the tabs actually overflow — on a
// wide screen all of them fit already, so there's nothing to hint at.
const showSportsScrollHint = ref(false)

function updateSportSlider() {
  const i = sports.value.findIndex((s) => s.id === sportFilter.value)
  const el = i === -1 ? null : sportTabRefs.value[i]
  if (!el) return
  sportSliderStyle.width = `${el.offsetWidth}px`
  sportSliderStyle.transform = `translateX(${el.offsetLeft}px)`
  sportSliderStyle.opacity = '1'
}

function updateSportsScrollHint() {
  const el = sportTabsScrollEl.value
  showSportsScrollHint.value = !!el && el.scrollWidth > el.clientWidth + 1
}

// One frame isn't always enough — layout can still be settling right after
// nextTick, so measure again on the following frame.
function updateSportSliderNextFrame() {
  requestAnimationFrame(() => requestAnimationFrame(() => {
    updateSportSlider()
    updateSportsScrollHint()
  }))
}

onMounted(async () => {
  sports.value = await fetchSports()
  if (sports.value.length > 0) sportFilter.value = sports.value[0].id
  await loadTeams()
  await nextTick()
  updateSportSliderNextFrame()
  window.addEventListener('resize', updateSportSlider)
  window.addEventListener('resize', updateSportsScrollHint)
  // Cached value (if any) is already showing instantly; this just keeps it fresh.
  refreshFeaturedMatch()
})

watch(sportFilter, async () => {
  selectedTeam.value = null
  loadTeams()
  await nextTick()
  updateSportSliderNextFrame()
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

<style scoped>
/* Dark tile with a blue underline instead of the navbar's filled-pill
   active state — reads better against this row's already-transparent
   background (see the "remove the bg" change above). */
.ms-tab-slider--outline {
  background: transparent;
  border: none;
  box-shadow: none;
}

/* A separate flat-edged bar rather than the tile's own border-bottom — the
   tile is rounded, so a border there would bow with its corners instead of
   sitting as a straight line. */
.ms-tab-slider--outline::after {
  content: '';
  position: absolute;
  left: 22%;
  right: 22%;
  bottom: 0;
  height: 2px;
  background: var(--ms-blue);
}

.hero-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ms-blue);
  margin-bottom: 10px;
}

.hero-title {
  font-size: clamp(32px, 6vw, 52px);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1;
  color: var(--ms-text);
}

.hero-title span {
  display: block;
}

.hero-subtitle {
  font-size: 16px;
  font-weight: 500;
  color: var(--ms-muted);
  max-width: 30rem;
  margin: 16px 0 0;
  line-height: 1.5;
}
</style>
