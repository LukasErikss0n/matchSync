<template>
  <div>
    <div class="admin-topbar">
      <div>
        <div class="admin-crumbs">
          <b>Admin</b><span class="sep">/</span>
          <template v-if="route.query.league"><b>Teams</b><span class="sep">/</span>{{ route.query.league }}</template>
          <template v-else>Teams</template>
        </div>
        <h1>Teams</h1>
      </div>
      <div class="admin-topbar-right">
        <RouterLink class="admin-btn admin-btn-ghost" to="/admin/leagues">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/></svg>
          Browse leagues
        </RouterLink>
      </div>
    </div>

    <section class="admin-stats">
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Teams tracked</div>
        <div class="admin-stat-value mono">{{ fmtNum(allTeams.length) }}</div>
        <div class="admin-stat-meta"><span>with at least 1 subscriber</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Total subscribers</div>
        <div class="admin-stat-value mono">{{ fmtNum(data.subscriptions.length) }}</div>
        <div class="admin-stat-meta"><span>across all teams</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Active now</div>
        <div class="admin-stat-value mono">{{ fmtNum(activeNow) }}</div>
        <div class="admin-stat-meta"><span>polled in last 5min</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Stale (&gt;24h)</div>
        <div class="admin-stat-value mono">{{ fmtNum(staleCount) }}</div>
        <div class="admin-stat-meta"><span>review feed source</span></div>
      </div>
    </section>

    <div class="admin-filter-bar">
      <div class="admin-search-input">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
        <input v-model="search" placeholder="Search teams by name…" />
      </div>
      <div class="admin-chip" :class="{ active: sportFilter === 'all' }" @click="sportFilter = 'all'">
        All sports <span class="admin-chip-count mono">{{ sportCounts.all }}</span>
      </div>
      <div v-for="s in sportSlugs" :key="s" class="admin-chip" :class="{ active: sportFilter === s }" @click="sportFilter = s">
        {{ s }} <span class="admin-chip-count mono">{{ sportCounts[s] || 0 }}</span>
      </div>
      <div class="admin-divider"></div>
      <div v-for="s in (['all', 'active', 'idle', 'stale'] as const)" :key="s" class="admin-chip" :class="{ active: statusFilter === s }" @click="statusFilter = s">
        {{ s[0].toUpperCase() + s.slice(1) }}
      </div>
      <div v-if="route.query.league" class="admin-chip active" @click="clearLeague">
        {{ route.query.league }}
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" style="width: 11px; height: 11px;"><path d="M6 6l12 12"/><path d="M18 6L6 18"/></svg>
      </div>
    </div>

    <section class="admin-card">
      <div class="admin-card-head">
        <div class="admin-card-title">
          {{ filtered.length === allTeams.length ? 'All teams' : 'Filtered teams' }}
          <span class="admin-hint">{{ filtered.length }} of {{ allTeams.length }}</span>
        </div>
      </div>
      <table v-if="slice.length" class="admin-tbl">
        <thead>
          <tr><th></th><th>Team</th><th class="r">Subs</th><th class="r">Syncs</th><th class="r">Last sync</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="t in slice" :key="t.sport + t.team" class="row-link" @click="openTeamKey = t.sport + '|' + t.team">
            <td><div class="admin-team-avatar">{{ initials(t.team) }}</div></td>
            <td>
              <div class="admin-team-meta">
                <div class="admin-team-name">{{ t.team }}</div>
                <div class="admin-team-sub">{{ t.sport }}</div>
              </div>
            </td>
            <td class="num">{{ t.subscribers }}<span class="admin-sparkbar" :style="{ width: sparkWidth(t.subscribers) }"></span></td>
            <td class="num">{{ fmtNum(t.total_syncs) }}</td>
            <td class="num">{{ fmtAgo(secondsSince(t.last_seen)) }}</td>
            <td><span class="admin-tag" :class="statusOf(secondsSince(t.last_seen)).tag">{{ statusOf(secondsSince(t.last_seen)).label }}</span></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="admin-empty">No teams match your filter.</div>

      <div v-if="slice.length" class="admin-pagination">
        <div>Showing <span class="mono">{{ (page - 1) * pageSize + 1 }}</span>–<span class="mono">{{ (page - 1) * pageSize + slice.length }}</span> of <span class="mono">{{ filtered.length }}</span></div>
        <div class="pg-pages">
          <button class="admin-pg-btn" :disabled="page === 1" @click="page = Math.max(1, page - 1)">‹</button>
          <button v-for="i in totalPages" :key="i" class="admin-pg-btn" :class="{ active: i === page }" @click="page = i">{{ i }}</button>
          <button class="admin-pg-btn" :disabled="page === totalPages" @click="page = Math.min(totalPages, page + 1)">›</button>
        </div>
      </div>
    </section>

    <div class="admin-drawer-backdrop" :class="{ open: !!openTeam }" @click="openTeamKey = null"></div>
    <aside class="admin-drawer" :class="{ open: !!openTeam }">
      <template v-if="openTeam">
        <div class="admin-drawer-head">
          <div class="admin-drawer-title">
            <div class="admin-team-avatar lg">{{ initials(openTeam.team) }}</div>
            <div>
              <h2>{{ openTeam.team }}</h2>
              <div class="admin-team-sub">{{ openTeam.sport }}</div>
            </div>
          </div>
          <button class="admin-drawer-close" @click="openTeamKey = null">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12"/><path d="M18 6L6 18"/></svg>
          </button>
        </div>
        <div class="admin-drawer-body">
          <div class="admin-drawer-grid">
            <div class="admin-dg-stat"><div class="lab">Subscribers</div><div class="val mono">{{ openTeam.subscribers }}</div></div>
            <div class="admin-dg-stat"><div class="lab">Total syncs</div><div class="val mono">{{ fmtNum(openTeam.total_syncs) }}</div></div>
            <div class="admin-dg-stat"><div class="lab">Last sync</div><div class="val mono">{{ fmtAgo(secondsSince(openTeam.last_seen)) }}</div></div>
            <div class="admin-dg-stat">
              <div class="lab">Status</div>
              <div class="val"><span class="admin-tag" :class="statusOf(secondsSince(openTeam.last_seen)).tag" style="font-size: 11.5px; padding: 3px 8px;">{{ statusOf(secondsSince(openTeam.last_seen)).label }}</span></div>
            </div>
          </div>
          <div class="admin-drawer-section-title">Metadata</div>
          <div class="admin-kv-list">
            <div class="admin-kv"><span class="k">Sport</span><span class="v">{{ openTeam.sport }}</span></div>
          </div>
        </div>
      </template>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { SubscriptionDashboard } from '@/types'
