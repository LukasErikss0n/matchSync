<template>
  <section class="relative px-4 sm:px-6 pt-8 sm:pt-14 pb-6">
    <!-- MOBILE: headline + compact badge share the top row -->
    <div class="lg:hidden max-w-5xl mx-auto">
      <div class="grid gap-3" style="grid-template-columns: 1fr 132px">
        <div>
          <p class="text-[11px] font-bold uppercase mb-2.5 ms-text-accent" style="letter-spacing: 0.15em">
            Auto-sync
          </p>
          <h1 class="text-[29px] font-extrabold leading-[1.08]" style="letter-spacing: -0.02em">
            The whole season.<br />One subscription.
          </h1>
        </div>
        <!-- compact pastel badge: both crests + VS chip, or a generic promo when nothing's featured -->
        <div class="relative flex-none w-[132px] h-[132px] rounded-[22px] overflow-hidden border border-white/20 flex items-center justify-center gap-1.5">
          <div class="absolute inset-0" style="background: linear-gradient(160deg, #bfe2f7 0%, #8ecdf2 55%, #5eb2e6 100%)"></div>
          <div class="absolute inset-0" style="background: linear-gradient(118deg, rgba(255,255,255,.5) 0 50%, transparent 50%)"></div>
          <template v-if="hasFeatured">
            <TeamBadge class="relative flex-none" :name="spotlight.homeTeam" :icon="spotlight.homeIcon" :size="42" />
            <div
              class="relative flex-none w-[22px] h-[22px] rounded-md flex items-center justify-center font-black text-[8px] italic"
              style="background: rgba(11,26,43,.55); border: 1px solid rgba(255,255,255,.5); backdrop-filter: blur(8px); color: #f4f7fb"
            >
              VS
            </div>
            <TeamBadge class="relative flex-none" :name="spotlight.awayTeam" :icon="spotlight.awayIcon" :size="42" />
          </template>
          <div
            v-else
            class="relative w-14 h-14 rounded-2xl flex items-center justify-center"
            style="background: rgba(255,255,255,.32); border: 1.5px solid rgba(255,255,255,.7); backdrop-filter: blur(8px); box-shadow: 0 10px 20px -8px rgba(9,30,50,.45), inset 0 1px 0 rgba(255,255,255,.6)"
          >
            <Icon name="calendar" class="!w-6 !h-6" style="color: white" />
          </div>
        </div>
      </div>

      <RouterLink
        v-if="!hasFeatured"
        to="/matches"
        class="flex items-center gap-3.5 rounded-2xl px-4 py-3.5 mt-3.5 glass-panel"
      >
        <div class="min-w-0">
          <div class="text-sm font-bold">More matches today</div>
          <div class="text-[11.5px] font-semibold mt-0.5" style="color: rgba(244,247,251,.55)">Browse every league and fixture</div>
        </div>
      </RouterLink>
      <div v-else class="flex items-center gap-3.5 rounded-2xl px-4 py-3.5 mt-3.5 glass-panel">
        <div class="w-12 text-center flex-shrink-0">
          <div class="text-[15px] font-extrabold">{{ spotlight.timeLabel }}</div>
          <div class="text-[10.5px] font-semibold mt-px" style="color: rgba(244,247,251,.55)">{{ spotlight.dayLabel }}</div>
        </div>
        <div class="min-w-0">
          <div class="text-sm font-bold truncate">{{ spotlight.homeTeam }} – {{ spotlight.awayTeam }}</div>
          <div class="text-[11.5px] font-semibold mt-0.5 truncate" style="color: rgba(244,247,251,.55)">{{ spotlight.leagueName }}</div>
        </div>
      </div>

      <p class="text-[15px] font-medium mt-3.5 leading-relaxed" style="color: var(--ms-muted)">
        Pick your team and get a live calendar link. Rescheduled matches, playoffs and cups, everything updates itself for free.
      </p>

      <div class="flex flex-col gap-3 mt-5.5">
        <button
          class="ms-btn-primary rounded-2xl py-3.5 font-bold text-[16px] flex items-center justify-center gap-2"
          @click="emit('getStarted')"
        >
          <Icon name="calendar" class="!w-[18px] !h-[18px]" />
          Choose your team
        </button>
        <RouterLink
          :to="seeAllRoute"
          class="ms-btn-secondary rounded-2xl py-3.5 font-bold text-[16px] text-center"
        >
          See all matches
        </RouterLink>
      </div>

      <div class="flex justify-center gap-2 mt-5.5 flex-wrap">
        <div class="glass-panel rounded-[14px] px-3.5 py-2.5 text-center">
          <div class="text-[15px] font-extrabold">13+</div>
          <div class="text-[10.5px] font-semibold uppercase tracking-wide mt-0.5" style="color: var(--ms-muted-dim)">Leagues</div>
        </div>
        <div class="glass-panel rounded-[14px] px-3.5 py-2.5 text-center">
          <div class="text-[15px] font-extrabold">3</div>
          <div class="text-[10.5px] font-semibold uppercase tracking-wide mt-0.5" style="color: var(--ms-muted-dim)">Sports</div>
        </div>
        <div class="glass-panel rounded-[14px] px-3.5 py-2.5 text-center">
          <div class="text-[15px] font-extrabold">1 min</div>
          <div class="text-[10.5px] font-semibold uppercase tracking-wide mt-0.5" style="color: var(--ms-muted-dim)">To get started</div>
        </div>
      </div>
    </div>

    <!-- DESKTOP: side-by-side split hero -->
    <div class="hidden lg:grid lg:grid-cols-2 gap-14 items-center max-w-5xl mx-auto">
      <div>
        <p class="text-[13px] font-bold uppercase mb-3.5 ms-text-accent" style="letter-spacing: 0.18em">
          Always up to date &nbsp;·&nbsp; Auto-sync
        </p>
        <h1
          class="text-5xl font-extrabold leading-[1.05] mb-4"
          style="letter-spacing: -0.02em"
        >
          The whole season.<br />One subscription.
        </h1>
        <p class="text-base font-medium mb-7 max-w-md leading-relaxed" style="color: var(--ms-muted)">
          Pick your team and get a live calendar link. Rescheduled matches and playoffs, everything updates itself.
        </p>
        <div class="flex flex-row gap-3">
          <button
            class="ms-btn-primary rounded-2xl px-6 py-3.5 font-bold text-[15px] flex items-center justify-center gap-2"
            @click="emit('getStarted')"
          >
            <Icon name="calendar" class="!w-[18px] !h-[18px]" />
            Choose your team
          </button>
          <RouterLink
            :to="seeAllRoute"
            class="ms-btn-secondary rounded-2xl px-6 py-3.5 font-bold text-[15px] text-center"
          >
            See all matches
          </RouterLink>
        </div>
        <div class="flex gap-2 mt-8 flex-wrap">
          <div class="glass-panel rounded-2xl px-4 py-3 text-center">
            <div class="text-[15px] font-extrabold">13+</div>
            <div class="text-[10.5px] font-semibold uppercase tracking-wide mt-0.5" style="color: var(--ms-muted-dim)">Leagues</div>
          </div>
          <div class="glass-panel rounded-2xl px-4 py-3 text-center">
            <div class="text-[15px] font-extrabold">3</div>
            <div class="text-[10.5px] font-semibold uppercase tracking-wide mt-0.5" style="color: var(--ms-muted-dim)">Sports</div>
          </div>
          <div class="glass-panel rounded-2xl px-4 py-3 text-center">
            <div class="text-[15px] font-extrabold">1 min</div>
            <div class="text-[10.5px] font-semibold uppercase tracking-wide mt-0.5" style="color: var(--ms-muted-dim)">To get started</div>
          </div>
        </div>
      </div>

      <!-- Pastel stage: real featured match, or a generic promo card when nothing's featured -->
      <div class="relative rounded-[28px] overflow-hidden h-[340px] border border-white/15">
        <div
          class="absolute inset-0"
          style="background: linear-gradient(160deg, #bfe2f7 0%, #8ecdf2 60%, #5eb2e6 100%)"
        ></div>
        <div
          class="absolute inset-0"
          style="background: linear-gradient(118deg, rgba(255,255,255,.5) 0 50%, transparent 50%)"
        ></div>
        <template v-if="hasFeatured">
          <div class="absolute left-1/2 top-[38%] -translate-x-1/2 -translate-y-1/2 flex items-center gap-4">
            <TeamBadge :name="spotlight.homeTeam" :icon="spotlight.homeIcon" :size="96" />
            <div
              class="flex-none w-11 h-11 rounded-2xl flex items-center justify-center font-black text-sm italic"
              style="background: rgba(11,26,43,.55); border: 1px solid rgba(255,255,255,.5); backdrop-filter: blur(8px); color: #f4f7fb"
            >
              VS
            </div>
            <TeamBadge :name="spotlight.awayTeam" :icon="spotlight.awayIcon" :size="96" />
          </div>
          <div
            class="absolute left-3.5 right-3.5 bottom-3.5 flex items-center gap-3.5 rounded-2xl px-4 py-3.5"
            style="background: rgba(11,26,43,.55); border: 1px solid rgba(255,255,255,.2); backdrop-filter: blur(20px)"
          >
            <div class="w-13 text-center flex-shrink-0">
              <div class="text-base font-extrabold">{{ spotlight.timeLabel }}</div>
              <div class="text-[11px] font-semibold mt-0.5" style="color: rgba(244,247,251,.55)">{{ spotlight.dayLabel }}</div>
            </div>
            <div class="min-w-0">
              <div class="text-[15px] font-bold truncate">{{ spotlight.homeTeam }} – {{ spotlight.awayTeam }}</div>
              <div class="text-xs font-semibold mt-0.5" style="color: rgba(244,247,251,.55)">{{ spotlight.leagueName }}</div>
            </div>
          </div>
        </template>
        <template v-else>
          <div
            class="absolute left-1/2 top-[38%] -translate-x-1/2 -translate-y-1/2 w-[110px] h-[110px] rounded-[24px] flex items-center justify-center"
            style="background: rgba(255,255,255,.30); border: 1.5px solid rgba(255,255,255,.65); backdrop-filter: blur(10px); box-shadow: 0 30px 50px -18px rgba(9,30,50,.45), inset 0 1px 0 rgba(255,255,255,.6)"
          >
            <Icon name="calendar" class="!w-10 !h-10" style="color: white" />
          </div>
          <RouterLink
            to="/matches"
            class="absolute left-3.5 right-3.5 bottom-3.5 flex items-center rounded-2xl px-4 py-3.5"
            style="background: rgba(11,26,43,.55); border: 1px solid rgba(255,255,255,.2); backdrop-filter: blur(20px)"
          >
            <div class="min-w-0">
              <div class="text-[15px] font-bold">More matches today</div>
              <div class="text-xs font-semibold mt-0.5" style="color: rgba(244,247,251,.55)">Browse every league and fixture</div>
            </div>
          </RouterLink>
        </template>
      </div>
    </div>

    <!-- TEAM PICKER PANEL -->
    <div class="relative flex justify-center mt-10 sm:mt-14">
      <div class="glass-panel relative w-full max-w-xl rounded-[28px] p-5 sm:p-6 overflow-hidden">
        <div
          class="absolute inset-0 pointer-events-none"
          style="background: linear-gradient(115deg, rgba(255,255,255,.055) 0%, rgba(255,255,255,.02) 30%, transparent 46%)"
        ></div>

        <!-- Sport tabs -->
        <div class="relative flex rounded-[14px] p-1 mb-3.5 bg-white/[0.08] border border-white/[0.14]">
          <button
            v-for="s in sports"
            :key="s.id"
            class="relative flex-1 text-center text-sm py-2.5 rounded-[11px] font-semibold transition-colors"
            :class="sportFilter === s.id ? 'text-[var(--ms-text)]' : 'text-[rgba(244,247,251,.55)] hover:text-[var(--ms-text)]'"
            :style="sportFilter === s.id
              ? 'background: rgba(142,205,242,.18); border: 1px solid rgba(142,205,242,.35); box-shadow: inset 0 1px 0 rgba(255,255,255,.14)'
              : ''"
            @click="onSportTabClick(s.id)"
          >
            {{ s.label }}
          </button>
        </div>

        <!-- Search -->
        <div class="relative flex items-center gap-2.5 rounded-[14px] px-4 mb-3.5 bg-white/[0.08] border border-white/[0.16]">
          <span style="color: rgba(244,247,251,.55)">
            <Icon name="search" class="!w-[17px] !h-[17px]" />
          </span>
          <input
            v-model="search"
            type="text"
            placeholder="Search team or league…"
            class="flex-1 bg-transparent border-none outline-none text-[15px] py-3.5"
            style="color: var(--ms-text)"
          />
        </div>

        <!-- Team grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-4 max-h-72 overflow-y-auto">
          <button
            v-for="t in teams"
            :key="`${t.sport}-${t.slug}`"
            class="team-card rounded-2xl border-2 px-3.5 py-3 text-left transition-all flex items-center gap-3"
            :class="{ selected: selectedTeam?.slug === t.slug && selectedTeam?.sport === t.sport }"
            @click="onTeamClick(t)"
          >
            <TeamBadge :name="t.name" :icon="t.icon" :size="34" />
            <div class="min-w-0">
              <div class="font-bold text-[14.5px] truncate">{{ t.name }}</div>
              <div class="text-xs font-semibold mt-0.5 truncate" style="color: rgba(244,247,251,.5)">
                {{ t.leagues.map(l => l.name).join(' · ') }}
              </div>
            </div>
          </button>
          <div
            v-if="!loading && teams.length === 0"
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
import { ref, computed, watch, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import type { Sport, Team } from '@/types'
import { fetchSports, fetchTeams } from '@/services/sports'
import { cachedFeaturedMatch, refreshFeaturedMatch } from '@/services/featuredMatchCache'
import Icon from './Icon.vue'
import TeamBadge from './TeamBadge.vue'

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
const hasFeatured = computed(() => !!cachedFeaturedMatch.value)

function dayLabelFor(iso: string): string {
  const start = new Date(iso)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const that = new Date(start)
  that.setHours(0, 0, 0, 0)
  const diffDays = Math.round((that.getTime() - today.getTime()) / 86_400_000)
  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'tomorrow'
  if (diffDays === -1) return 'yesterday'
  return start.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })
}

// Only meaningful when hasFeatured is true — templates guard on that first.
const spotlight = computed(() => {
  const m = cachedFeaturedMatch.value!
  return {
    homeTeam: m.home_team,
    awayTeam: m.away_team,
    leagueName: m.league.name,
    leagueSlug: m.league.slug,
    timeLabel: new Date(m.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
    dayLabel: dayLabelFor(m.start_time),
    homeIcon: m.home_icon ?? null,
    awayIcon: m.away_icon ?? null,
  }
})

// "See all matches" should always land on the league the hero is currently
// showing — not whatever the user last browsed to on the Matches page.
const seeAllRoute = computed(() =>
  hasFeatured.value ? { path: '/matches', query: { league: spotlight.value.leagueSlug } } : '/matches',
)

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
  // Cached value (if any) is already showing instantly; this just keeps it fresh.
  refreshFeaturedMatch()
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
