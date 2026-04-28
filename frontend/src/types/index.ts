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

export interface Sport {
  id: string
  label: string
  icon: IconName
  leagues: string[]
}

export interface CalendarLink {
  team: string
  league: string
  url: string
}