import {
  teamBreakdown,
  fmtNum,
  fmtAgo,
  initials,
  secondsSince,
  statusOf,
  type TeamRow,
} from '@/utils/adminAggregate'

const props = defineProps<{
  data: SubscriptionDashboard
  loading: boolean
  error: string | null
}>()

const route = useRoute()
const router = useRouter()

const search = ref('')
const sportFilter = ref('all')
const statusFilter = ref<'all' | 'active' | 'idle' | 'stale'>('all')
const page = ref(1)
const pageSize = 10
const openTeamKey = ref<string | null>(null)

const allTeams = computed<TeamRow[]>(() => teamBreakdown(props.data.subscriptions))
const sportSlugs = computed(() => [...new Set(allTeams.value.map((t) => t.sport))].sort())
const sportCounts = computed(() => {
  const c: Record<string, number> = { all: allTeams.value.length }
  for (const s of sportSlugs.value) c[s] = allTeams.value.filter((t) => t.sport === s).length
  return c
})

const activeNow = computed(() => allTeams.value.filter((t) => (secondsSince(t.last_seen) ?? Infinity) < 300).length)
const staleCount = computed(() => allTeams.value.filter((t) => (secondsSince(t.last_seen) ?? Infinity) >= 86400).length)

const filtered = computed(() => {
  const leagueFilterRaw = route.query.league
  return allTeams.value
    .filter((t) => {
      if (sportFilter.value !== 'all' && t.sport !== sportFilter.value) return false
      if (statusFilter.value !== 'all') {
        const st = statusOf(secondsSince(t.last_seen)).tag
        if (statusFilter.value === 'active' && st !== 'good') return false
        if (statusFilter.value === 'idle' && st !== 'warn') return false
        if (statusFilter.value === 'stale' && st !== 'bad') return false
      }
      if (search.value && !t.team.toLowerCase().includes(search.value.toLowerCase())) return false
      if (leagueFilterRaw) {
        const sub = props.data.subscriptions.find((s) => s.sport === t.sport && s.team === t.team)
        if (!sub || !sub.leagues.includes(String(leagueFilterRaw))) return false
      }
      return true
    })
    .sort((a, b) => b.subscribers - a.subscribers)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const slice = computed(() => filtered.value.slice((page.value - 1) * pageSize, (page.value - 1) * pageSize + pageSize))
const maxSubs = computed(() => Math.max(1, ...filtered.value.map((t) => t.subscribers)))

const openTeam = computed(() => {
  if (!openTeamKey.value) return null
  const [sport, team] = openTeamKey.value.split('|')
  return allTeams.value.find((t) => t.sport === sport && t.team === team) ?? null
})

watch([search, sportFilter, statusFilter, () => route.query.league], () => { page.value = 1 })

function clearLeague() {
  router.replace({ path: '/admin/teams' })
}
function sparkWidth(v: number) {
  return `${(v / maxSubs.value) * 60}px`
}
</script>
