import { computed, ref } from 'vue'
import type { Match } from '@/types'
import { fetchFeaturedMatches } from './sports'
import { detectRegion } from '@/utils/region'

// Module-level singleton — shared across every Hero.vue mount, so switching
// tabs and back doesn't flash the fallback card while a fresh fetch resolves.
// undefined = never fetched yet, [] = fetched, nothing scored high enough.
export const cachedFeaturedMatches = ref<Match[] | undefined>(undefined)

// The hero rotates through these; other callers just want the top one.
export const cachedFeaturedMatch = computed<Match | null | undefined>(() => {
  if (cachedFeaturedMatches.value === undefined) return undefined
  return cachedFeaturedMatches.value[0] ?? null
})

export async function refreshFeaturedMatch(): Promise<void> {
  try {
    cachedFeaturedMatches.value = await fetchFeaturedMatches(detectRegion(), 3)
  } catch {
    // Keep whatever was cached before; only clear to [] if we never had data.
    if (cachedFeaturedMatches.value === undefined) cachedFeaturedMatches.value = []
  }
}
