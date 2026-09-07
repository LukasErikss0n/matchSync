<template>
  <div>
    <!-- Headline: only the numbers that describe real people -->
    <section class="admin-stats admin-stats-3">
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Live subscribers</div>
        <div class="admin-stat-value">{{ t.live }}</div>
        <div class="admin-stat-meta"><span>calendars polling within {{ data.active_window_days }} days</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Teams followed</div>
        <div class="admin-stat-value">{{ t.teamsFollowed }}</div>
        <div class="admin-stat-meta"><span>with at least one live subscriber</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Last poll</div>
        <div class="admin-stat-value">{{ fmtAgo(t.lastPoll) }}</div>
        <div class="admin-stat-meta"><span>most recent calendar fetch</span></div>
      </div>
    </section>

    <!-- The funnel, stated plainly so the numbers can't mislead -->
    <div class="admin-funnel">
      <span><b>{{ t.generated }}</b> links generated</span>
      <span class="sep">·</span>
      <span><b>{{ t.activated }}</b> added to a calendar ({{ t.activationRate }}%)</span>
      <span class="sep">·</span>
      <span><b>{{ t.unused }}</b> never used</span>
      <span v-if="t.dropped" class="sep">·</span>
      <span v-if="t.dropped"><b>{{ t.dropped }}</b> dropped off</span>
      <span class="admin-funnel-note">a link is created when someone reaches the last wizard step, so this counts generations, not people</span>
    </div>

    <section class="admin-card admin-gap-md">
      <div class="admin-card-head">
        <div class="admin-card-title">Teams <span class="admin-hint">by live subscribers</span></div>
      </div>
      <table v-if="teams.length" class="admin-tbl">
        <thead>
          <tr><th>Team</th><th class="r">Live</th><th class="r">Polls</th><th class="r">Last poll</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in teams" :key="row.sport + row.team">
            <td>
              <div class="admin-team-cell">
                <div class="admin-team-avatar">{{ initials(row.team) }}</div>
                <div class="admin-team-meta">
                  <div class="admin-team-name">{{ row.team }}</div>
                  <div class="admin-team-sub">{{ row.sport }}</div>
                </div>
              </div>
            </td>
            <td class="num">
              <span :class="{ 'admin-zero': !row.live }">{{ row.live }}</span>
              <span v-if="row.generated > row.live" class="admin-of">of {{ row.generated }}</span>
            </td>
            <td class="num"><span :class="{ 'admin-zero': !row.polls }">{{ fmtNum(row.polls) }}</span></td>
            <td class="num"><span :class="{ 'admin-zero': !row.lastSeen }">{{ fmtAgo(row.lastSeen) }}</span></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="admin-empty">No links generated yet.</div>
    </section>

    <!-- Two short breakdown lists paired with each other: similar shape, so
         they stay level without stranding whitespace inside either card. -->
    <section class="admin-grid-2">
      <div class="admin-card">
        <div class="admin-card-head">
          <div class="admin-card-title">Leagues <span class="admin-hint">live subscribers</span></div>
        </div>
        <div class="admin-pills-list">
          <div v-for="l in leagues" :key="l.slug" class="admin-pill-row">
            <div class="admin-pill-bar-wrap">
              <div class="admin-pill-name" :title="leagueName(l.slug)">{{ leagueName(l.slug) }}</div>
              <div class="admin-pill-bar">
                <div class="admin-pill-bar-fill" :style="{ width: pct(l.live, maxLeagueLive) }"></div>
              </div>
            </div>
            <div class="admin-pill-count">
              <span :class="{ 'admin-zero': !l.live }">{{ l.live }}</span>
            </div>
          </div>
          <div v-if="!leagues.length" class="admin-empty">No league data yet.</div>
        </div>
      </div>

      <div class="admin-card">
        <div class="admin-card-head">
          <div class="admin-card-title">Calendar apps <span class="admin-hint">of {{ t.activated }} activated</span></div>
        </div>
        <div class="admin-pills-list">
          <div v-for="c in clients" :key="c.label" class="admin-pill-row">
            <div class="admin-pill-bar-wrap">
              <div class="admin-pill-name">{{ c.label }}</div>
              <div class="admin-pill-bar">
                <div class="admin-pill-bar-fill" :style="{ width: pct(c.count, maxClient) }"></div>
              </div>
            </div>
            <div class="admin-pill-count">{{ c.count }}</div>
          </div>
          <div v-if="!clients.length" class="admin-empty">No calendar app has fetched a link yet.</div>
        </div>
      </div>
    </section>

    <section class="admin-card admin-gap-md">
      <div class="admin-card-head">
        <div class="admin-card-title">Links created <span class="admin-hint">last 14 days</span></div>
        <div class="admin-card-actions">
          <span class="admin-hint">{{ createdTotal }} total</span>
        </div>
      </div>
      <div class="admin-chart">
        <div class="admin-chart-y">
          <span v-for="tick in scale.ticks" :key="tick" class="admin-chart-tick" :style="{ bottom: offset(tick) }">
            {{ tick }}
          </span>
        </div>
        <div class="admin-chart-plot">
          <div
            v-for="tick in scale.ticks"
            :key="tick"
            class="admin-chart-line"
            :class="{ base: tick === 0 }"
            :style="{ bottom: offset(tick) }"
          ></div>
          <div class="admin-chart-bars">
            <div
              v-for="d in daily"
              :key="d.day"
              class="admin-bar-col"
              :title="`${d.count} link${d.count === 1 ? '' : 's'} on ${d.day}`"
            >
              <div class="bar" :style="{ height: offset(d.count) }"></div>
            </div>
          </div>
        </div>
        <div class="admin-chart-x">
          <div v-for="d in daily" :key="d.day" class="admin-chart-xlabel">{{ fmtDate(d.day) }}</div>
        </div>
      </div>
    </section>

    <section class="admin-card">
      <div class="admin-card-head">
        <div class="admin-card-title">All links <span class="admin-hint">{{ filtered.length }} of {{ data.subscriptions.length }}</span></div>
        <div class="admin-card-actions">
          <div class="admin-search-input">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
            <input v-model="search" placeholder="Search team or league…" />
          </div>
          <div class="admin-chip" :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">All</div>
          <div v-for="s in (['live', 'dropped', 'unused'] as const)" :key="s" class="admin-chip" :class="{ active: statusFilter === s }" @click="statusFilter = s">
            {{ STATUS_LABEL[s] }}
          </div>
        </div>
      </div>
      <table v-if="filtered.length" class="admin-tbl">
        <thead>
          <tr><th>Team</th><th>Leagues</th><th class="r">Polls</th><th class="r">Created</th><th class="r">Last poll</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="s in filtered" :key="s.token">
            <td>
              <div class="admin-team-meta">
                <div class="admin-team-name">{{ s.team }}</div>
                <div class="admin-team-sub">{{ s.sport }}</div>
              </div>
            </td>
            <td>
              <div class="admin-league-tags">
                <span v-for="slug in s.leagues" :key="slug" class="admin-tag brand">{{ leagueName(slug) }}</span>
              </div>
            </td>
            <td class="num"><span :class="{ 'admin-zero': !s.fetch_count }">{{ s.fetch_count }}</span></td>
            <td class="num">{{ fmtDate(s.created_at) }}</td>
            <td class="num"><span :class="{ 'admin-zero': !s.last_seen }">{{ fmtAgo(s.last_seen) }}</span></td>
            <td>
              <span class="admin-tag" :class="statusTag(s)">{{ STATUS_LABEL[statusOf(s)] }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="admin-empty">No links match your filter.</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { CalendarSubscription, SubscriptionDashboard } from '@/types'
import { fetchSports } from '@/services/sports'
import {
  totals,
  teamBreakdown,
  leagueBreakdown,
  clientBreakdown,
  dailyCreated,
  statusOf,
  STATUS_LABEL,
  fmtNum,
  fmtAgo,
  fmtDate,
  initials,
  type SubStatus,
} from '@/utils/adminAggregate'

const props = defineProps<{
  data: SubscriptionDashboard
  loading: boolean
  error: string | null
}>()

const search = ref('')
const statusFilter = ref<'all' | SubStatus>('all')

/* The subscription rows store league *slugs*; the catalog gives us display
   names. Falls back to the slug if the catalog is unavailable. */
const leagueNames = ref<Record<string, string>>({})
onMounted(async () => {
  try {
    const sports = await fetchSports()
    const map: Record<string, string> = {}
    for (const sport of sports) {
      for (const league of sport.leagues) map[league.slug] = league.name
    }
    leagueNames.value = map
  } catch {
    // Names are a nicety — slugs remain readable if the catalog call fails.
  }
})
function leagueName(slug: string) {
  return leagueNames.value[slug] ?? slug
}

const t = computed(() => totals(props.data.subscriptions))
const teams = computed(() => teamBreakdown(props.data.subscriptions))
const leagues = computed(() => leagueBreakdown(props.data.subscriptions))
const clients = computed(() => clientBreakdown(props.data.subscriptions))
const daily = computed(() => dailyCreated(props.data.subscriptions, 14))

const maxLeagueLive = computed(() => Math.max(1, ...leagues.value.map((l) => l.live)))
const maxClient = computed(() => Math.max(1, ...clients.value.map((c) => c.count)))
const createdTotal = computed(() => daily.value.reduce((a, d) => a + d.count, 0))

/* Round the y-axis up to whole-number ticks so the gridlines land on values
   you can actually read — these are counts, so fractional ticks are nonsense. */
const scale = computed(() => {
  const peak = Math.max(...daily.value.map((d) => d.count), 0)
  if (peak <= 0) return { max: 1, ticks: [0, 1] }

  const rawStep = peak / 4
  const magnitude = 10 ** Math.floor(Math.log10(rawStep))
  const normalised = rawStep / magnitude
  const step = Math.max(1, Math.round((normalised <= 1 ? 1 : normalised <= 2 ? 2 : normalised <= 5 ? 5 : 10) * magnitude))
  const max = Math.ceil(peak / step) * step

  const ticks: number[] = []
  for (let v = 0; v <= max; v += step) ticks.push(v)
  return { max, ticks }
})

/** Height/position as a share of the y-axis, shared by bars and gridlines. */
function offset(value: number) {
  return `${(value / scale.value.max) * 100}%`
}

const filtered = computed(() =>
  props.data.subscriptions
    .filter((s) => {
      if (statusFilter.value !== 'all' && statusOf(s) !== statusFilter.value) return false
      if (search.value) {
        const q = search.value.toLowerCase()
        const haystack = `${s.team} ${s.sport} ${s.leagues.map(leagueName).join(' ')} ${s.leagues.join(' ')}`
        if (!haystack.toLowerCase().includes(q)) return false
      }
      return true
    })
    .slice()
    .sort((a, b) => (b.last_seen ?? '').localeCompare(a.last_seen ?? '') || b.created_at.localeCompare(a.created_at)),
)

function statusTag(s: CalendarSubscription) {
  const status = statusOf(s)
  return status === 'live' ? 'good' : status === 'dropped' ? 'warn' : ''
}
function pct(v: number, max: number) {
  return `${(v / max) * 100}%`
}
</script>
