import type { CalendarLink, Match, SeasonStats, Sport, Team } from '@/types'

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

export async function fetchSeasonStats(leagueSlug: string): Promise<SeasonStats> {
  const res = await fetch(`${API_BASE}/leagues/${encodeURIComponent(leagueSlug)}/season-stats`)
  if (!res.ok) throw new Error(`Failed to fetch season stats: ${res.status}`)
  return res.json()
}

export async function fetchFeaturedMatch(): Promise<Match | null> {
  const res = await fetch(`${API_BASE}/matches/featured`)
  if (!res.ok) throw new Error(`Failed to fetch featured match: ${res.status}`)
  return res.json()
}

export async function fetchLastUpdated(): Promise<string | null> {
  const res = await fetch(`${API_BASE}/last-updated`)
  if (!res.ok) throw new Error(`Failed to fetch last-updated: ${res.status}`)
  const data = await res.json()
  return data.last_run
}

export async function fetchCalendarLink(
  sport: string,
  teamSlug: string,
  leagueSlugs: string[],
): Promise<CalendarLink> {
  const params = new URLSearchParams({
    sport,
    team: teamSlug,
    leagues: leagueSlugs.join(','),
  })
  const res = await fetch(`${API_BASE}/calendar?${params}`)
  if (!res.ok) throw new Error(`Failed to fetch calendar link: ${res.status}`)
  return res.json()
}
