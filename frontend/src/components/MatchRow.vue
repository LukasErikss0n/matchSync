<template>
  <div
    class="group relative flex items-center gap-2 sm:gap-3 px-3 sm:px-6 py-4 border-b border-white/[0.06] transition-colors hover:bg-white/[0.04]"
    :class="{ 'cursor-pointer': supportsStandings }"
    :title="supportsStandings ? 'View standings' : undefined"
    @click="supportsStandings && emit('view-standings', match)"
  >
    <template v-if="isMotorsport">
      <div class="flex-shrink-0 w-12 sm:w-16 text-[10px] sm:text-[11px] font-bold uppercase tracking-wide tabular-nums" style="color: rgba(244,247,251,.4)">
        {{ timeLabel }}
      </div>
      <div class="flex-1 flex items-center gap-2.5 sm:gap-3 min-w-0">
        <TeamBadge :name="match.home_team" :icon="homeIcon" :size="badgeSize" />
        <div class="min-w-0">
          <div class="font-bold text-xs sm:text-sm truncate">{{ match.home_team }}</div>
          <div class="text-[11px] sm:text-xs font-semibold truncate" style="color: rgba(244,247,251,.5)">{{ match.away_team }}</div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="flex-shrink-0 flex items-center" :class="isLive ? '' : 'w-8 sm:w-12'">
        <span
          v-if="isLive"
          class="inline-flex items-center gap-1.5 rounded-full px-2 sm:px-2.5 py-1 text-[9px] sm:text-[10px] font-extrabold uppercase tracking-wide whitespace-nowrap"
          style="background: rgba(142,205,242,.16); border: 1px solid rgba(142,205,242,.35); color: #bfe2f7"
        >
          <span class="match-live-dot" />
          Live
        </span>
        <span
          v-else
          class="text-[10px] sm:text-[11px] font-bold uppercase tracking-wide"
          style="color: rgba(244,247,251,.4)"
        >
          {{ leftLabel }}
        </span>
      </div>

      <div class="flex-1 flex items-center justify-end gap-1.5 sm:gap-2.5 min-w-0">
        <span class="font-bold text-xs sm:text-sm text-right break-words">{{ match.home_team }}</span>
        <TeamBadge :name="match.home_team" :icon="homeIcon" :size="badgeSize" />
      </div>

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

      <div class="flex-1 flex items-center gap-1.5 sm:gap-2.5 min-w-0">
        <TeamBadge :name="match.away_team" :icon="awayIcon" :size="badgeSize" />
        <span class="font-bold text-xs sm:text-sm break-words">{{ match.away_team }}</span>
      </div>
    </template>

    <svg
      v-if="supportsStandings"
      class="flex-shrink-0 transition-opacity sm:group-hover:opacity-0"
      width="7"
      height="12"
      viewBox="0 0 7 12"
      fill="none"
      style="color: rgba(244,247,251,.35)"
    >
      <path d="M1 1l5 5-5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>

    <div class="hidden sm:block absolute right-3 sm:right-10 top-1/2 -translate-y-1/2">
      <button
        class="flex items-center gap-1.5 rounded-full transition-all opacity-0 group-hover:opacity-100 px-3.5 py-2 text-xs font-bold"
        style="background: rgba(21,30,48,.95); border: 1px solid rgba(255,255,255,.14); color: rgba(244,247,251,.75)"
        title="Add to calendar"
        @click.stop="emit('add', match)"
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
import { nowMs } from '@/utils/clock'
import { matchState } from '@/utils/matchState'
import TeamBadge from './TeamBadge.vue'
import Icon from './Icon.vue'

const props = defineProps<{ match: Match }>()
const emit = defineEmits<{ add: [match: Match]; 'view-standings': [match: Match] }>()

const supportsStandings = computed(() => !!props.match.league.supports_standings)

const homeIcon = computed(() => props.match.home_icon_cropped ?? props.match.home_icon ?? null)
const awayIcon = computed(() => props.match.away_icon_cropped ?? props.match.away_icon ?? null)
const isMotorsport = computed(() => props.match.sport === 'motorsport')

const hasScore = computed(
  () => props.match.home_score != null && props.match.away_score != null,
)

const kickoff = computed(() => new Date(props.match.start_time))

const state = computed(() => matchState(props.match, nowMs.value))
const isLive = computed(() => state.value === 'live')
const finished = computed(() => state.value === 'finished')

const timeLabel = computed(() =>
  kickoff.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
)

const leftLabel = computed(() => {
  if (isLive.value) return 'LIVE'
  return finished.value ? 'FT' : ''
})

const centerText = computed(() => {
  if (hasScore.value) return `${props.match.home_score}-${props.match.away_score}`
  if (isLive.value) return '0-0'
  return finished.value ? '–' : timeLabel.value
})

const badgeSize = computed(() =>
  typeof window !== 'undefined' && window.innerWidth < 640 ? 28 : 34,
)
</script>
