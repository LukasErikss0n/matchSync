import { computed, ref, type Ref } from 'vue'
import type { Match } from '@/types'

const DAY = 86_400_000

function startOfWeek(d: Date): Date {
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  const day = (x.getDay() + 6) % 7
  x.setDate(x.getDate() - day)
  return x
}

function dayKey(d: Date): string {
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`
}

function dayLabel(d: Date): string {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const that = new Date(d)
  that.setHours(0, 0, 0, 0)
  const diff = Math.round((that.getTime() - today.getTime()) / DAY)
  if (diff === 0) return 'Today'
  if (diff === -1) return 'Yesterday'
  if (diff === 1) return 'Tomorrow'
  return d.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })
}

export function formatSessionTime(iso: string): string {
  return new Date(iso)
    .toLocaleString([], {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
    .replace(',', '')
}

interface MatchGroup {
  key: string
  label: string
  date: number
  matches: Match[]
}

export function useWeekWindow(matches: Ref<Match[]>, selectedSport: Ref<string | undefined>) {
  const weekOffset = ref(0)
  const autoWeekOffset = ref(0)

  const isMotorsportLeague = computed(() => selectedSport.value === 'motorsport')

  const windowStart = computed(() => {
    const base = startOfWeek(new Date())
    return new Date(base.getTime() + weekOffset.value * 7 * DAY)
  })
  const windowEnd = computed(() => new Date(windowStart.value.getTime() + 7 * DAY))

  function jumpToRelevantWeek() {
    if (!matches.value.length) {
      weekOffset.value = 0
      autoWeekOffset.value = 0
      return
    }
    const now = Date.now()
    const sorted = [...matches.value].sort(
      (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
    )
    const target = sorted.find((m) => new Date(m.start_time).getTime() >= now) ?? sorted[sorted.length - 1]
    const base = startOfWeek(new Date()).getTime()
    const tgt = startOfWeek(new Date(target.start_time)).getTime()
    weekOffset.value = Math.round((tgt - base) / (7 * DAY))
    autoWeekOffset.value = weekOffset.value
  }

  const visibleMatches = computed(() =>
    matches.value.filter((m) => {
      const t = new Date(m.start_time).getTime()
      return t >= windowStart.value.getTime() && t < windowEnd.value.getTime()
    }),
  )

  const meetingRounds = computed(() => {
    const earliest = new Map<string, number>()
    for (const m of matches.value) {
      const t = new Date(m.start_time).getTime()
      const prev = earliest.get(m.home_team)
      if (prev === undefined || t < prev) earliest.set(m.home_team, t)
    }
    const ordered = [...earliest.entries()].sort((a, b) => a[1] - b[1])
    return new Map(ordered.map(([name], i) => [name, i + 1]))
  })

  const visibleGroups = computed<MatchGroup[]>(() => {
    if (isMotorsportLeague.value) {
      const groups = new Map<string, MatchGroup>()
      for (const m of visibleMatches.value) {
        const key = m.home_team
        if (!groups.has(key)) {
          const round = meetingRounds.value.get(m.home_team)
          groups.set(key, {
            key,
            label: round ? `Round ${round} · ${m.home_team}` : m.home_team,
            date: new Date(m.start_time).getTime(),
            matches: [],
          })
        }
        const g = groups.get(key)!
        g.matches.push(m)
        g.date = Math.min(g.date, new Date(m.start_time).getTime())
      }
      const arr = [...groups.values()].sort((a, b) => a.date - b.date)
      for (const g of arr) {
        g.matches.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
      }
      return arr
    }

    const groups = new Map<string, MatchGroup>()
    for (const m of visibleMatches.value) {
      const d = new Date(m.start_time)
      const key = dayKey(d)
      if (!groups.has(key)) {
        const dd = new Date(d)
        dd.setHours(0, 0, 0, 0)
        groups.set(key, { key, label: dayLabel(d), date: dd.getTime(), matches: [] })
      }
      groups.get(key)!.matches.push(m)
    }
    const arr = [...groups.values()].sort((a, b) => a.date - b.date)
    for (const g of arr) {
      g.matches.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    }
    return arr
  })

  const windowTitle = computed(() => {
    const s = windowStart.value
    const e = new Date(windowEnd.value.getTime() - DAY)
    const sameMonth = s.getMonth() === e.getMonth()
    const month = (d: Date) => d.toLocaleDateString([], { month: 'short' })
    if (sameMonth) return `${s.getDate()}–${e.getDate()} ${month(e)}`
    return `${s.getDate()} ${month(s)} – ${e.getDate()} ${month(e)}`
  })
  const windowSubtitle = computed(() => `${visibleMatches.value.length} matches this week`)

  return {
    weekOffset,
    autoWeekOffset,
    windowStart,
    isMotorsportLeague,
    visibleGroups,
    windowTitle,
    windowSubtitle,
    jumpToRelevantWeek,
  }
}
