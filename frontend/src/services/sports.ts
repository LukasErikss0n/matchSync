import type { CalendarLink, Sport } from '@/types'
import { slugify } from '@/utils'

const API_BASE = '/api'

export async function fetchSports(): Promise<Sport[]> {
  const res = await fetch(`${API_BASE}/sports`)
  if (!res.ok) throw new Error(`Failed to fetch sports: ${res.status}`)
  return res.json()
}

export async function fetchTeams(league: string): Promise<string[]> {
  const res = await fetch(`${API_BASE}/leagues/${encodeURIComponent(slugify(league))}/teams`)
  if (!res.ok) throw new Error(`Failed to fetch teams: ${res.status}`)
  return res.json()
}

export async function fetchCalendarLink(team: string, league: string): Promise<CalendarLink> {
  const res = await fetch(`${API_BASE}/calendar?team=${encodeURIComponent(team)}&league=${encodeURIComponent(league)}`)
  if (!res.ok) throw new Error(`Failed to fetch calendar link: ${res.status}`)
  return res.json()
}
