<template>
  <div class="fxn-wrap">
    <div
      class="fxn-panel relative overflow-hidden"
      @mouseenter="hoverPaused = true"
      @mouseleave="hoverPaused = false"
      @focusin="hoverPaused = true"
      @focusout="hoverPaused = false"
    >
      <!-- Fixed surface — deliberately NOT derived from either team's colour
           (that used to be a per-fixture wash), so the card looks the same
           fixture to fixture and only the two crest tiles carry club colour. -->



      <div class="absolute inset-0" style="background: rgba(18,26,44,.96)"></div>



      <div
        class="absolute inset-0 pointer-events-none"
        style="background: radial-gradient(120% 90% at 100% 0%, rgba(142,205,242,.06), transparent 60%)"
      ></div>

      <template v-if="current">
        <div class="fxn-header relative z-[1] flex items-center justify-between gap-2">
          <span class="fxn-league truncate">{{ current.league }}</span>
          <span class="fxn-when-pill flex items-center gap-1.5 flex-none">
            <Icon name="clock" class="!w-3.5 !h-3.5" />
            {{ whenLabel }}
          </span>
        </div>

        <div class="fxn-crests relative z-[1]" :class="{ 'fxn-crests-solo': current.isMotorsport }">
          <div class="fxn-crest fxn-crest-home">
            <!-- background-image, not <img>: several crests (e.g. Premier
                 League's) are SVGs with no width/height on the root element,
                 only a viewBox — Chromium rasterises a plain <img> of one of
                 those at a small default box and stretches that bitmap up,
                 visibly blurry at this tile's size. background-size:contain
                 rasterises at the real display size instead. -->
            <div
              v-if="current.homeIcon && !homeIconFailed"
              class="fxn-logo"
              :style="homeLogoStyle"
              role="img"
              :aria-label="current.home.monogram"
            ></div>
            <span v-else class="fxn-mono">{{ current.home.monogram }}</span>
            <!-- Invisible — exists purely to get a real load/error event (and
                 the source's natural size), since a CSS background-image has
                 no equivalent of <img>'s @error. -->
            <img
              v-if="current.homeIcon"
              :src="current.homeIcon"
              alt=""
              aria-hidden="true"
              class="fxn-logo-probe"
              decoding="async"
              @error="onHomeIconError"
              @load="onHomeIconLoad"
            />
          </div>
          <div
            v-if="!current.isMotorsport"
            class="fxn-crest fxn-crest-away"
          >
            <div
              v-if="current.awayIcon && !awayIconFailed"
              class="fxn-logo"
              :style="awayLogoStyle"
              role="img"
              :aria-label="current.away.monogram"
            ></div>
            <span v-else class="fxn-mono">{{ current.away.monogram }}</span>
            <img
              v-if="current.awayIcon"
              :src="current.awayIcon"
              alt=""
              aria-hidden="true"
              class="fxn-logo-probe"
              decoding="async"
              @error="onAwayIconError"
              @load="onAwayIconLoad"
            />
          </div>

          <!-- Rotation indicator, anchored to the crest row so it doesn't
               drift when the copy below grows/shrinks between fixtures. -->
          <div v-if="fixtures.length > 1" class="fxn-dots flex flex-col items-center">
            <button
              v-for="(f, i) in fixtures"
              :key="f.id"
              type="button"
              class="fxn-dot"
              :class="{ active: i === index }"
              :aria-label="`Show fixture ${i + 1}`"
              :aria-current="i === index"
              @click="jumpTo(i)"
            ></button>
          </div>
        </div>

        <p v-if="!current.isMotorsport" class="fxn-vs relative z-[1] text-center">vs</p>

        <h2 class="fxn-title relative z-[1] text-center">
          <template v-if="current.isMotorsport">{{ current.homeTeam }}</template>
          <template v-else>{{ current.homeTeam }} vs {{ current.awayTeam }}</template>
        </h2>

        <p v-if="venueName" class="fxn-venue relative z-[1] text-center truncate">{{ venueName }}</p>

        <p v-if="countdown" class="fxn-count-line relative z-[1] text-center tabular-nums">
          {{ countdown }} to kickoff
        </p>
      </template>

      <!-- Nothing scored high enough to feature -->
      <RouterLink v-else to="/matches" class="fxn-empty relative z-[1] flex flex-col items-center justify-center gap-3">
        <div class="fx-crest flex items-center justify-center" style="background: rgba(142,205,242,.16); border: 1px solid rgba(142,205,242,.35)">
          <Icon name="calendar" class="!w-8 !h-8" style="color: #8ecdf2" />
        </div>
        <div class="text-center">
          <div class="text-[15px] font-bold">More matches today</div>
          <div class="text-xs font-semibold mt-0.5" style="color: rgba(244,247,251,.55)">Browse every league and fixture</div>
        </div>
      </RouterLink>
    </div>

    <div v-if="current" class="fxn-actions flex flex-nowrap gap-3">
      <button
        class="ms-btn-primary rounded-2xl px-6 py-3.5 font-bold text-[15px] flex items-center justify-center gap-2"
        @click="emit('getStarted')"
      >
        <Icon name="calendar" class="!w-[18px] !h-[18px]" />
        Choose your team
      </button>
      <RouterLink
        :to="seeAllRoute"
        class="ms-btn-secondary rounded-2xl px-6 py-3.5 font-bold text-[15px] text-center"
      >
        Matches
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import type { Match } from '@/types'
import { clubIdentity, type ClubIdentity } from '@/utils/clubIdentity'
import Icon from './Icon.vue'

const props = defineProps<{ matches: Match[] }>()
const emit = defineEmits<{ getStarted: [] }>()

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

// "Matches" always targets the top-ranked fixture's league, not
// whichever one happens to be rotating on screen right now.
const seeAllRoute = computed(() => {
  const top = fixtures.value[0]
  return top ? { path: '/matches', query: { league: top.league } } : '/matches'
})

// Venue is "<Stadium>, <City>" — city dropped, same reasoning as
// WeekMatches.vue: this is a single truncating line.
const venueName = computed(() => {
  const venue = current.value?.venue
  return venue ? venue.split(',')[0].trim() : null
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
  return `${dayLabel(start)} · ${time}`
})

function dayLabel(start: Date): string {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const that = new Date(start)
  that.setHours(0, 0, 0, 0)
  const diffDays = Math.round((that.getTime() - today.getTime()) / 86_400_000)
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Tomorrow'
  if (diffDays === -1) return 'Yesterday'
  return start.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })
}

