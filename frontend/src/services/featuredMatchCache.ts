import { computed, ref } from 'vue'
import type { Match } from '@/types'
import { fetchFeaturedMatches } from './sports'
import { detectRegion } from '@/utils/region'

export const cachedFeaturedMatches = ref<Match[] | undefined>(undefined)

export const cachedFeaturedMatch = computed<Match | null | undefined>(() => {
  if (cachedFeaturedMatches.value === undefined) return undefined
  return cachedFeaturedMatches.value[0] ?? null
})

export async function refreshFeaturedMatch(): Promise<void> {
  try {
    cachedFeaturedMatches.value = await fetchFeaturedMatches(detectRegion(), 3)
  } catch {
    if (cachedFeaturedMatches.value === undefined) cachedFeaturedMatches.value = []
  }
}
