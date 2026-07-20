import { ref } from 'vue'

// Single shared ticking clock so every MatchRow doesn't run its own timer —
// match lists can render hundreds of rows at once. 30s is plenty granular
// for a LIVE/FT transition; nothing here needs per-second accuracy.
export const nowMs = ref(Date.now())

if (typeof window !== 'undefined') {
  window.setInterval(() => {
    nowMs.value = Date.now()
  }, 30_000)
}