// Crest load failures, reset whenever the rotation moves to a different
// fixture — a previous error must not stick to the next club shown here.
const homeIconFailed = ref(false)
const awayIconFailed = ref(false)

// Natural pixel size of each crest source, read off the load-probe <img>.
// Many crests are small raster icons — filling the tile via a plain
// `background-size: contain` stretches those past their native resolution
// and they come out visibly blurry. Capping background-size at the source's
// own dimensions lets it still shrink to fit a small tile, but never grow
// past what it actually has. (SVG crests report their intrinsic viewBox size
// here, which is already ≥ the tile, so they're unaffected and still fill it.)
const homeLogoSize = ref<{ w: number; h: number } | null>(null)
const awayLogoSize = ref<{ w: number; h: number } | null>(null)
watch(current, () => {
  homeIconFailed.value = false
  awayIconFailed.value = false
  homeLogoSize.value = null
  awayLogoSize.value = null
})

function onHomeIconLoad(e: Event) {
  homeIconFailed.value = false
  const img = e.target as HTMLImageElement
  homeLogoSize.value = { w: img.naturalWidth, h: img.naturalHeight }
}
function onHomeIconError() {
  homeIconFailed.value = true
  homeLogoSize.value = null
}
function onAwayIconLoad(e: Event) {
  awayIconFailed.value = false
  const img = e.target as HTMLImageElement
  awayLogoSize.value = { w: img.naturalWidth, h: img.naturalHeight }
}
function onAwayIconError() {
  awayIconFailed.value = true
  awayLogoSize.value = null
}

function logoStyle(icon: string | null | undefined, size: { w: number; h: number } | null) {
  if (!icon) return {}
  const backgroundSize = size && size.w > 0 ? `min(${size.w}px, 100%) auto` : 'contain'
  return { backgroundImage: `url(${icon})`, backgroundSize }
}
const homeLogoStyle = computed(() => logoStyle(current.value?.homeIcon, homeLogoSize.value))
const awayLogoStyle = computed(() => logoStyle(current.value?.awayIcon, awayLogoSize.value))

