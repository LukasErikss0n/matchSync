import type { CalendarLink, Match, SeasonStats, StandingEntry, Sport, SubscriptionDashboard, SupportPayload, Team } from '@/types'

const API_BASE = '/api'

export async function fetchSports(): Promise<Sport[]> {
  const res = await fetch(`${API_BASE}/sports`)
  if (!res.ok) throw new Error(`Failed to fetch sports: ${res.status}`)
  return res.json()
}

export async function fetchTeams(opts: {
  sport?: string
  q?: string
  limit?: number
} = {}): Promise<Team[]> {
  const params = new URLSearchParams()
  if (opts.sport) params.set('sport', opts.sport)
  if (opts.q) params.set('q', opts.q)
  if (opts.limit) params.set('limit', String(opts.limit))
  const qs = params.toString()
  const res = await fetch(`${API_BASE}/teams${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error(`Failed to fetch teams: ${res.status}`)
  return res.json()
}

export async function fetchTeam(teamSlug: string, sport?: string): Promise<Team> {
  const qs = sport ? `?sport=${encodeURIComponent(sport)}` : ''
  const res = await fetch(`${API_BASE}/teams/${encodeURIComponent(teamSlug)}${qs}`)
  if (!res.ok) throw new Error(`Failed to fetch team: ${res.status}`)
  return res.json()
}

export async function fetchMatches(opts: {
  sport?: string
  league?: string
  team?: string
  limit?: number
} = {}): Promise<Match[]> {
  const params = new URLSearchParams()
  if (opts.sport) params.set('sport', opts.sport)
  if (opts.league) params.set('league', opts.league)
  if (opts.team) params.set('team', opts.team)
  if (opts.limit) params.set('limit', String(opts.limit))
  const qs = params.toString()
  const res = await fetch(`${API_BASE}/matches${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error(`Failed to fetch matches: ${res.status}`)
  return res.json()
}

export async function fetchStandings(leagueSlug: string): Promise<StandingEntry[] | null> {
  const res = await fetch(`${API_BASE}/leagues/${encodeURIComponent(leagueSlug)}/standings`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`Failed to fetch standings: ${res.status}`)
  return res.json()
}

export async function fetchSeasonStats(leagueSlug: string): Promise<SeasonStats> {
  const res = await fetch(`${API_BASE}/leagues/${encodeURIComponent(leagueSlug)}/season-stats`)
  if (!res.ok) throw new Error(`Failed to fetch season stats: ${res.status}`)
  return res.json()
}

export async function fetchFeaturedMatch(region?: string): Promise<Match | null> {
  const qs = region ? `?region=${encodeURIComponent(region)}` : ''
  const res = await fetch(`${API_BASE}/matches/featured${qs}`)
  if (!res.ok) throw new Error(`Failed to fetch featured match: ${res.status}`)
  return res.json()
}

export async function fetchFeaturedMatches(region?: string, limit = 3): Promise<Match[]> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (region) params.set('region', region)
  const res = await fetch(`${API_BASE}/matches/featured/list?${params}`)
  if (!res.ok) throw new Error(`Failed to fetch featured matches: ${res.status}`)
  return res.json()
}

export async function fetchWeekMatches(region?: string): Promise<Match[]> {
  const params = new URLSearchParams()
  if (region) params.set('region', region)
  const qs = params.toString()
  const res = await fetch(`${API_BASE}/matches/this-week${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error(`Failed to fetch this week's matches: ${res.status}`)
  return res.json()
}

export async function fetchLastUpdated(): Promise<string | null> {
  const res = await fetch(`${API_BASE}/last-updated`)
  if (!res.ok) throw new Error(`Failed to fetch last-updated: ${res.status}`)
  const data = await res.json()
  return data.last_run
}

export async function sendSupportRequest(payload: SupportPayload): Promise<void> {
  const res = await fetch(`${API_BASE}/support`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Failed to send support request: ${res.status}`)
}

const CAL_LINK_CACHE_PREFIX = 'ms-cal-link:'

function calLinkCacheKey(sport: string, teamSlug: string, leagueSlugs: string[]): string {
  return `${CAL_LINK_CACHE_PREFIX}${sport}|${teamSlug}|${[...leagueSlugs].sort().join(',')}`
}

export async function fetchCalendarLink(
  sport: string,
  teamSlug: string,
  leagueSlugs: string[],
): Promise<CalendarLink> {
  const cacheKey = calLinkCacheKey(sport, teamSlug, leagueSlugs)
  try {
    const cached = sessionStorage.getItem(cacheKey)
    if (cached) return JSON.parse(cached) as CalendarLink
  } catch {
    // Private mode, disabled storage, or a corrupt entry — just re-fetch.
  }

  const params = new URLSearchParams({
    sport,
    team: teamSlug,
    leagues: leagueSlugs.join(','),
  })
  const res = await fetch(`${API_BASE}/calendar?${params}`)
  if (!res.ok) throw new Error(`Failed to fetch calendar link: ${res.status}`)
  const link: CalendarLink = await res.json()

  try {
    sessionStorage.setItem(cacheKey, JSON.stringify(link))
  } catch {
    // Caching is an optimisation; a failure here must not break the flow.
  }
  return link
}

export async function fetchSubscriptionDashboard(
  adminToken: string,
  windowDays?: number,
): Promise<SubscriptionDashboard> {
  const qs = windowDays ? `?window_days=${windowDays}` : ''
  const res = await fetch(`${API_BASE}/admin/subscriptions${qs}`, {
    headers: { 'X-Admin-Token': adminToken },
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.detail ?? `Failed to load dashboard: ${res.status}`)
  }
  return res.json()
}
