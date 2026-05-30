<template>
  <div class="group flex items-center gap-3 px-4 sm:px-6 py-4 hover:bg-slate-50 transition-colors">
    <!-- Status -->
    <div class="w-10 sm:w-12 flex-shrink-0 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
      {{ leftLabel }}
    </div>

    <!-- Home -->
    <div class="flex-1 flex items-center justify-end gap-2.5 min-w-0">
      <span class="font-semibold text-slate-800 text-sm text-right truncate">{{ match.home_team }}</span>
      <TeamBadge :name="match.home_team" :icon="match.home_icon" :size="34" />
    </div>

    <!-- Score / time -->
    <div class="flex-shrink-0">
      <div
        class="min-w-[3.25rem] px-2.5 py-1 rounded-lg text-center text-sm font-bold tabular-nums"
        :class="hasScore
          ? 'bg-slate-100 text-slate-800'
          : 'border border-slate-200 text-slate-500'"
      >
        {{ centerText }}
      </div>
    </div>

    <!-- Away -->
    <div class="flex-1 flex items-center gap-2.5 min-w-0">
      <TeamBadge :name="match.away_team" :icon="match.away_icon" :size="34" />
      <span class="font-semibold text-slate-800 text-sm truncate">{{ match.away_team }}</span>
    </div>

    <!-- Add to calendar -->
    <div class="flex-shrink-0 w-9 sm:w-auto">
      <button
        class="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white text-slate-600 hover:border-[var(--ms-blue)] hover:text-[var(--ms-blue)] transition-all
               sm:opacity-0 sm:group-hover:opacity-100 px-2 sm:px-3.5 py-2 text-xs font-semibold"
        title="Add to calendar"
        @click="emit('add', match)"
      >
        <Icon name="calendar" class="!w-4 !h-4" />
        <span class="hidden sm:inline">Add to calendar</span>
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

const leftLabel = computed(() => (finished.value ? 'FT' : timeLabel.value))

const centerText = computed(() => {
  if (hasScore.value) return `${props.match.home_score}-${props.match.away_score}`
  return finished.value ? '–' : timeLabel.value
})
</script>
