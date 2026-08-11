export type IconName =
  | 'football'
  | 'hockey'
  | 'basketball'
  | 'baseball'
  | 'amfootball'
  | 'rugby'
  | 'car'
  | 'refresh'
  | 'trophy'
  | 'devices'
  | 'globe'
  | 'bell'
  | 'zap'
  | 'link'
  | 'calendar'
  | 'search'

export interface League {
  name: string
  slug: string
  supports_standings?: boolean
}

export interface Sport {
  id: string          // sport slug, e.g. "football"
  label: string       // display name, e.g. "Football"
  icon: IconName
  leagues: League[]
}

export interface Team {
  name: string
  slug: string
  sport: string       // sport slug
  icon?: string | null
  leagues: League[]
}

export interface Match {
  id: number
  external_id: string
  sport: string
  league: League
  home_team: string
  away_team: string
  home_slug?: string | null
  away_slug?: string | null
  home_icon?: string | null
  away_icon?: string | null
  home_score?: number | null
  away_score?: number | null
  start_time: string   // ISO-UTC (with Z) — rendered in the viewer's local time
}

export interface SeasonStats {
  published: boolean
  season_start: string | null   // ISO-UTC
  regular_season_count: number
  progressive_knockout: boolean // true for cups like FA Cup/EFL Cup — later rounds aren't drawn yet
}

export interface StandingEntry {
  position: number
  team: string
  team_slug?: string | null
  team_icon?: string | null
  played: number
  won: number
  drawn: number
  lost: number
  goal_difference: number
  points: number
  form: string[]   // oldest → newest, each "W" | "D" | "L"
}

export interface CalendarLink {
  team: string
  sport: string
  leagues: League[]
  url: string
}
