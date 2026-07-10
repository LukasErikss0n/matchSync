import { ref } from 'vue'
import type { Match } from '@/types'
import { fetchFeaturedMatch } from './sports'

// Module-level singleton — shared across every Hero.vue mount, so switching
// tabs and back doesn't flash the fallback card while a fresh fetch resolves.
// undefined = never fetched yet, null = fetched, nothing scored high enough.
export const cachedFeaturedMatch = ref<Match | null | undefined>(undefined)

export async function refreshFeaturedMatch(): Promise<void> {
  try {
    cachedFeaturedMatch.value = await fetchFeaturedMatch()
  } catch {
    // Keep whatever was cached before; only clear to null if we never had data.
    if (cachedFeaturedMatch.value === undefined) cachedFeaturedMatch.value = null
  }
}
