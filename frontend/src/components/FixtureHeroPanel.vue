<template>
  <div
    class="fx-panel relative overflow-hidden"
    @mouseenter="hoverPaused = true"
    @mouseleave="hoverPaused = false"
    @focusin="hoverPaused = true"
    @focusout="hoverPaused = false"
  >
    <!-- 1. Flat base — the product surface every fixture shares. -->
    <div class="absolute inset-0" style="background: rgba(18,26,44,.96)"></div>

    <!-- 2. Club wash. Gradients can't be transitioned, so each fixture's wash
         is its own keyed layer and the two cross-fade over .8s. -->
    <Transition name="fx-wash">
      <div
        v-if="current"
        :key="index"
        class="absolute inset-0"
        :style="{ background: washGradient }"
      ></div>
    </Transition>

    <!-- 3. Vignette, above the wash so it grounds every fixture identically. -->
    <div
      class="absolute inset-0"
      style="background: radial-gradient(120% 80% at 50% 120%, rgba(0,0,0,.45), transparent 60%)"
    ></div>

    <template v-if="current">
      <!-- League · venue -->
      <div class="fx-eyebrow absolute">{{ eyebrow }}</div>

      <!-- Crests -->
      <div class="fx-crest-row absolute flex items-center" :class="current.isMotorsport ? 'justify-center' : 'justify-between'">
        <template v-if="current.isMotorsport">
          <!-- Motorsport rows are "<Grand Prix> / <session>", not two clubs —
               a VS between them would be nonsense, so it's one crest. -->
          <div class="flex items-center fx-solo-gap">
            <FixtureCrest :club="current.home" :icon="current.homeIcon" />
            <div class="min-w-0">
              <div class="fx-solo-title truncate">{{ current.homeTeam }}</div>
              <div class="fx-solo-sub truncate">{{ current.awayTeam }}</div>
            </div>
          </div>
        </template>
        <template v-else>
          <FixtureCrest :club="current.home" :icon="current.homeIcon" />
          <div class="fx-vs">VS</div>
          <FixtureCrest :club="current.away" :icon="current.awayIcon" />
        </template>
      </div>

      <!-- Countdown under 12h, otherwise the kickoff day + time -->
      <div class="fx-kickoff absolute flex items-baseline">
        <template v-if="countdown">
          <span class="fx-count tabular-nums">{{ countdown }}</span>
          <span class="fx-count-label">TO KICKOFF</span>
        </template>
        <span v-else class="fx-when">{{ whenLabel }}</span>
      </div>

      <!-- Dots -->
      <div v-if="fixtures.length > 1" class="fx-dots absolute flex items-center justify-center">
        <button
          v-for="(f, i) in fixtures"
          :key="f.id"
          type="button"
          class="fx-dot"
          :class="{ active: i === index }"
          :aria-label="`Show fixture ${i + 1}`"
          :aria-current="i === index"
          @click="jumpTo(i)"
        ></button>
      </div>
    </template>

    <!-- Nothing scored high enough to feature -->
    <RouterLink v-else to="/matches" class="absolute inset-0 flex flex-col items-center justify-center gap-3">
      <div class="fx-crest flex items-center justify-center" style="background: rgba(142,205,242,.16); border: 1px solid rgba(142,205,242,.35)">
        <Icon name="calendar" class="!w-8 !h-8" style="color: #8ecdf2" />
      </div>
      <div class="text-center">
        <div class="text-[15px] font-bold">More matches today</div>
        <div class="text-xs font-semibold mt-0.5" style="color: rgba(244,247,251,.55)">Browse every league and fixture</div>
      </div>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import type { Match } from '@/types'
import { clubIdentity, type ClubIdentity } from '@/utils/clubIdentity'
import FixtureCrest from './FixtureCrest.vue'
import Icon from './Icon.vue'

const props = defineProps<{ matches: Match[] }>()

const ROTATE_MS = 10_000
// Below this the panel switches from a day/time label to a live countdown.
const COUNTDOWN_WINDOW_MS = 12 * 60 * 60 * 1000

