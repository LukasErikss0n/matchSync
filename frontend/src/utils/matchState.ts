import type { Match } from '@/types'

// The fetcher only pulls every ~30 minutes, so there's no real per-minute
// clock to show during a match — kickoff..kickoff+LIVE_WINDOW_MS is treated as
// "could still be playing". Mirrors backend/services/featured_match.py's
// LIVE_WINDOW; keep the two in sync.
export const LIVE_WINDOW_MS = (2 * 60 + 30) * 60 * 1000 // 2h30m — match + stoppage

export type MatchState = 'scheduled' | 'live' | 'finished'

/**
 * What to actually display for a match, combining the source's own reported
 * status (when it has one) with a kickoff-time safety net.
 *
 * Two rules drive this:
 *
 * 1. Never infer "finished" from the presence of a score. Every provider
 *    starts reporting 0-0 the moment a match kicks off, so a score means
 *    "under way or over" — reading it as "over" is what made rows flip to FT
 *    at kickoff and stay there for the full 90 minutes.
 *
 * 2. Never trust a status indefinitely. Statuses go stale: a fixture can drop
 *    out of the upstream window, a fetch can fail, or a source can stop
 *    updating mid-match (and DBStore.save only overwrites status with a
 *    truthy value, so a stale one is never cleared). Both of the non-terminal
 *    statuses are therefore bounded by the clock, so nothing can sit on LIVE
 *    forever.
 *
 * Kept here rather than duplicated per component — MatchRow and WeekMatches
 * previously each had their own copy and had already drifted apart.
 */
export function matchState(match: Pick<Match, 'start_time' | 'status'>, nowMs: number): MatchState {
  const kickoff = new Date(match.start_time).getTime()
  const withinLiveWindow = nowMs <= kickoff + LIVE_WINDOW_MS

  // Terminal and only ever set by a source that genuinely saw the match end,
  // so it needs no time bound.
  if (match.status === 'finished') return 'finished'

  // Trusted, but only for as long as the match could plausibly still be on —
  // past that the source has clearly stopped updating.
  if (match.status === 'live') return withinLiveWindow ? 'live' : 'finished'

  // Only meaningful before kickoff. Left as-is it would survive into (and
  // past) the match itself, hiding an in-progress fixture entirely.
  if (match.status === 'scheduled' && nowMs < kickoff) return 'scheduled'

  // No status, or a stale one — fall back to the clock alone.
  if (nowMs < kickoff) return 'scheduled'
  return withinLiveWindow ? 'live' : 'finished'
}
