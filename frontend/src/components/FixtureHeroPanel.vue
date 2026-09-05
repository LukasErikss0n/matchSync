<template>
  <div class="fxn-wrap">
    <div
      class="fxn-panel relative overflow-hidden"
      @mouseenter="hoverPaused = true"
      @mouseleave="hoverPaused = false"
      @focusin="hoverPaused = true"
      @focusout="hoverPaused = false"
    >
      <div class="absolute inset-0" style="background: rgba(18,26,44,.96)"></div>

      <div
        class="absolute inset-0 pointer-events-none"
        style="background: radial-gradient(120% 90% at 100% 0%, rgba(142,205,242,.06), transparent 60%)"
      ></div>

      <template v-if="loading">
        <div class="fxn-row-top relative z-[1] flex items-center justify-between gap-2">
          <span class="ms-skeleton" style="width: 116px; height: 27px; border-radius: 999px"></span>
          <span class="ms-skeleton" style="width: 62px; height: 14px"></span>
        </div>
        <div class="fxn-matchup relative z-[1]" aria-hidden="true">
          <div class="fxn-team">
            <span class="ms-skeleton fxn-crest" style="border-radius: 18px"></span>
            <span class="ms-skeleton" style="width: 76px; height: 15px; margin-top: 10px"></span>
            <span class="ms-skeleton" style="width: 34px; height: 11px; margin-top: 6px"></span>
          </div>
          <div class="fxn-meta">
            <span class="ms-skeleton" style="width: 84px; height: 30px"></span>
            <span class="ms-skeleton" style="width: 68px; height: 11px; margin-top: 8px"></span>
          </div>
          <div class="fxn-team">
            <span class="ms-skeleton fxn-crest" style="border-radius: 18px"></span>
            <span class="ms-skeleton" style="width: 76px; height: 15px; margin-top: 10px"></span>
            <span class="ms-skeleton" style="width: 34px; height: 11px; margin-top: 6px"></span>
          </div>
        </div>
      </template>

      <template v-else-if="current">
        <div class="fxn-row-top relative z-[1] flex items-center justify-between gap-2">
          <span class="fxn-league-pill truncate">{{ current.league }}</span>
          <span class="fxn-day-label flex-none">{{ dayOnlyLabel }}</span>
        </div>

        <div class="fxn-matchup relative z-[1]" :class="{ 'fxn-matchup-solo': current.isMotorsport }">
          <div class="fxn-team">
            <div class="fxn-crest">
              <div
                v-if="current.homeIcon && !homeIconFailed"
                class="fxn-logo"
                :style="homeLogoStyle"
                role="img"
                :aria-label="current.home.monogram"
              ></div>
              <span v-else class="fxn-mono">{{ current.home.monogram }}</span>
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
            <div class="fxn-team-name">{{ current.homeTeam }}</div>
            <div class="fxn-team-abbr">{{ current.home.monogram }}</div>
          </div>

          <div class="fxn-meta">
            <div class="fxn-time tabular-nums">{{ timeOnlyLabel }}</div>
            <div v-if="venueName" class="fxn-venue truncate">{{ venueName }}</div>
            <div v-if="countdown" class="fxn-count tabular-nums">{{ countdown }} to kickoff</div>
          </div>

          <div v-if="!current.isMotorsport" class="fxn-team">
            <div class="fxn-crest">
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
            <div class="fxn-team-name">{{ current.awayTeam }}</div>
            <div class="fxn-team-abbr">{{ current.away.monogram }}</div>
          </div>

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
      </template>

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

    <div v-if="loading" class="fxn-actions flex flex-nowrap gap-3" aria-hidden="true">
      <span class="ms-skeleton flex-1" style="height: 48px; border-radius: 999px"></span>
      <span class="ms-skeleton flex-none" style="width: 116px; height: 48px; border-radius: 999px"></span>
    </div>

    <div v-else-if="current" class="fxn-actions flex flex-nowrap gap-3">
      <button
        class="ms-btn-primary rounded-full px-6 py-3.5 font-bold text-[15px] flex items-center justify-center gap-2"
        @click="emit('getStarted')"
      >
        <Icon name="calendar" class="!w-[18px] !h-[18px]" />
        Choose your team
      </button>
      <RouterLink
        :to="seeAllRoute"
        class="ms-btn-secondary rounded-full px-6 py-3.5 font-bold text-[15px] text-center"
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

const props = defineProps<{ matches: Match[]; loading?: boolean }>()
const emit = defineEmits<{ getStarted: [] }>()

const ROTATE_MS = 10_000
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
    const home = clubIdentity(m.home_team)
    return {
      id: m.id,
      homeTeam: m.home_team,
      awayTeam: m.away_team,
      home,
      away: clubIdentity(m.away_team, { avoid: home.color }),
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

const seeAllRoute = computed(() => {
  const top = fixtures.value[0]
  return top ? { path: '/matches', query: { league: top.league } } : '/matches'
})

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

const timeOnlyLabel = computed(() => {
  const f = current.value
  if (!f) return ''
  return new Date(f.startMs).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
})

const dayOnlyLabel = computed(() => {
  const f = current.value
  return f ? dayLabel(new Date(f.startMs)) : ''
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

const homeIconFailed = ref(false)
const awayIconFailed = ref(false)

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

const MIN_CREDIBLE_CREST_PX = 24

function logoStyle(icon: string | null | undefined, size: { w: number; h: number } | null) {
  if (!icon) return {}

  const isSvg = /\.svg(\?|#|$)/i.test(icon)
  const sizeIsCredible =
    !isSvg &&
    size !== null &&
    size.w >= MIN_CREDIBLE_CREST_PX &&
    size.h >= MIN_CREDIBLE_CREST_PX

  const box = sizeIsCredible
    ? { width: `min(${size!.w}px, 100%)`, height: `min(${size!.h}px, 100%)` }
    : { width: '100%', height: '100%' }
  return { backgroundImage: `url(${icon})`, ...box }
}
const homeLogoStyle = computed(() => logoStyle(current.value?.homeIcon, homeLogoSize.value))
const awayLogoStyle = computed(() => logoStyle(current.value?.awayIcon, awayLogoSize.value))

const hoverPaused = ref(false)

declare global {
  interface Window {
    freeze?: boolean
  }
}

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
  startRotation()
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

watch(
  () => props.matches,
  () => {
    if (index.value >= fixtures.value.length) index.value = 0
    startRotation()
  },
)
</script>

<style scoped src="./FixtureHeroPanel.css"></style>