const index = ref(0)
const now = ref(Date.now())

interface Fixture {
  id: number
  homeTeam: string
  awayTeam: string
  home: ClubIdentity
  away: ClubIdentity
  homeIcon: string | null
  awayIcon: string | null
  league: string
  venue: string | null
  startMs: number
  isMotorsport: boolean
}

const fixtures = computed<Fixture[]>(() =>
  props.matches.map((m) => {
    const home = clubIdentity(m.home_team, { color: m.home_color })
    return {
      id: m.id,
      homeTeam: m.home_team,
      awayTeam: m.away_team,
      home,
      away: clubIdentity(m.away_team, { color: m.away_color, avoid: home.color }),
      homeIcon: m.home_icon_cropped ?? m.home_icon ?? null,
      awayIcon: m.away_icon_cropped ?? m.away_icon ?? null,
      league: m.league.name,
      venue: m.venue ?? null,
      startMs: new Date(m.start_time).getTime(),
      isMotorsport: m.sport === 'motorsport',
    }
  }),
)

const current = computed<Fixture | undefined>(() => fixtures.value[index.value])

const eyebrow = computed(() => {
  const f = current.value
  if (!f) return ''
  if (!f.venue) return f.league
  // Venue is "<Stadium>, <City>" — the city is the part this single-line,
  // fixed-width label can least afford, so it's dropped here (the full
  // string is still what's used everywhere else, e.g. the calendar feed and
  // structured data). "League · Stadium" still overflows for a handful of
  // long combinations, which the ellipsis below handles.
  const stadium = f.venue.split(',')[0].trim()
  return `${f.league} · ${stadium}`
})

const washGradient = computed(() => {
  const f = current.value
  if (!f) return 'transparent'
  return `linear-gradient(100deg, ${f.home.color}29 0%, ${f.home.color}29 44%, ${f.away.color}29 56%, ${f.away.color}29 100%)`
})

const msToKickoff = computed(() => (current.value ? current.value.startMs - now.value : 0))

