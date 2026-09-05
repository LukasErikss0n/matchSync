<template>
  <div>
    <div class="admin-topbar">
      <div>
        <div class="admin-crumbs"><b>Admin</b><span class="sep">/</span>Leagues</div>
        <h1>Leagues</h1>
      </div>
      <div class="admin-topbar-right">
        <RouterLink class="admin-btn admin-btn-ghost" to="/admin">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12l9-9 9 9"/><path d="M5 10v10h14V10"/></svg>
          Back to analytics
        </RouterLink>
      </div>
    </div>

    <section class="admin-stats">
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Leagues catalogued</div>
        <div class="admin-stat-value mono">{{ catalogLoading ? '—' : fmtNum(allLeagues.length) }}</div>
        <div class="admin-stat-meta"><span>across {{ sportCount }} sports</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Leagues with subscribers</div>
        <div class="admin-stat-value mono">{{ fmtNum(subscribedLeagues.length) }}</div>
        <div class="admin-stat-meta"><span>at least 1 subscriber</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Total subscribers</div>
        <div class="admin-stat-value mono">{{ fmtNum(totalSubs) }}</div>
        <div class="admin-stat-meta"><span>league memberships, aggregated</span></div>
      </div>
      <div class="admin-stat" v-if="topLeague">
        <div class="admin-stat-label"><span class="dot"></span>Top league</div>
        <div class="admin-stat-value" style="font-size: 20px;">{{ topLeague.league }}</div>
        <div class="admin-stat-meta"><span>{{ topLeague.subscribers }} subs</span></div>
      </div>
    </section>

    <div class="admin-filter-bar">
      <div class="admin-search-input">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
        <input v-model="search" placeholder="Search leagues…" />
      </div>
      <div class="admin-chip" :class="{ active: sportFilter === 'all' }" @click="sportFilter = 'all'">All <span class="admin-chip-count mono">{{ allLeagues.length }}</span></div>
      <div v-for="s in sports" :key="s.id" class="admin-chip" :class="{ active: sportFilter === s.id }" @click="sportFilter = s.id">
        {{ s.label }} <span class="admin-chip-count mono">{{ s.leagues.length }}</span>
      </div>
    </div>

    <div v-if="catalogLoading" class="admin-card"><div class="admin-empty">Loading leagues…</div></div>
    <div v-else-if="catalogError" class="admin-card"><div class="admin-empty err">Failed to load league catalog: {{ catalogError }}</div></div>
    <template v-else>
      <div v-if="featured.length" class="admin-league-grid">
        <div v-for="l in featured" :key="l.slug" class="admin-lc" @click="openLeague(l.name)">
          <div class="admin-lc-head">
            <div class="admin-lc-title">
              <div class="admin-lc-name">{{ l.name }}</div>
              <div class="admin-lc-tags">
                <span class="admin-tag brand">{{ l.sportLabel }}</span>
              </div>
            </div>
          </div>
          <div class="admin-lc-stats">
            <div class="admin-lc-stat"><div class="admin-lc-stat-val mono">{{ l.teamCount }}</div><div class="admin-lc-stat-lab">Teams</div></div>
            <div class="admin-lc-stat"><div class="admin-lc-stat-val mono">{{ l.subscribers }}</div><div class="admin-lc-stat-lab">Subs</div></div>
            <div class="admin-lc-stat"><div class="admin-lc-stat-val mono">{{ fmtNum(l.total_syncs) }}</div><div class="admin-lc-stat-lab">Syncs</div></div>
          </div>
        </div>
      </div>

      <section v-if="rest.length" class="admin-card">
        <div class="admin-card-head">
          <div class="admin-card-title">All leagues <span class="admin-hint">{{ filtered.length }} total</span></div>
        </div>
        <table class="admin-tbl">
          <thead><tr><th></th><th>League</th><th>Sport</th><th class="r">Teams</th><th class="r">Subscribers</th><th class="r">Total syncs</th></tr></thead>
          <tbody>
            <tr v-for="(l, i) in rest" :key="l.slug" class="row-link" @click="openLeague(l.name)">
              <td class="rank">{{ String(i + featured.length + 1).padStart(2, '0') }}</td>
              <td><div class="admin-team-name">{{ l.name }}</div></td>
              <td><span class="admin-tag">{{ l.sportLabel }}</span></td>
              <td class="num">{{ l.teamCount }}</td>
              <td class="num">{{ l.subscribers }}<span class="admin-sparkbar" :style="{ width: sparkWidth(l.subscribers) }"></span></td>
              <td class="num">{{ fmtNum(l.total_syncs) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <div v-if="!filtered.length" class="admin-card"><div class="admin-empty">No leagues match your filter.</div></div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { SubscriptionDashboard, Sport, Team } from '@/types'
import { fetchSports, fetchTeams } from '@/services/sports'
import { leagueBreakdown, fmtNum } from '@/utils/adminAggregate'

const props = defineProps<{
  data: SubscriptionDashboard
  loading: boolean
  error: string | null
}>()

const router = useRouter()

const sports = ref<Sport[]>([])
const teams = ref<Team[]>([])
const catalogLoading = ref(true)
const catalogError = ref<string | null>(null)

const search = ref('')
const sportFilter = ref('all')

onMounted(async () => {
  try {
    const [s, t] = await Promise.all([fetchSports(), fetchTeams({ limit: 200 })])
    sports.value = s
    teams.value = t
  } catch (e) {
    catalogError.value = e instanceof Error ? e.message : 'Failed to load'
  } finally {
    catalogLoading.value = false
  }
})

const sportCount = computed(() => sports.value.length)

interface LeagueCard {
  slug: string
  name: string
  sportLabel: string
  teamCount: number
  subscribers: number
  total_syncs: number
}

const subscriberStats = computed(() => leagueBreakdown(props.data.subscriptions))
const totalSubs = computed(() => subscriberStats.value.reduce((a, l) => a + l.subscribers, 0))

const allLeagues = computed<LeagueCard[]>(() => {
  const out: LeagueCard[] = []
  for (const sport of sports.value) {
    for (const league of sport.leagues) {
      const teamCount = teams.value.filter((t) => t.leagues.some((l) => l.slug === league.slug)).length
      const stat = subscriberStats.value.find((s) => s.league === league.name)
      out.push({
        slug: league.slug,
        name: league.name,
        sportLabel: sport.label,
        teamCount,
        subscribers: stat?.subscribers ?? 0,
        total_syncs: stat?.total_syncs ?? 0,
      })
    }
  }
  return out
})

const subscribedLeagues = computed(() => allLeagues.value.filter((l) => l.subscribers > 0))
const topLeague = computed(() => [...subscriberStats.value].sort((a, b) => b.subscribers - a.subscribers)[0] ?? null)

const filtered = computed(() =>
  allLeagues.value
    .filter((l) => {
      if (sportFilter.value !== 'all') {
        const sport = sports.value.find((s) => s.id === sportFilter.value)
        if (!sport?.leagues.some((sl) => sl.slug === l.slug)) return false
      }
      if (search.value && !l.name.toLowerCase().includes(search.value.toLowerCase())) return false
      return true
    })
    .sort((a, b) => b.subscribers - a.subscribers),
)

const featured = computed(() => filtered.value.slice(0, 6))
const rest = computed(() => filtered.value.slice(6))
const maxSubs = computed(() => Math.max(1, ...rest.value.map((l) => l.subscribers)))

function sparkWidth(v: number) {
  return `${(v / maxSubs.value) * 60}px`
}
function openLeague(name: string) {
  router.push({ path: '/admin/teams', query: { league: name } })
}
</script>
