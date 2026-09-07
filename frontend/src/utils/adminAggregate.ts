import type { CalendarSubscription } from '@/types'

/**
 * Vocabulary note — the backend creates a CalendarSubscription row every time
 * someone reaches step 4 of the wizard (calendar.py: get_calendar_link), with
 * no dedupe. So a row is a *generated link*, not a subscriber. A link only
 * becomes a real subscription once a calendar app fetches it:
 *
 *   unused  — never fetched (last_seen === null). Link made, never added anywhere.
 *   live    — fetched within the backend's active window (subscription.active).
 *   dropped — was fetched once, but not inside the active window any more.
 *
 * "live" is the only number that maps to a real person still following a team.
 */
export type SubStatus = 'live' | 'dropped' | 'unused'

export function statusOf(sub: CalendarSubscription): SubStatus {
  if (!sub.last_seen) return 'unused'
  return sub.active ? 'live' : 'dropped'
}

export const STATUS_LABEL: Record<SubStatus, string> = {
  live: 'Live',
  dropped: 'Dropped off',
  unused: 'Unused',
}

export interface Totals {
  live: number
  dropped: number
  unused: number
  generated: number
  activated: number
  activationRate: number
  teamsFollowed: number
  lastPoll: string | null
}

export function totals(subs: CalendarSubscription[]): Totals {
  let live = 0
  let dropped = 0
  let unused = 0
  let lastPoll: string | null = null
  const liveTeams = new Set<string>()

  for (const s of subs) {
    const status = statusOf(s)
    if (status === 'live') {
      live += 1
      liveTeams.add(`${s.sport}|${s.team}`)
    } else if (status === 'dropped') dropped += 1
    else unused += 1

    if (s.last_seen && (!lastPoll || s.last_seen > lastPoll)) lastPoll = s.last_seen
  }

  const activated = live + dropped
  return {
    live,
    dropped,
    unused,
    generated: subs.length,
    activated,
    activationRate: subs.length ? Math.round((activated / subs.length) * 100) : 0,
    teamsFollowed: liveTeams.size,
    lastPoll,
  }
}

export interface TeamRow {
  sport: string
  team: string
  live: number
  generated: number
  polls: number
  lastSeen: string | null
}

export function teamBreakdown(subs: CalendarSubscription[]): TeamRow[] {
  const map = new Map<string, TeamRow>()
  for (const s of subs) {
    const key = `${s.sport}|${s.team}`
    let row = map.get(key)
    if (!row) {
      row = { sport: s.sport, team: s.team, live: 0, generated: 0, polls: 0, lastSeen: null }
      map.set(key, row)
    }
    row.generated += 1
    row.polls += s.fetch_count
    if (statusOf(s) === 'live') row.live += 1
    if (s.last_seen && (!row.lastSeen || s.last_seen > row.lastSeen)) row.lastSeen = s.last_seen
  }
  // Live followers first, then whoever is polling hardest.
  return [...map.values()].sort((a, b) => b.live - a.live || b.polls - a.polls)
}

export interface LeagueRow {
  slug: string
  live: number
  generated: number
}

/** Keyed by league *slug* — that is what the backend stores in the leagues column. */
export function leagueBreakdown(subs: CalendarSubscription[]): LeagueRow[] {
  const map = new Map<string, LeagueRow>()
  for (const s of subs) {
    const isLive = statusOf(s) === 'live'
    for (const slug of s.leagues) {
      let row = map.get(slug)
      if (!row) {
        row = { slug, live: 0, generated: 0 }
        map.set(slug, row)
      }
      row.generated += 1
      if (isLive) row.live += 1
    }
  }
  return [...map.values()].sort((a, b) => b.live - a.live || b.generated - a.generated)
}

export interface ClientRow {
  label: string
  count: number
}

/**
 * The backend already normalises the User-Agent into a friendly label
 * (calendar.py: _client_label) — "Apple Calendar", "Google Calendar",
 * "Outlook", "Thunderbird", "Web browser", "Other". Use it as-is; re-parsing
 * that label as if it were a raw UA string is what made everything "Other".
 * Rows that were never fetched have no client and are excluded.
 */
export function clientBreakdown(subs: CalendarSubscription[]): ClientRow[] {
  const map = new Map<string, number>()
  for (const s of subs) {
    if (!s.last_user_agent) continue
    map.set(s.last_user_agent, (map.get(s.last_user_agent) ?? 0) + 1)
  }
  return [...map.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count)
}

export interface DailyCount {
  day: string
  count: number
}

export function dailyCreated(subs: CalendarSubscription[], days = 14): DailyCount[] {
  const counts = new Map<string, number>()
  for (const s of subs) {
    const day = s.created_at.slice(0, 10)
    counts.set(day, (counts.get(day) ?? 0) + 1)
  }
  const out: DailyCount[] = []
  const today = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    out.push({ day: key, count: counts.get(key) ?? 0 })
  }
  return out
}

export function fmtNum(n: number): string {
  return n.toLocaleString('en-US')
}

export function initials(name: string): string {
  return name
    .replace(/-/g, ' ')
    .split(/\s+/)
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export function fmtAgo(iso: string | null): string {
  if (!iso) return 'never'
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 90) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
