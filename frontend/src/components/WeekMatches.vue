<template>
  <!-- Kept mounted while loading so the section doesn't pop into the page
       once the fetch lands; it collapses to nothing only if the week is
       genuinely empty. -->
  <section v-if="loading || matches.length" class="px-4 sm:px-6 py-10 sm:py-14">
    <div class="max-w-3xl mx-auto">
      <div class="flex items-baseline justify-between mb-4">
        <h2 class="text-xl sm:text-2xl font-extrabold" style="letter-spacing: -0.02em">
          This week
        </h2>
        <button
          v-if="!loading && matches.length > COLLAPSED_COUNT"
          type="button"
          class="text-sm font-bold ms-text-accent hover:opacity-80 transition-opacity"
          @click="expanded = !expanded"
        >
          {{ expanded ? 'Show less' : 'See all' }}
        </button>
      </div>

      <div class="glass-card rounded-[20px] overflow-hidden">
        <template v-if="loading && !matches.length">
          <div
            v-for="n in COLLAPSED_COUNT"
            :key="`week-skeleton-${n}`"
            class="flex items-center gap-3 sm:gap-3.5 px-3.5 sm:px-4 py-3 sm:py-3.5 border-b border-white/[0.07] last:border-b-0"
            aria-hidden="true"
          >
            <span class="ms-skeleton week-crest flex-none" style="border-radius: 12px"></span>
            <div class="min-w-0 flex-1">
              <span class="ms-skeleton block" style="width: 62%; height: 14px"></span>
              <span class="ms-skeleton block" style="width: 40%; height: 12px; margin-top: 6px"></span>
            </div>
            <div class="flex items-center gap-2 sm:gap-2.5 flex-none">
              <span class="ms-skeleton" style="width: 30px; height: 13px"></span>
              <span class="ms-skeleton" style="width: 38px; height: 15px"></span>
            </div>
          </div>
        </template>

        <RouterLink
          v-for="m in visible"
          :key="m.id"
          :to="m.to"
          class="week-row flex items-center gap-3 sm:gap-3.5 px-3.5 sm:px-4 py-3 sm:py-3.5 border-b border-white/[0.07] last:border-b-0 transition-colors"
        >
          <div
            class="week-crest flex-none flex items-center justify-center overflow-hidden rounded-xl"
            :style="{ background: m.crestBg }"
          >
            <img
              v-if="m.icon"
              :src="m.icon"
              :alt="m.club.monogram"
              class="w-full h-full object-contain p-1"
              loading="lazy"
              decoding="async"
              @error="failedIcons.add(m.id)"
            />
            <span v-else class="text-[12px] font-black" :style="{ color: m.club.ink }">
              {{ m.club.monogram }}
            </span>
          </div>

          <div class="min-w-0 flex-1">
            <!-- Wraps rather than truncates: long pairings ("Brentford –
                 Tottenham Hotspur") lose the away side entirely to an
                 ellipsis on a phone, which is the half that matters most. -->
            <div class="font-bold text-[14px] sm:text-[15px] leading-snug break-words">
              {{ m.title }}
            </div>
            <!-- Wraps rather than truncates, same reasoning as the title
                 above: "League · Stadium" routinely doesn't fit one line next
                 to the day badge and time on a phone, and the venue is the
                 whole point of showing it — cutting it off defeats the row. -->
            <div
              class="text-[12px] sm:text-[13px] font-semibold break-words mt-0.5"
              style="color: rgba(244,247,251,.5)"
            >
              {{ m.subtitle }}
            </div>
          </div>

          <div class="flex items-center gap-2 sm:gap-2.5 flex-none">
            <span v-if="m.isLive" class="day-pill live">LIVE</span>
            <span v-else-if="m.isToday" class="day-pill today">{{ m.dayLabel }}</span>
            <span v-else class="text-[12px] sm:text-[13px] font-semibold" style="color: rgba(244,247,251,.5)">
              {{ m.dayLabel }}
            </span>
            <span class="text-[13px] sm:text-[15px] font-extrabold tabular-nums">{{ m.timeLabel }}</span>
          </div>
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import type { Match } from '@/types'
import { fetchWeekMatches } from '@/services/sports'
import { detectRegion } from '@/utils/region'
import { clubIdentity } from '@/utils/clubIdentity'
import { matchState } from '@/utils/matchState'

const COLLAPSED_COUNT = 4

const matches = ref<Match[]>([])
const loading = ref(true)
const expanded = ref(false)
// Reactive so a crest that 404s falls back to the monogram on the spot.
const failedIcons = reactive(new Set<number>())

const rows = computed(() =>
  matches.value.map((m) => {
    const club = clubIdentity(m.home_team, { color: m.home_color })
    const start = new Date(m.start_time)
    const now = Date.now()
    const icon = m.home_icon_cropped ?? m.home_icon ?? null

    return {
      id: m.id,
      club,
      icon: icon && !failedIcons.has(m.id) ? icon : null,
      // A real crest sits on a near-transparent tile so it reads against the
      // dark row; the monogram fallback uses the club's own colour at full
      // strength, as in the design.
      crestBg: icon && !failedIcons.has(m.id) ? 'rgba(82, 82, 82, 0.02)' : club.color,
      // Motorsport rows are "<Grand Prix> / <session>", not two opponents, so
      // an en dash between them would read as a fixture that doesn't exist.
      title:
        m.sport === 'motorsport'
          ? `${m.home_team} · ${m.away_team}`
          : `${m.home_team} – ${m.away_team}`,
      // Venue is "<Stadium>, <City>" — city is dropped here since this row is
      // a single truncating line and the stadium name is the part worth the
      // space (the full string is still used for the calendar feed/JSON-LD).
      subtitle: m.venue ? `${m.league.name} · ${m.venue.split(',')[0].trim()}` : m.league.name,
      dayLabel: start.toLocaleDateString([], { weekday: 'short' }),
      timeLabel: start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
      isToday: start.toDateString() === new Date().toDateString(),
      isLive: matchState(m, now) === 'live',
      to: { path: '/matches', query: { league: m.league.slug } },
    }
  }),
)

const visible = computed(() =>
  expanded.value ? rows.value : rows.value.slice(0, COLLAPSED_COUNT),
)

onMounted(async () => {
  try {
    matches.value = await fetchWeekMatches(detectRegion())
  } catch {
    matches.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.week-crest {
  width: 40px;
  height: 40px;
}

@media (min-width: 640px) {
  .week-crest {
    width: 44px;
    height: 44px;
  }
}

.week-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.day-pill {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 3px 7px;
  border-radius: 7px;
}

.day-pill.today {
  color: var(--ms-green);
  background: rgba(201, 232, 210, 0.13);
  border: 1px solid rgba(201, 232, 210, 0.35);
}

.day-pill.live {
  color: var(--ms-ink);
  background: var(--ms-green);
}
</style>
