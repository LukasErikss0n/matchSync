<template>
  <span
    class="inline-flex items-center justify-center rounded-full overflow-hidden flex-shrink-0"
    :style="{ width: `${size}px`, height: `${size}px`, boxShadow: '0 4px 10px -4px rgba(0,0,0,.5)' }"
  >
    <img
      v-if="icon && !failed"
      :src="icon"
      :alt="name"
      class="w-full h-full"
      :class="fitContain ? 'object-contain p-1' : 'object-cover'"
      loading="lazy"
      decoding="async"
      @error="failed = true"
    />
    <span
      v-else
      class="w-full h-full flex items-center justify-center font-bold text-white select-none"
      :style="{ background: bgColor, fontSize: `${Math.round(size * 0.38)}px` }"
    >
      {{ initials }}
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{ name: string; icon?: string | null; size?: number }>(),
  { icon: null, size: 40 },
)

const failed = ref(false)
// Reset the error flag if the icon URL changes (component reused across rows)
watch(() => props.icon, () => (failed.value = false))

// The F1 series logo is a 4:1 wordmark (120x30) — object-cover in a circular
// badge crops it down to an unrecognizable sliver, so it needs to be
// letterboxed (object-contain) instead. Every other crest/flag this app uses
// is close enough to square that cover still looks right, so this is a
// narrow, name-based exception rather than a global change.
const fitContain = computed(() => props.name === 'Formula 1')

const initials = computed(() => {
  const words = props.name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return '?'
  if (words.length === 1) return words[0][0].toUpperCase()
  return (words[0][0] + words[1][0]).toUpperCase()
})

// Deterministic, pleasant color picked from the team name.
const PALETTE = [
  '#0ea5e9', '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e',
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981',
  '#14b8a6', '#3b82f6', '#64748b', '#1e293b',
]

const bgColor = computed(() => {
  let hash = 0
  for (let i = 0; i < props.name.length; i++) {
    hash = (hash * 31 + props.name.charCodeAt(i)) >>> 0
  }
  return PALETTE[hash % PALETTE.length]
})
</script>