// Fixed rather than derived from the club's synthesised colour (clubIdentity
// has no real per-team colour data — it's a hash-based guess) — a crest sits
// on the same flat navy regardless of which two clubs are shown, instead of
// the disc's colour swinging with whatever the hash happened to pick.
const CIRCLE_BG = '#151f31'

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
.fxn-wrap {
  max-width: 26rem;
  margin: 0 auto;
}

.fxn-panel {
  min-height: 340px;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 22px 24px 26px;
}

.fxn-header {
  margin-bottom: 8px;
}

.fxn-league {
  font-size: 14px;
  font-weight: 700;
  color: var(--ms-text);
  min-width: 0;
}

.fxn-when-pill {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 700;
  color: var(--ms-blue);
  background: rgba(142, 205, 242, 0.12);
  border: 1px solid rgba(142, 205, 242, 0.35);
}

.fxn-crests {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Scales with the card so the two tiles can't outgrow a narrow phone. */
  --fxn-crest: clamp(96px, 26vw, 132px);
  --fxn-overlap: calc(var(--fxn-crest) * -0.26);
  margin: 22px 0 8px;
}

.fxn-crests-solo {
  --fxn-overlap: 0px;
}

.fxn-crest {
  position: relative;
  width: var(--fxn-crest);
  height: var(--fxn-crest);
  border-radius: 26px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Fixed rather than derived from either club's colour — see CIRCLE_BG in
     the script for why. */
  background: v-bind(CIRCLE_BG);
  box-shadow: 0 20px 40px -18px rgba(0, 0, 0, 0.55);
}

/* Away sits in front of home where they overlap. */
.fxn-crest-home {
  z-index: 1;
}

.fxn-crest-away {
  margin-left: var(--fxn-overlap);
  z-index: 2;
}

.fxn-logo {
  position: absolute;
  inset: 18%;
  /* background-size is set inline per-icon (see logoStyle in the script) —
     capped at the source's natural resolution so small raster crests aren't
     upscaled past their real size and don't come out blurry. */
  background-position: center;
  background-repeat: no-repeat;
}

.fxn-logo-probe {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.fxn-mono {
  /* Tracks the tile rather than a fixed size, so it stays proportionate at
     every breakpoint now that --fxn-crest is fluid. */
  font-size: calc(var(--fxn-crest) * 0.2);
  font-weight: 900;
  letter-spacing: 0.5px;
  /* Fixed light colour rather than clubIdentity's "ink" — ink is tuned for
     legibility against that club's own bright synthesised colour, which the
     tile no longer uses as its background. */
  color: var(--ms-text);
}

.fxn-dots {
  position: absolute;
  top: 50%;
  right: -2px;
  transform: translateY(-50%);
  gap: 6px;
  z-index: 3;
}

.fxn-dot {
  width: 6px;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.25);
  cursor: pointer;
  transition: height 0.3s ease, background-color 0.3s ease;
}

.fxn-dot.active {
  height: 18px;
  background: #8ecdf2;
}

.fxn-vs {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: rgba(244, 247, 251, 0.4);
  margin-bottom: 10px;
}

.fxn-title {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 1.2;
  margin-bottom: 8px;
}

.fxn-venue {
  font-size: 14px;
  font-weight: 600;
  color: rgba(244, 247, 251, 0.7);
  margin-bottom: 4px;
}

.fxn-count-line {
  font-size: 13px;
  font-weight: 600;
  color: rgba(244, 247, 251, 0.5);
}

.fxn-empty {
  min-height: 340px;
}

.fx-crest {
  width: 64px;
  height: 64px;
  border-radius: 20px;
}

.fxn-actions {
  margin-top: 16px;
}

.fxn-actions .ms-btn-primary {
  flex: 1 1 auto;
  min-width: 0;
}

.fxn-actions .ms-btn-secondary {
  flex: none;
}

@media (prefers-reduced-motion: reduce) {
  .fxn-dot {
    transition: none;
  }
}

</style>
