<template>
  <div>
    <div class="admin-topbar">
      <div>
        <div class="admin-crumbs"><b>Admin</b><span class="sep">/</span>Analytics</div>
        <h1>Webcal analytics</h1>
      </div>
      <div class="admin-topbar-right">
        <button class="admin-btn admin-btn-ghost" :disabled="loading" @click="$emit('refresh')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-3-6.7"/><path d="M21 4v6h-6"/></svg>
          {{ loading ? 'Loading…' : 'Refresh' }}
        </button>
      </div>
    </div>

    <section class="admin-stats">
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Total subscriptions</div>
        <div class="admin-stat-value mono">{{ fmtNum(data.subscriptions.length) }}</div>
        <div class="admin-stat-meta"><span>issued webcal links</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Total syncs</div>
        <div class="admin-stat-value mono">{{ fmtNum(syncsTotal) }}</div>
        <div class="admin-stat-meta"><span>calendar app fetches, all-time</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Active last {{ data.active_window_days }}d</div>
        <div class="admin-stat-value mono">{{ fmtNum(data.active_count) }}</div>
        <div class="admin-stat-meta"><span>polled &ge; 1&times;</span></div>
      </div>
      <div class="admin-stat">
        <div class="admin-stat-label"><span class="dot"></span>Gone quiet</div>
        <div class="admin-stat-value mono">{{ fmtNum(data.dormant_count) }}</div>
        <div class="admin-stat-meta"><span>{{ data.pending_count }} never fetched</span></div>
      </div>
    </section>

    <section class="admin-grid">
      <div class="admin-card">
        <div class="admin-card-head">
          <div class="admin-card-title">New subscriptions <span class="admin-hint">14d window</span></div>
        </div>
        <div class="admin-chart-summary">
          <div><div class="label">avg / day</div><div class="big mono">{{ chartSummary.avg }}</div></div>
          <div><div class="label">peak</div><div class="big mono">{{ chartSummary.peak }}</div></div>
          <div><div class="label">total</div><div class="big mono">{{ chartSummary.total }}</div></div>
        </div>
        <div class="admin-bars">
          <div v-for="d in daily" :key="d.day" class="admin-bar-col">
            <div class="bar" :style="{ height: barHeight(d.count) }" :title="`${d.count} on ${d.day}`"></div>
            <div class="bar-label">{{ formatDay(d.day) }}</div>
          </div>
        </div>
      </div>

      <div class="admin-card">
        <div class="admin-card-head">
          <div class="admin-card-title">League breakdown <span class="admin-hint">by subscribers</span></div>
          <div class="admin-card-actions">
            <RouterLink class="admin-btn admin-btn-ghost admin-btn-sm" to="/admin/leagues">View all</RouterLink>
          </div>
        </div>
        <div class="admin-pills-list">
          <div v-for="l in leagues.slice(0, 6)" :key="l.league" class="admin-pill-row">
            <div class="admin-pill-bar-wrap">
              <div class="admin-pill-name">{{ l.league }}</div>
              <div class="admin-pill-bar">
                <div class="admin-pill-bar-fill" :style="{ width: pct(l.subscribers, maxLeague) }"></div>
              </div>
            </div>
            <div class="admin-pill-count mono">{{ l.subscribers }}</div>
          </div>
          <div v-if="!leagues.length" class="admin-empty">No league data yet.</div>
        </div>
      </div>
    </section>

    <section class="admin-card admin-gap-md">
      <div class="admin-card-head">
        <div class="admin-card-title">Calendar clients <span class="admin-hint">by user-agent</span></div>
      </div>
      <div class="admin-mix-grid" style="padding: 8px 20px 20px;">
        <div v-for="(count, key) in mix" :key="key">
          <div class="admin-mix-head">
            <span>{{ CLIENT_LABEL[key] }}</span>
            <span class="mono admin-mix-pct">{{ mixPct(count) }}%</span>
          </div>
          <div class="admin-mix-bar"><div class="admin-mix-bar-fill" :class="key" :style="{ width: mixPct(count) + '%' }"></div></div>
        </div>
      </div>
    </section>

    <section class="admin-card admin-gap-md">
      <div class="admin-card-head">
        <div class="admin-card-title">Top teams <span class="admin-hint">ranked by subscribers</span></div>
        <div class="admin-card-actions">
          <RouterLink class="admin-btn admin-btn-ghost admin-btn-sm" to="/admin/teams">View all</RouterLink>
        </div>
      </div>
      <table class="admin-tbl">
        <thead>
          <tr><th></th><th>Team</th><th class="r">Subscribers</th><th class="r">Total syncs</th></tr>
        </thead>
        <tbody>
          <tr v-for="(t, i) in teams.slice(0, 12)" :key="t.sport + t.team" :class="{ 'top-row': i === 0 }">
            <td class="rank">{{ String(i + 1).padStart(2, '0') }}</td>
            <td>
              <div class="admin-team-cell">
                <div class="admin-team-avatar">{{ initials(t.team) }}</div>
                <div class="admin-team-meta">
                  <div class="admin-team-name">{{ t.team }}</div>
                  <div class="admin-team-sub">{{ t.sport }}</div>
                </div>
              </div>
            </td>
            <td class="num">{{ t.subscribers }}</td>
            <td class="num">
              {{ fmtNum(t.total_syncs) }}
              <span class="admin-sparkbar" :style="{ width: sparkWidth(t.total_syncs) }"></span>
            </td>
          </tr>
          <tr v-if="!teams.length"><td colspan="4" class="admin-empty">No team data yet.</td></tr>
        </tbody>
      </table>
    </section>

    <div class="admin-footer-note">
      <span><b>endpoint</b> GET /admin/subscriptions</span>
      <span v-if="error" class="err"><b>error</b> {{ error }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SubscriptionDashboard } from '@/types'
