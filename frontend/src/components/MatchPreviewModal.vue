<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    style="background: rgba(5, 8, 14, 0.6); backdrop-filter: blur(8px)"
    @click.self="emit('close')"
  >
    <div
      class="glass-panel relative rounded-[30px] w-full max-w-md fade-up overflow-hidden"
      style="background: rgba(22,32,52,.9); backdrop-filter: blur(32px) saturate(150%); border: 1px solid rgba(255,255,255,.2)"
    >
      <div
        class="absolute inset-0 pointer-events-none"
        style="background: linear-gradient(100deg, rgba(142,205,242,.05) 0%, rgba(142,205,242,.02) 35%, transparent 65%)"
      ></div>

      <!-- Header -->
      <div class="relative flex items-center justify-between px-7 pt-7">
        <div class="text-[11.5px] font-bold uppercase ms-text-accent" style="letter-spacing: 1.8px">
          {{ dateLabel }}
        </div>
        <button class="xcl-btn-1 w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" @click="emit('close')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M6 6l12 12M18 6 6 18"/></svg>
        </button>
      </div>

      <!-- Teams -->
      <div class="relative flex items-center justify-center gap-5 sm:gap-7 px-7 pt-5 pb-7">
        <div class="flex flex-col items-center gap-2 min-w-0">
          <TeamBadge :name="match.home_team" :icon="match.home_icon" :size="64" />
          <span class="font-bold text-sm text-center max-w-[7.5rem]" style="overflow-wrap: anywhere">{{ match.home_team }}</span>
          <span v-if="loading" class="ms-skeleton" style="width: 34px; height: 18px; border-radius: 999px"></span>
          <span v-else-if="homePosition" class="text-[11px] font-bold px-2 py-0.5 rounded-full" style="background: rgba(255,255,255,.1); color: rgba(244,247,251,.6)">
            {{ ordinal(homePosition) }}
          </span>
        </div>

        <div
          class="flex-shrink-0 px-3.5 py-1.5 rounded-full text-sm font-extrabold tabular-nums"
          style="border: 1px solid rgba(255,255,255,.25); color: var(--ms-text)"
        >
          {{ timeLabel }}
        </div>

        <div class="flex flex-col items-center gap-2 min-w-0">
          <TeamBadge :name="match.away_team" :icon="match.away_icon" :size="64" />
          <span class="font-bold text-sm text-center max-w-[7.5rem]" style="overflow-wrap: anywhere">{{ match.away_team }}</span>
          <span v-if="loading" class="ms-skeleton" style="width: 34px; height: 18px; border-radius: 999px"></span>
          <span v-else-if="awayPosition" class="text-[11px] font-bold px-2 py-0.5 rounded-full" style="background: rgba(255,255,255,.1); color: rgba(244,247,251,.6)">
            {{ ordinal(awayPosition) }}
          </span>
        </div>
      </div>

      <div class="relative border-t border-white/10"></div>

      <!-- Last 5 matches -->
      <div class="relative px-7 py-5">
        <div class="text-[10.5px] font-bold uppercase tracking-widest mb-3" style="color: rgba(244,247,251,.4)">
          Last 5 matches
        </div>

        <template v-if="loading">
          <div v-for="n in 2" :key="`form-skeleton-${n}`" class="flex items-center justify-between py-1.5">
            <div class="flex items-center gap-2.5">
              <span class="ms-skeleton flex-shrink-0" style="width: 22px; height: 22px; border-radius: 999px"></span>
              <span class="ms-skeleton block" style="width: 90px; height: 13px"></span>
            </div>
            <div class="flex gap-1.5">
              <span v-for="i in 5" :key="i" class="ms-skeleton flex-shrink-0" style="width: 20px; height: 20px; border-radius: 999px"></span>
            </div>
          </div>
        </template>
        <template v-else-if="homeForm || awayForm">
          <div v-if="homeForm" class="flex items-center justify-between py-1.5">
            <div class="flex items-center gap-2.5 min-w-0">
              <TeamBadge :name="match.home_team" :icon="match.home_icon" :size="28" />
              <span class="font-bold text-sm truncate">{{ match.home_team }}</span>
            </div>
            <div class="flex gap-1.5 flex-shrink-0">
              <span v-for="(r, i) in homeForm" :key="i" class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" :style="formStyle(r)">{{ r }}</span>
            </div>
          </div>
          <div v-if="awayForm" class="flex items-center justify-between py-1.5">
            <div class="flex items-center gap-2.5 min-w-0">
              <TeamBadge :name="match.away_team" :icon="match.away_icon" :size="28" />
              <span class="font-bold text-sm truncate">{{ match.away_team }}</span>
            </div>
            <div class="flex gap-1.5 flex-shrink-0">
              <span v-for="(r, i) in awayForm" :key="i" class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" :style="formStyle(r)">{{ r }}</span>
            </div>
          </div>
        </template>
        <div v-else class="text-sm py-2" style="color: rgba(244,247,251,.5)">
          Recent form isn't available for this league yet.
        </div>
      </div>

      <!-- View full standings -->
      <div class="relative px-7 pb-7">
        <span v-if="loading" class="ms-skeleton block" style="width: 100%; height: 52px; border-radius: 16px"></span>
        <button
          v-else-if="standings"
          class="vfs-btn-1 rounded-2xl w-full py-3.5 font-bold text-[15px] transition-colors"
          style="color: var(--ms-text)"
          @click="emit('view-full-standings')"
        >
          View full standings
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Match, StandingEntry } from '@/types'
import { fetchStandings } from '@/services/sports'
import TeamBadge from './TeamBadge.vue'