const countdown = computed(() => {
  const ms = msToKickoff.value
  if (!current.value || ms <= 0 || ms >= COUNTDOWN_WINDOW_MS) return null
  const total = Math.floor(ms / 1000)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(Math.floor(total / 3600))}:${pad(Math.floor((total % 3600) / 60))}:${pad(total % 60)}`
})

const whenLabel = computed(() => {
  const f = current.value
  if (!f) return ''
  const start = new Date(f.startMs)
  const time = start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  return `${dayLabel(start).toUpperCase()} · ${time}`
})

function dayLabel(start: Date): string {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const that = new Date(start)
  that.setHours(0, 0, 0, 0)
  const diffDays = Math.round((that.getTime() - today.getTime()) / 86_400_000)
  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'tomorrow'
  if (diffDays === -1) return 'yesterday'
  return start.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })
}

// While hovered/focused the panel freezes completely — fixture, crests and
// countdown all hold still, so it can be inspected (or screenshotted)
// without the 1s countdown tick or 10s rotation moving things mid-look.
const hoverPaused = ref(false)

declare global {
  interface Window {
    freeze?: boolean
  }
}

// Dev hook: typing `freeze = true` in the devtools console freezes the panel
// the same way hovering does (`freeze = false` releases it), without needing
// the mouse to stay put. Read directly off `window` on every tick instead of
// wiring a getter/setter — plain reads see a console-assigned global exactly
// like any other page script would, no property-interception edge cases.
function isFrozen(): boolean {
  return hoverPaused.value || window.freeze === true
}

let rotateTimer: number | null = null
let tickTimer: number | null = null

function startRotation() {
  if (rotateTimer !== null) window.clearInterval(rotateTimer)
  if (fixtures.value.length < 2) return
  rotateTimer = window.setInterval(() => {
    if (isFrozen()) return
    index.value = (index.value + 1) % fixtures.value.length
  }, ROTATE_MS)
}

function jumpTo(i: number) {
  index.value = i
  startRotation() // a manual jump earns a full dwell, not the tail of the old one
}

onMounted(() => {
  if (typeof window.freeze !== 'boolean') window.freeze = false
  tickTimer = window.setInterval(() => {
    if (isFrozen()) return
    now.value = Date.now()
  }, 1000)
  startRotation()
})

onBeforeUnmount(() => {
  if (rotateTimer !== null) window.clearInterval(rotateTimer)
  if (tickTimer !== null) window.clearInterval(tickTimer)
})

// Fixtures arrive after the first paint, and can shrink on refresh.
watch(
  () => props.matches,
  () => {
    if (index.value >= fixtures.value.length) index.value = 0
    startRotation()
  },
)
</script>

<style scoped>
.fx-panel {
  --fx-pad: 16px;
  --fx-crest-w: 92px;
  --fx-crest-h: 108px;
  --fx-crest-radius: 18px 18px 30px 30px;
  --fx-monogram: 19px;
  --fx-count: 30px;
  --fx-label: 10px;
  height: 272px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

@media (min-width: 1024px) {
  .fx-panel {
    --fx-pad: 28px;
    --fx-crest-w: 120px;
    --fx-crest-h: 138px;
    --fx-crest-radius: 24px 24px 40px 40px;
    --fx-monogram: 24px;
    --fx-count: 44px;
    --fx-label: 12px;
    height: 380px;
    border-radius: 28px;
  }
}

.fx-eyebrow {
  top: var(--fx-pad);
  left: var(--fx-pad);
  right: var(--fx-pad);
  font-size: var(--fx-label);
  font-weight: 800;
  letter-spacing: 2.2px;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.85);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fx-crest-row {
  left: var(--fx-pad);
  right: var(--fx-pad);
  top: 50%;
  transform: translateY(-67%);
}

@media (min-width: 1024px) {
  .fx-crest-row {
    transform: translateY(-60%);
  }
}

.fx-crest {
  width: var(--fx-crest-w);
  height: var(--fx-crest-h);
  border-radius: var(--fx-crest-radius);
  flex: none;
}

.fx-vs {
  font-size: calc(var(--fx-label) + 4px);
  font-weight: 800;
  letter-spacing: 3px;
  color: rgba(255, 255, 255, 0.9);
}

.fx-solo-gap {
  gap: calc(var(--fx-pad) * 0.7);
}

.fx-solo-title {
  font-size: calc(var(--fx-label) + 5px);
  font-weight: 800;
}

.fx-solo-sub {
  font-size: calc(var(--fx-label) + 1px);
  font-weight: 600;
  margin-top: 2px;
  color: rgba(255, 255, 255, 0.6);
}

.fx-kickoff {
  left: var(--fx-pad);
  right: var(--fx-pad);
  bottom: calc(var(--fx-pad) + 18px);
  gap: 10px;
}

.fx-count {
  font-size: var(--fx-count);
  font-weight: 800;
  line-height: 1;
  color: #fff;
  letter-spacing: -0.01em;
}

.fx-count-label,
.fx-when {
  font-size: var(--fx-label);
  font-weight: 800;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.6);
}

.fx-when {
  font-size: calc(var(--fx-count) * 0.62);
  letter-spacing: 0.5px;
  color: #fff;
  line-height: 1;
}

.fx-dots {
  left: var(--fx-pad);
  right: var(--fx-pad);
  bottom: var(--fx-pad);
  gap: 5px;
}

.fx-dot {
  width: 6px;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.25);
  cursor: pointer;
  transition: width 0.4s ease, background-color 0.4s ease;
}

.fx-dot.active {
  width: 18px;
  background: #8ecdf2;
}

.fx-wash-enter-active,
.fx-wash-leave-active {
  transition: opacity 0.8s ease;
}

.fx-wash-enter-from,
.fx-wash-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .fx-wash-enter-active,
  .fx-wash-leave-active,
  .fx-dot {
    transition: none;
  }
}
</style>
