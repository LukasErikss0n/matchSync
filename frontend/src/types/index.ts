export type IconName =
  | 'football'
  | 'hockey'
  | 'basketball'
  | 'baseball'
  | 'amfootball'
  | 'rugby'
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
  leagues: League[]
}

export interface CalendarLink {
  team: string
  sport: string
  leagues: League[]
  url: string
}
