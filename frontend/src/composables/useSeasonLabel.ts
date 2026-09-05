import { computed, type Ref } from 'vue'

interface SeasonConfig {
  flipMonth: number
  flipsAtMonthStart: boolean
  singleYearLabel: boolean
}

const LEAGUE_SEASON: Record<string, SeasonConfig> = {
  'premier-league': { flipMonth: 4, flipsAtMonthStart: false, singleYearLabel: false },
  'uefa-champions-league': { flipMonth: 4, flipsAtMonthStart: false, singleYearLabel: false },
  'uefa-conference-league': { flipMonth: 4, flipsAtMonthStart: false, singleYearLabel: false },
  'fa-cup': { flipMonth: 4, flipsAtMonthStart: false, singleYearLabel: false },
  'efl-cup': { flipMonth: 2, flipsAtMonthStart: false, singleYearLabel: false },
  'uefa-europa-league': { flipMonth: 4, flipsAtMonthStart: false, singleYearLabel: false },
  allsvenskan: { flipMonth: 3, flipsAtMonthStart: true, singleYearLabel: true },
  shl: { flipMonth: 2, flipsAtMonthStart: false, singleYearLabel: false },
  sdhl: { flipMonth: 2, flipsAtMonthStart: false, singleYearLabel: false },
  'sbl-herrar': { flipMonth: 3, flipsAtMonthStart: false, singleYearLabel: false },
  'sbl-damer': { flipMonth: 3, flipsAtMonthStart: false, singleYearLabel: false },
  'iihf-world-championship': { flipMonth: 4, flipsAtMonthStart: false, singleYearLabel: false },
  'formula-1': { flipMonth: 0, flipsAtMonthStart: true, singleYearLabel: true },
}

export function useSeasonLabel(windowStart: Ref<Date>, leagueSlug: Ref<string | undefined>) {
  return computed(() => {
    const viewed = windowStart.value
    const m = viewed.getMonth()
    const y = viewed.getFullYear()
    const cfg = LEAGUE_SEASON[leagueSlug.value ?? '']
    const start = cfg
      ? cfg.flipsAtMonthStart
        ? (m >= cfg.flipMonth ? y : y - 1)
        : (m > cfg.flipMonth ? y : y - 1)
      : (m > 4 ? y : y - 1)
    return cfg?.singleYearLabel ? `${start}` : `${start}/${String((start + 1) % 100).padStart(2, '0')}`
  })
}
