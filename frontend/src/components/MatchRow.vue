<template>
  <div class="group relative flex items-center gap-2 sm:gap-3 px-3 sm:px-6 py-4 border-b border-white/[0.06] transition-colors hover:bg-white/[0.04]">
    <!-- Status -->
    <div class="w-8 sm:w-12 flex-shrink-0 text-[10px] sm:text-[11px] font-bold uppercase tracking-wide" style="color: rgba(244,247,251,.4)">
      {{ leftLabel }}
    </div>

    <!-- Home -->
    <div class="flex-1 flex items-center justify-end gap-1.5 sm:gap-2.5 min-w-0">
      <span class="font-bold text-xs sm:text-sm text-right break-words">{{ match.home_team }}</span>
      <TeamBadge :name="match.home_team" :icon="match.home_icon" :size="badgeSize" />
    </div>

    <!-- Score / time -->
    <div class="flex-shrink-0">
      <div
        class="min-w-[2.75rem] sm:min-w-[3.25rem] px-2 sm:px-2.5 py-1 rounded-[10px] text-center text-xs sm:text-sm font-extrabold tabular-nums"
        :style="hasScore
          ? 'background: rgba(142,205,242,.16); border: 1px solid rgba(142,205,242,.35); color: #bfe2f7'
          : 'background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.14); color: rgba(244,247,251,.7)'"
      >
        {{ centerText }}
      </div>
    </div>

    <!-- Away -->
    <div class="flex-1 flex items-center gap-1.5 sm:gap-2.5 min-w-0">
      <TeamBadge :name="match.away_team" :icon="match.away_icon" :size="badgeSize" />
      <span class="font-bold text-xs sm:text-sm break-words">{{ match.away_team }}</span>
    </div>

    <!-- Add to calendar — absolutely positioned so it doesn't shift the row's
         flex content off-center; hidden on mobile to free up name space -->
    <div class="hidden sm:block absolute right-3 sm:right-6 top-1/2 -translate-y-1/2">
      <button
        class="flex items-center gap-1.5 rounded-full transition-all opacity-0 group-hover:opacity-100 px-3.5 py-2 text-xs font-bold"
        style="background: rgba(21,30,48,.95); border: 1px solid rgba(255,255,255,.14); color: rgba(244,247,251,.75)"
        title="Add to calendar"
        @click="emit('add', match)"
      >
        <Icon name="calendar" class="!w-4 !h-4" />
        <span>Add to calendar</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Match } from '@/types'
import TeamBadge from './TeamBadge.vue'
import Icon from './Icon.vue'

const props = defineProps<{ match: Match }>()
const emit = defineEmits<{ add: [match: Match] }>()

const hasScore = computed(
  () => props.match.home_score != null && props.match.away_score != null,
)

const kickoff = computed(() => new Date(props.match.start_time))
const isPast = computed(() => kickoff.value.getTime() < Date.now())
const finished = computed(() => hasScore.value || isPast.value)

const timeLabel = computed(() =>
  kickoff.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
)

const leftLabel = computed(() => (finished.value ? 'FT' : ''))

const centerText = computed(() => {
  if (hasScore.value) return `${props.match.home_score}-${props.match.away_score}`
  return finished.value ? '–' : timeLabel.value
})

// Smaller badges on mobile to give names more room
const badgeSize = computed(() =>
  typeof window !== 'undefined' && window.innerWidth < 640 ? 28 : 34,
)
</script>
