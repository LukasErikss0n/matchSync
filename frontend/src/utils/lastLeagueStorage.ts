const LAST_LEAGUE_KEY = 'ms:last-league'

export interface LastLeague {
  sport: string
  slug: string
}

export function saveLastLeague(league: LastLeague): void {
  localStorage.setItem(LAST_LEAGUE_KEY, JSON.stringify({ sport: league.sport, slug: league.slug }))
}

export function readLastLeague(): LastLeague | null {
  try {
    const raw = localStorage.getItem(LAST_LEAGUE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}
