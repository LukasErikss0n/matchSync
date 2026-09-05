import type { Match } from '@/types'

// Keep in sync with backend/services/featured_match.py's LIVE_WINDOW.
export const LIVE_WINDOW_MS = (2 * 60 + 30) * 60 * 1000

export type MatchState = 'scheduled' | 'live' | 'finished'

export function matchState(match: Pick<Match, 'start_time' | 'status'>, nowMs: number): MatchState {
  const kickoff = new Date(match.start_time).getTime()
  const withinLiveWindow = nowMs <= kickoff + LIVE_WINDOW_MS

  if (match.status === 'finished') return 'finished'
  if (match.status === 'live') return withinLiveWindow ? 'live' : 'finished'
  if (match.status === 'scheduled' && nowMs < kickoff) return 'scheduled'

  if (nowMs < kickoff) return 'scheduled'
  return withinLiveWindow ? 'live' : 'finished'
}