const props = defineProps<{ match: Match }>()
const emit = defineEmits<{ close: []; 'view-full-standings': [] }>()

const loading = ref(true)
const standings = ref<StandingEntry[] | null>(null)

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  // Locking scroll removes the scrollbar, which shrinks the viewport and
  // shifts everything left of it — pad the gap back in so nothing jumps.
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
  document.body.style.overflow = 'hidden'
  if (scrollbarWidth > 0) document.body.style.paddingRight = `${scrollbarWidth}px`

  try {
    standings.value = await fetchStandings(props.match.league.slug)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  document.body.style.paddingRight = ''
})

function findEntry(team: string): StandingEntry | undefined {
  return standings.value?.find((e) => e.team === team)
}

const homePosition = computed(() => findEntry(props.match.home_team)?.position ?? null)
const awayPosition = computed(() => findEntry(props.match.away_team)?.position ?? null)
const homeForm = computed(() => findEntry(props.match.home_team)?.form ?? null)
const awayForm = computed(() => findEntry(props.match.away_team)?.form ?? null)

function ordinal(n: number): string {
  const rem100 = n % 100
  if (rem100 >= 11 && rem100 <= 13) return `${n}th`
  switch (n % 10) {
    case 1: return `${n}st`
    case 2: return `${n}nd`
    case 3: return `${n}rd`
    default: return `${n}th`
  }
}

function formStyle(result: string): string {
  if (result === 'W') return 'background: rgba(78,201,144,.22); color: #7de3ab'
  if (result === 'L') return 'background: rgba(232,93,117,.22); color: #f596a8'
  return 'background: rgba(255,255,255,.14); color: rgba(244,247,251,.7)'
}

const kickoff = computed(() => new Date(props.match.start_time))

const timeLabel = computed(() =>
  kickoff.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
)

const dateLabel = computed(() => {
  const now = new Date()
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const diffDays = Math.round((startOfDay(kickoff.value) - startOfDay(now)) / 86400000)
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Tomorrow'
  return kickoff.value.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
})
</script>

<style scoped>
/* Bare-icon close button, matching TeamSelectorModal's cross. */
.xcl-btn-1 {
  background: transparent;
  border: none;
  transition: transform 0.15s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.15s ease;
}
.xcl-btn-1:hover {
  opacity: 0.7;
  transform: scale(1.08);
}
.xcl-btn-1:active {
  transform: scale(0.92);
}

@media (prefers-reduced-motion: reduce) {
  .xcl-btn-1:hover,
  .xcl-btn-1:active {
    transform: none;
  }
}

.vfs-btn-1 {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.16);
}
.vfs-btn-1:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.28);
}
.vfs-btn-1:active {
  background: rgba(255, 255, 255, 0.03);
}
</style>
