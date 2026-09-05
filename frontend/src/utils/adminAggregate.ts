import type { CalendarSubscription } from '@/types'

export interface TeamRow {
  sport: string
  team: string
  subscribers: number
  total_syncs: number
  last_seen: string | null
}

export interface LeagueRow {
  league: string
  subscribers: number
  total_syncs: number
}

export interface DailyCount {
  day: string
  count: number
}

export type ClientKind = 'apple' | 'google' | 'outlook' | 'other'

export function totalSyncs(subs: CalendarSubscription[]): number {
  return subs.reduce((sum, s) => sum + s.fetch_count, 0)
}

export function teamBreakdown(subs: CalendarSubscription[]): TeamRow[] {
  const map = new Map<string, TeamRow>()
  for (const s of subs) {
    const key = `${s.sport}|${s.team}`
    const row = map.get(key)
    if (row) {
      row.subscribers += 1
      row.total_syncs += s.fetch_count
      if (!row.last_seen || (s.last_seen && s.last_seen > row.last_seen)) {
        row.last_seen = s.last_seen
      }
    } else {
      map.set(key, {
        sport: s.sport,
        team: s.team,
        subscribers: 1,
        total_syncs: s.fetch_count,
        last_seen: s.last_seen,
      })
    }
  }
  return [...map.values()].sort((a, b) => b.subscribers - a.subscribers)
}

export function leagueBreakdown(subs: CalendarSubscription[]): LeagueRow[] {
  const map = new Map<string, LeagueRow>()
  for (const s of subs) {
    for (const league of s.leagues) {
      const row = map.get(league)
      if (row) {
        row.subscribers += 1
        row.total_syncs += s.fetch_count
      } else {
        map.set(league, { league, subscribers: 1, total_syncs: s.fetch_count })
      }
    }
  }
  return [...map.values()].sort((a, b) => b.subscribers - a.subscribers)
}

export function dailySignups(subs: CalendarSubscription[], days = 14): DailyCount[] {
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

export function classifyClient(userAgent: string | null): ClientKind {
  if (!userAgent) return 'other'
  const ua = userAgent.toLowerCase()
  if (ua.includes('calendaragent') || ua.includes('cfnetwork') || ua.includes('ical') || ua.includes('mac os x') || ua.includes('iphone') || ua.includes('ipad')) {
    return 'apple'
  }
  if (ua.includes('google-calendar') || ua.includes('googlecalendar') || ua.includes('gsa/')) {
    return 'google'
  }
  if (ua.includes('outlook') || ua.includes('microsoft office') || ua.includes('ms-office')) {
    return 'outlook'
  }
  return 'other'
}

export function clientMix(subs: CalendarSubscription[]): Record<ClientKind, number> {
  const mix: Record<ClientKind, number> = { apple: 0, google: 0, outlook: 0, other: 0 }
  for (const s of subs) {
    mix[classifyClient(s.last_user_agent)] += 1
  }
  return mix
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

export function fmtAgo(seconds: number | null): string {
  if (seconds === null) return 'never'
  if (seconds < 60) return `${Math.max(0, Math.floor(seconds))}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export function secondsSince(iso: string | null): number | null {
  if (!iso) return null
  return Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
}

export function statusOf(seconds: number | null): { tag: 'good' | 'warn' | 'bad'; label: string } {
  if (seconds === null) return { tag: 'bad', label: 'Never' }
  if (seconds < 300) return { tag: 'good', label: 'Active' }
  if (seconds < 86400) return { tag: 'warn', label: 'Idle' }
  return { tag: 'bad', label: 'Stale' }
}
