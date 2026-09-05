<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop"
    :class="{ 'is-closing': closing }"
    style="background: rgba(5, 8, 14, 0.6); backdrop-filter: blur(8px)"
    @click.self="handleClose"
  >
    <div
      class="glass-panel relative rounded-[30px] w-full max-w-xl modal-panel overflow-hidden"
      :class="{ 'is-closing': closing }"
      style="max-height: 90vh; overflow-y: auto; background: rgba(22,32,52,.9); backdrop-filter: blur(32px) saturate(150%); border: 1px solid rgba(255,255,255,.2)"
    >
      <div
        class="absolute inset-0 pointer-events-none"
        style="background: linear-gradient(100deg, rgba(142,205,242,.05) 0%, rgba(142,205,242,.02) 35%, transparent 65%)"
      ></div>

      <!-- Header -->
      <div class="relative flex items-center justify-between px-7 pt-7 pb-5 border-b border-white/10">
        <div>
          <div class="text-[11.5px] font-bold uppercase mb-1 ms-text-accent" style="letter-spacing: 1.8px">
            Standings · {{ leagueName }}
          </div>
          <h2 class="text-2xl font-extrabold" style="letter-spacing: -0.5px">{{ homeTeam }} vs {{ awayTeam }}</h2>
        </div>
        <button
          class="xcl-btn-1 w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0"
          :class="{ 'xcl-closing-1': closing }"
          @click="handleClose"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round">
            <path class="xcl-cross-a" d="M6 6 18 18"/>
            <path class="xcl-cross-b" d="M18 6 6 18"/>
          </svg>
        </button>
      </div>

      <div class="relative px-3 sm:px-4 pb-5 pt-2">
        <template v-if="loading">
          <div class="grid px-4 py-2 text-[10.5px] font-bold uppercase tracking-widest" style="grid-template-columns: 28px 1fr 52px 44px; color: rgba(244,247,251,.4)">
            <span>#</span>
            <span>Team</span>
            <span class="text-right">GD</span>
            <span class="text-right">Pts</span>
          </div>
          <div v-for="n in 8" :key="`standings-skeleton-${n}`" class="grid items-center px-4 py-3 mb-1.5" style="grid-template-columns: 28px 1fr 52px 44px">
            <span class="ms-skeleton" style="width: 16px; height: 13px"></span>
            <div class="flex items-center gap-2 min-w-0">
              <span class="ms-skeleton flex-shrink-0" style="width: 30px; height: 30px; border-radius: 999px"></span>
              <span class="ms-skeleton block" style="width: 60%; height: 13px"></span>
            </div>
            <span class="ms-skeleton justify-self-end" style="width: 24px; height: 13px"></span>
            <span class="ms-skeleton justify-self-end" style="width: 20px; height: 13px"></span>
          </div>
        </template>
        <div v-else-if="standings === null" class="py-14 text-center text-sm px-4" style="color: rgba(244,247,251,.5)">
          Standings aren't available for this league yet.
        </div>
        <div v-else-if="standings.length === 0" class="py-14 text-center text-sm" style="color: rgba(244,247,251,.5)">
          No table data found.
        </div>
        <template v-else>
          <div class="grid px-4 py-2 text-[10.5px] font-bold uppercase tracking-widest" style="grid-template-columns: 28px 1fr 52px 44px; color: rgba(244,247,251,.4)">
            <span>#</span>
            <span>Team</span>
            <span class="text-right">GD</span>
            <span class="text-right">Pts</span>
          </div>
          <div
            v-for="entry in standings"
            :key="entry.position"
            class="grid items-start px-4 py-3 rounded-2xl mb-1.5 transition-colors"
            :style="`grid-template-columns: 28px 1fr 52px 44px; ${isFocusTeam(entry.team)
              ? 'background: rgba(142,205,242,.12); border: 1px solid rgba(142,205,242,.35)'
              : 'border: 1px solid transparent'}`"
          >
            <span class="text-sm font-bold" style="color: rgba(244,247,251,.5)">{{ entry.position }}</span>
            <div class="min-w-0">
              <div class="flex items-center gap-2 min-w-0">
                <TeamBadge :name="entry.team" :icon="entry.team_icon" :size="30" />
                <span class="font-bold text-sm truncate">{{ entry.team }}</span>
              </div>
              <div class="flex gap-1 mt-1.5 ml-[38px]">
                <span
                  v-for="(r, i) in entry.form"
                  :key="i"
                  class="w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
                  :style="formStyle(r)"
                >{{ r }}</span>
              </div>
            </div>
            <span class="text-sm font-bold text-right" :style="entry.goal_difference > 0 ? 'color: var(--ms-green)' : 'color: rgba(244,247,251,.7)'">
              {{ entry.goal_difference > 0 ? '+' : '' }}{{ entry.goal_difference }}
            </span>
            <span class="text-sm font-extrabold text-right ms-text-accent">{{ entry.points }}</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { StandingEntry } from '@/types'
import { fetchStandings } from '@/services/sports'
import TeamBadge from './TeamBadge.vue'

const props = defineProps<{
  leagueSlug: string
  leagueName: string
  homeTeam: string
  awayTeam: string
}>()

const emit = defineEmits<{ close: [] }>()

const loading = ref(true)
const standings = ref<StandingEntry[] | null>(null)

// Same reverse-animation-then-unmount pattern as TeamSelectorModal — closing
// by simply vanishing looked abrupt next to the panel's animated entrance.
const closing = ref(false)
const CLOSE_ANIMATION_MS = 180
function handleClose() {
  if (closing.value) return
  closing.value = true
  setTimeout(() => emit('close'), CLOSE_ANIMATION_MS)
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') handleClose()
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  // Locking scroll removes the scrollbar, which shrinks the viewport and
  // shifts everything left of it — pad the gap back in so nothing jumps.
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
  document.body.style.overflow = 'hidden'
  if (scrollbarWidth > 0) document.body.style.paddingRight = `${scrollbarWidth}px`

  try {
    standings.value = await fetchStandings(props.leagueSlug)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  document.body.style.paddingRight = ''
})

function isFocusTeam(name: string): boolean {
  return name === props.homeTeam || name === props.awayTeam
}

function formStyle(result: string): string {
  if (result === 'W') return 'background: rgba(78,201,144,.22); color: #7de3ab'
  if (result === 'L') return 'background: rgba(232,93,117,.22); color: #f596a8'
  return 'background: rgba(255,255,255,.14); color: rgba(244,247,251,.7)'
}
</script>

<style scoped>
.modal-backdrop {
  /* Chromium quirk: an element with any active CSS `animation` stops
     correctly inheriting `color` (computes as transparent) unless it's set
     explicitly here — even though the animation itself only touches
     opacity. Reproduces mid-animation too, not just once "forwards" freezes
     it. Setting `color: inherit` sidesteps it. */
  color: inherit;
  animation: backdropIn 0.22s ease forwards;
}
.modal-backdrop.is-closing {
  animation: backdropIn 0.18s ease reverse forwards;
}
@keyframes backdropIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-panel {
  color: inherit; /* see .modal-backdrop comment above */
  animation: panelIn 0.32s cubic-bezier(0.2, 0.9, 0.3, 1) forwards;
}
.modal-panel.is-closing {
  animation: panelIn 0.18s ease reverse forwards;
}
@keyframes panelIn {
  from { opacity: 0; transform: translateY(14px) scale(0.98); }
  to { opacity: 1; transform: none; }
}

@media (prefers-reduced-motion: reduce) {
  .modal-backdrop,
  .modal-panel {
    animation: none;
  }
}

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
.xcl-cross-a,
.xcl-cross-b {
  transform-box: fill-box;
  transform-origin: center;
}
/* Scissor close: each diagonal is its own path so it can rotate independently
   to flat instead of the whole icon just scaling down (which read as nothing
   more than shrinking, not "closing"). The two strokes flatten into a single
   dash — finishing before the button's own fade-out does, so the cross
   visibly closes shut first rather than just disappearing mid-rotation. */
.xcl-closing-1 .xcl-cross-a {
  animation: xcl-flatten-a 0.13s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
.xcl-closing-1 .xcl-cross-b {
  animation: xcl-flatten-b 0.13s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
@keyframes xcl-flatten-a {
  to { transform: rotate(-45deg); }
}
@keyframes xcl-flatten-b {
  to { transform: rotate(45deg); }
}
.xcl-closing-1 {
  animation: xcl-fade-1 0.2s ease forwards;
}
@keyframes xcl-fade-1 {
  to { opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .xcl-btn-1:hover,
  .xcl-btn-1:active {
    transform: none;
  }
  .xcl-closing-1 {
    animation: none;
    opacity: 0.4;
  }
  .xcl-closing-1 .xcl-cross-a,
  .xcl-closing-1 .xcl-cross-b {
    animation: none;
  }
}
</style>
