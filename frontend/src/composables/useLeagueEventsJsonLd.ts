import { onUnmounted, watch, type Ref } from 'vue'
import type { Match } from '@/types'
import { setJsonLd, removeJsonLd } from '@/utils/seo'

const JSONLD_ID = 'league-events-jsonld'
const SITE_URL = 'https://matchcalender.com'

const EVENT_DURATION_MS: Record<string, number> = {
  football: 2 * 60 * 60 * 1000,
  hockey: 2.5 * 60 * 60 * 1000,
  basketball: 2 * 60 * 60 * 1000,
  motorsport: 2 * 60 * 60 * 1000,
}
const DEFAULT_DURATION_MS = 2 * 60 * 60 * 1000

function eventImage(m: Match): string {
  const crest = m.home_icon ?? m.away_icon
  return crest && /^https?:\/\//.test(crest) ? crest : `${SITE_URL}/logo-social.png`
}

function hasVenue(m: Match): boolean {
  return !!m.venue
}

export function useLeagueEventsJsonLd(
  matches: Ref<Match[]>,
  leagueLock: Ref<string | null>,
  leagueName: Ref<string>,
  routePath: Ref<string>,
) {
  watch(
    [matches, leagueLock],
    () => {
      if (!leagueLock.value) {
        removeJsonLd(JSONLD_ID)
        return
      }
      const DAY_MS = 86_400_000
      const now = Date.now()
      const upcoming = [...matches.value]
        .filter((m) => new Date(m.start_time).getTime() >= now - 3 * DAY_MS)
        .filter(hasVenue)
        .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
        .slice(0, 25)
      if (!upcoming.length) {
        removeJsonLd(JSONLD_ID)
        return
      }
      setJsonLd(JSONLD_ID, {
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        itemListElement: upcoming.map((m, i) => {
          const teams = [
            { '@type': 'SportsTeam', name: m.home_team },
            { '@type': 'SportsTeam', name: m.away_team },
          ]
          const start = new Date(m.start_time)
          const end = new Date(start.getTime() + (EVENT_DURATION_MS[m.sport] ?? DEFAULT_DURATION_MS))
          return {
            '@type': 'ListItem',
            position: i + 1,
            item: {
              '@type': 'SportsEvent',
              name: `${m.home_team} vs ${m.away_team}`,
              description: `${leagueName.value}: ${m.home_team} vs ${m.away_team} at ${m.venue} on ${start.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}. Sync the fixture to your calendar with MatchCalender.`,
              startDate: m.start_time,
              endDate: end.toISOString(),
              eventStatus: 'https://schema.org/EventScheduled',
              eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
              image: eventImage(m),
              location: { '@type': 'Place', name: m.venue },
              competitor: teams,
              performer: teams,
              organizer: {
                '@type': 'Organization',
                name: leagueName.value,
                url: `${SITE_URL}${routePath.value}`,
              },
            },
          }
        }),
      })
    },
    { immediate: true },
  )

  onUnmounted(() => removeJsonLd(JSONLD_ID))
}