import {
  totalSyncs,
  teamBreakdown,
  leagueBreakdown,
  dailySignups,
  clientMix,
  fmtNum,
  initials,
  type ClientKind,
} from '@/utils/adminAggregate'

const props = defineProps<{
  data: SubscriptionDashboard
  loading: boolean
  error: string | null
}>()

defineEmits<{ refresh: [] }>()

const CLIENT_LABEL: Record<ClientKind, string> = {
  apple: 'Apple Calendar',
  google: 'Google Calendar',
  outlook: 'Outlook',
  other: 'Other / ICS',
}

const syncsTotal = computed(() => totalSyncs(props.data.subscriptions))
const teams = computed(() => teamBreakdown(props.data.subscriptions))
const leagues = computed(() => leagueBreakdown(props.data.subscriptions))
const daily = computed(() => dailySignups(props.data.subscriptions, 14))
const mix = computed(() => clientMix(props.data.subscriptions))

const maxLeague = computed(() => Math.max(1, ...leagues.value.map((l) => l.subscribers)))
const maxTeamSyncs = computed(() => Math.max(1, ...teams.value.map((t) => t.total_syncs)))
const maxDaily = computed(() => Math.max(1, ...daily.value.map((d) => d.count)))

const chartSummary = computed(() => {
  const vals = daily.value.map((d) => d.count)
  const total = vals.reduce((a, b) => a + b, 0)
  return {
    avg: vals.length ? +(total / vals.length).toFixed(1) : 0,
    peak: vals.length ? Math.max(...vals) : 0,
    total,
  }
})

function pct(v: number, max: number) {
  return `${(v / max) * 100}%`
}
function sparkWidth(v: number) {
  return `${(v / maxTeamSyncs.value) * 60}px`
}
function barHeight(v: number) {
  return `${Math.max(2, (v / maxDaily.value) * 100)}%`
}
function formatDay(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
function mixPct(count: number) {
  const total = Object.values(mix.value).reduce((a, b) => a + b, 0) || 1
  return Math.round((count / total) * 100)
}
</script>
