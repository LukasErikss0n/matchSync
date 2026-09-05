export type IconName =
  | 'football'
  | 'hockey'
  | 'basketball'
  | 'baseball'
  | 'amfootball'
  | 'rugby'
  | 'car'
  | 'flag'
  | 'refresh'
  | 'trophy'
  | 'devices'
  | 'globe'
  | 'bell'
  | 'zap'
  | 'link'
  | 'calendar'
  | 'search'
  | 'clock'

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
  home_icon_cropped?: string | null
  away_icon_cropped?: string | null
  home_score?: number | null
  away_score?: number | null
  start_time: string
  venue?: string | null
  status?: MatchStatus | null
}

export type MatchStatus = 'scheduled' | 'live' | 'finished'

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

export type SupportType = 'bug' | 'improvement' | 'other'

export interface SupportPayload {
  type: SupportType
  text: string
  page?: string | null
  device: string
  email?: string | null
}

export interface CalendarSubscription {
  token: string
  sport: string
  team: string
  leagues: string[]
  created_at: string
  last_seen: string | null
  fetch_count: number
  last_user_agent: string | null
  active: boolean
}

export interface SubscriptionDashboard {
  active_count: number
  pending_count: number
  dormant_count: number
  active_window_days: number
  subscriptions: CalendarSubscription[]
}
