<template>
  <div
    class="fxn-panel relative overflow-hidden"
    @mouseenter="hoverPaused = true"
    @mouseleave="hoverPaused = false"
    @focusin="hoverPaused = true"
    @focusout="hoverPaused = false"
  >
    <!-- Fixed surface — deliberately NOT derived from either team's colour
         (that used to be a per-fixture wash), so the card looks the same
         fixture to fixture and only the two crest circles carry club colour. -->
    <div class="absolute inset-0" style="background: rgba(18,26,44,.96)"></div>
    <div
      class="absolute inset-0 pointer-events-none"
      style="background: radial-gradient(120% 90% at 100% 0%, rgba(142,205,242,.06), transparent 60%)"
    ></div>

    <template v-if="current">
      <div class="fxn-left relative z-[1]">
        <div class="fxn-meta flex items-center gap-2.5 flex-wrap">
          <span class="fxn-when">{{ whenLabel }}</span>
          <span class="fxn-eyebrow truncate">{{ eyebrow }}</span>
        </div>

        <h2 class="fxn-title">
          <template v-if="current.isMotorsport">{{ current.homeTeam }}</template>
          <template v-else>{{ current.homeTeam }} vs {{ current.awayTeam }}</template>
        </h2>

        <div v-if="countdown" class="fxn-countdown flex items-baseline gap-2">
          <span class="fxn-count tabular-nums">{{ countdown }}</span>
          <span class="fxn-count-label">TO KICKOFF</span>
        </div>

        <p class="fxn-sub">
          Subscribe once and every kick-off, reschedule and playoff lands in your calendar automatically.
        </p>

        <div class="fxn-actions flex flex-wrap gap-3">
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

      <div class="fxn-right" :class="{ 'fxn-right-solo': current.isMotorsport }">
        <div class="fxn-circle fxn-circle-home">
          <!-- background-image, not <img>: several crests (e.g. Premier
               League's) are SVGs with no width/height on the root element,
               only a viewBox — Chromium rasterises a plain <img> of one of
               those at a small default box and stretches that bitmap up,
               visibly blurry at this circle's size. background-size:contain
               rasterises at the real display size instead. -->
          <div
            v-if="current.homeIcon && !homeIconFailed"
            class="fxn-logo"
            :style="{ backgroundImage: `url(${current.homeIcon})` }"
            role="img"
            :aria-label="current.home.monogram"
          ></div>
          <span v-else class="fxn-mono">{{ current.home.monogram }}</span>
          <!-- Invisible — exists purely to get a real load/error event, since
               a CSS background-image has no equivalent of <img>'s @error. -->
          <img
            v-if="current.homeIcon"
            :src="current.homeIcon"
            alt=""
            aria-hidden="true"
            class="fxn-logo-probe"
            decoding="async"
            @error="homeIconFailed = true"
            @load="homeIconFailed = false"
          />
        </div>
        <div
          v-if="!current.isMotorsport"
          class="fxn-circle fxn-circle-away"
        >
          <div
            v-if="current.awayIcon && !awayIconFailed"
            class="fxn-logo"
            :style="{ backgroundImage: `url(${current.awayIcon})` }"
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
            @error="awayIconFailed = true"
            @load="awayIconFailed = false"
          />
        </div>
      </div>

      <!-- Rotation indicator — kept off to the right (not bottom-center like
           the old design) so it doesn't compete with the CTAs on the left. -->
      <div v-if="fixtures.length > 1" class="fxn-dots relative z-[1] flex flex-col items-center">
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

const eyebrow = computed(() => {
  const f = current.value
  if (!f) return ''
  if (!f.venue) return f.league
  // Venue is "<Stadium>, <City>" — city dropped, same reasoning as
  // WeekMatches.vue: this is a single truncating line.
  const stadium = f.venue.split(',')[0].trim()
  return `${f.league} · ${stadium}`
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

// Crest load failures, reset whenever the rotation moves to a different
// fixture — a previous error must not stick to the next club shown here.
const homeIconFailed = ref(false)
const awayIconFailed = ref(false)
watch(current, () => {
  homeIconFailed.value = false
  awayIconFailed.value = false
})

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
.fxn-panel {
  min-height: 340px;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 32px;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 24px;
}

.fxn-left {
  min-width: 0;
  max-width: 30rem;
}

.fxn-meta {
  margin-bottom: 14px;
}

.fxn-when {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: var(--ms-blue);
  background: rgba(142, 205, 242, 0.12);
  border: 1px solid rgba(142, 205, 242, 0.35);
  flex: none;
}

.fxn-eyebrow {
  font-size: 11.5px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(244, 247, 251, 0.45);
}

.fxn-title {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.15;
  margin-bottom: 10px;
}

.fxn-countdown {
  margin-bottom: 14px;
}

.fxn-count {
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
  color: #fff;
  letter-spacing: -0.01em;
}

.fxn-count-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: rgba(244, 247, 251, 0.5);
}

.fxn-sub {
  font-size: 15px;
  font-weight: 500;
  line-height: 1.5;
  color: rgba(244, 247, 251, 0.8);
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.55);
  margin-bottom: 22px;
  max-width: 30rem;
}

.fxn-right {
  /* Shrinks on narrower desktops so the two circles plus the text column
     can't outgrow the card. */
  --fxn-circle: clamp(150px, 21vw, 220px);
  --fxn-overlap: calc(var(--fxn-circle) * -0.29);
  display: flex;
  align-items: center;
  flex: none;
}

.fxn-right-solo {
  --fxn-overlap: 0px;
}

.fxn-circle {
  position: relative;
  width: var(--fxn-circle);
  height: var(--fxn-circle);
  border-radius: 50%;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Fixed rather than derived from either club's colour — see CIRCLE_BG in
     the script for why. */
  background: v-bind(CIRCLE_BG);
  box-shadow: 0 24px 48px -20px rgba(0, 0, 0, 0.55);
}

/* Home sits in front of away where they overlap — the away circle is the one
   that trails off toward the corner. */
.fxn-circle-home {
  z-index: 2;
}

.fxn-circle-away {
  margin-left: var(--fxn-overlap);
  z-index: 1;
}

.fxn-logo {
  position: absolute;
  inset: 18%;
  background-size: contain;
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
  /* Tracks the circle rather than a fixed size, so it stays proportionate at
     every breakpoint now that --fxn-circle is fluid. */
  font-size: calc(var(--fxn-circle) * 0.2);
  font-weight: 900;
  letter-spacing: 0.5px;
  /* Fixed light colour rather than clubIdentity's "ink" — ink is tuned for
     legibility against that club's own bright synthesised colour, which the
     circle no longer uses as its background. */
  color: var(--ms-text);
}

.fxn-dots {
  position: absolute;
  top: 50%;
  right: 14px;
  transform: translateY(-50%);
  gap: 6px;
  /* Above the circles, which on mobile span the whole card. */
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

.fxn-empty {
  min-height: 340px;
}

.fx-crest {
  width: 64px;
  height: 64px;
  border-radius: 20px;
}

@media (max-width: 900px) {
  .fxn-panel {
    grid-template-columns: 1fr;
    padding: 22px;
    min-height: 0;
  }
  .fxn-left {
    /* Text reads on top of the circles rather than being pushed aside by
       them — there isn't room at this width for both, and padding the text
       clear of them shrinks it to a column too narrow for a long fixture
       name. Full width, above the circles. */
    position: relative;
    z-index: 2;
    max-width: none;
  }
  /* Stays one row rather than wrapping — the default gap plus each button's
     px-6 padding was wide enough to force "Matches" onto its own line below
     "Choose your team". The primary button grows to fill the spare width and
     wraps its own label onto two lines instead; the secondary stays sized to
     its (now short) content. */
  .fxn-actions {
    flex-wrap: nowrap;
    gap: 10px;
  }
  .fxn-actions .ms-btn-primary {
    flex: 1 1 auto;
    min-width: 0;
    padding-left: 18px;
    padding-right: 18px;
  }
  .fxn-actions .ms-btn-secondary {
    flex: none;
    padding-left: 20px;
    padding-right: 20px;
  }
  /* Stacked rather than inline: the two together don't fit on one line here,
     and letting them wrap naturally leaves the league line hanging under a
     badge it's meant to sit beside. */
  .fxn-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  /* Each circle is placed individually here rather than as a flex row, so the
     away one can trail off the top-right corner (clipped by the panel's own
     overflow-hidden + border-radius) while the home one stays fully on-card,
     overlapping it from the lower-left. */
  .fxn-right {
    /* Scales with the viewport so it can't crowd the card on a small phone
       or look undersized on a big one. */
    --fxn-circle: clamp(104px, 34vw, 150px);
    position: absolute;
    inset: 0;
    z-index: 1;
    display: block;
    pointer-events: none;
  }
  .fxn-circle {
    position: absolute;
  }
  .fxn-circle-home {
    top: 58px;
    /* Overlaps the away circle from the lower-left, tracking its size. */
    right: calc(var(--fxn-circle) * 0.62);
  }
  /* Fully inside the card — no negative offsets anywhere. The panel clips to
     its rounded corners, so any bleed cuts a real club crest against a hard
     edge (the layered "trailing off the corner" look only works with the
     monograms the mockups used). */
  .fxn-circle-away {
    top: 14px;
    right: 14px;
    margin-left: 0;
  }
  /* Motorsport has a single circle. It deliberately does NOT take the away
     circle's bleeding corner spot: the bleed only reads as intentional
     layering when a second circle sits in front of it, and on its own a
     clipped disc in the corner just looks like a rendering fault. Fully
     inside the card instead. */
  .fxn-right-solo .fxn-circle-home {
    top: 50px;
    right: 16px;
  }
  .fxn-title {
    font-size: 21px;
  }
  /* Dots keep the desktop's vertical right-edge placement here — nudged in
     slightly since the card's padding is tighter. */
  .fxn-dots {
    right: 8px;
  }
  .fxn-empty {
    min-height: 220px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fxn-dot {
    transition: none;
  }
}
</style>
