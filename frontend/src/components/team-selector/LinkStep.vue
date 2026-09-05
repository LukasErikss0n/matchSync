<template>
  <div>
    <button
      class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 mb-4 transition-all"
      style="color: rgba(244,247,251,.6);  border: 1px solid rgba(255,255,255,.16)"
      @click="emit('back')"
    >
      <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
      Back
    </button>
    <div class="text-center mb-7">
      <div
        class="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
        style="background: #131c2e"
      >
        <img
          src="/logo.svg"
          alt="MatchCalender"
          class="w-full h-full object-contain"
        />
      </div>
      <h3 class="text-xl font-extrabold mb-1" style="letter-spacing: -0.3px">Your calendar is ready!</h3>
      <p class="text-sm font-medium" style="color: rgba(244,247,251,.6)">
        <strong style="color: var(--ms-text)">{{ calLink.team }}</strong> , {{ calLink.leagues.map(l => l.name).join(', ') }}.
        Every match syncs automatically.
      </p>
    </div>
    <div class="mb-4">
      <div class="text-[10.5px] font-bold uppercase tracking-widest mb-2" style="color: rgba(244,247,251,.45)">
        Your personal calendar link
      </div>
      <button
        type="button"
        class="link-box rounded-2xl px-4 py-3 break-all mb-2 text-left w-full cursor-pointer"
        title="Click to copy"
        @click="emit('copy')"
      >{{ calLink.url }}</button>
      <div class="flex items-center gap-2">
        <button
          class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 transition-all"
          style="background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.16); color: var(--ms-text)"
          @click="emit('copy')"
        >
          <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4.5" y="4.5" width="9" height="9" rx="1.5"/><path d="M2.5 10V3a1 1 0 0 1 1-1h7"/></svg>
          Copy link
        </button>
        <button
          class="inline-flex items-center gap-1.5 text-xs font-bold rounded-full px-3 py-1.5 transition-all"
          style="background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.16); color: var(--ms-text)"
          @click="emit('toggle-preview')"
        >
          <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M1 8s2.5-4.5 7-4.5S15 8 15 8s-2.5 4.5-7 4.5S1 8 1 8Z"/><circle cx="8" cy="8" r="2"/></svg>
          {{ showPreview ? 'Hide preview' : 'Preview all matches' }}
        </button>
      </div>
    </div>

    <Transition name="preview">
      <div v-if="showPreview" class="rounded-2xl overflow-hidden mb-5" style="background: rgba(0,0,0,.2); border: 1px solid rgba(255,255,255,.12)">
        <div v-if="previewLoading" aria-hidden="true">
          <div
            v-for="n in 4"
            :key="`preview-skeleton-${n}`"
            class="flex items-start gap-3 px-4 py-3 border-b border-white/[0.06] last:border-b-0"
          >
            <span class="ms-skeleton flex-shrink-0" style="width: 44px; height: 12px; margin-top: 2px"></span>
            <div class="flex-1 min-w-0">
              <span class="ms-skeleton block" style="width: 66%; height: 13px"></span>
              <span class="ms-skeleton block" style="width: 38%; height: 11px; margin-top: 6px"></span>
            </div>
          </div>
        </div>
        <div v-else-if="previewMatches.length === 0" class="py-6 text-center text-sm" style="color: rgba(244,247,251,.5)">
          No upcoming matches found.
        </div>
        <div v-else style="max-height: 260px; overflow-y: auto">
          <div
            v-for="m in previewMatches"
            :key="m.id"
            class="flex items-start gap-3 px-4 py-3 border-b border-white/[0.06] last:border-b-0"
          >
            <div class="w-11 flex-shrink-0 pt-px text-xs font-bold" style="color: rgba(244,247,251,.4)">
              {{ formatMatchDate(m.start_time) }}
            </div>
            <div class="flex-1 min-w-0 text-sm font-semibold break-words">
              <template v-if="m.sport === 'motorsport'">
                {{ m.home_team }} <span style="color: rgba(244,247,251,.45)">·</span> {{ m.away_team }}
              </template>
              <template v-else>
                {{ m.home_team }} <span style="color: rgba(244,247,251,.45)">vs</span> {{ m.away_team }}
              </template>
              <div class="text-xs font-bold ms-text-accent mt-0.5">{{ m.league.name }}</div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
      <a
        :href="calLink.url"
        class="ms-btn-primary rounded-2xl flex items-center gap-2 justify-center py-3.5 font-bold text-sm"
      >
        Add to Apple Calendar
      </a>
      <a
        :href="`https://calendar.google.com/calendar/r?cid=${encodeURIComponent(calLink.url)}`"
        target="_blank"
        rel="noreferrer"
        class="ms-btn-secondary rounded-2xl flex items-center gap-2 justify-center py-3.5 font-bold text-sm"
      >
        Add to Google Calendar
      </a>
    </div>
    <div
      class="rounded-2xl p-4 text-sm leading-relaxed"
      style="background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1); color: rgba(244,247,251,.6)"
    >
      <strong style="color: var(--ms-text)">How it stays updated:</strong> Your calendar app checks
      this link automatically. Every reschedule and playoff round appears instantly, nothing
      to do on your end.
    </div>
    <button
      class="mt-4 w-full text-sm font-semibold py-2"
      style="color: rgba(244,247,251,.45)"
      @click="emit('reset')"
    >
      Pick a diffrent team
    </button>
  </div>
</template>

<script setup lang="ts">
import type { CalendarLink, Match } from '@/types'

defineProps<{
  calLink: CalendarLink
  showPreview: boolean
  previewLoading: boolean
  previewMatches: Match[]
}>()

const emit = defineEmits<{
  back: []
  copy: []
  'toggle-preview': []
  reset: []
}>()

function formatMatchDate(iso: string): string {
  return new Date(iso).toLocaleDateString([], { month: 'short', day: 'numeric' })
}
</script>

<style scoped src="./LinkStep.css"></style>
