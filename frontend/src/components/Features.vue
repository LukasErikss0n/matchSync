<template>
  <section class="py-24 px-6">
    <div class="max-w-5xl mx-auto">
      <div class="text-center mb-16">
        <div class="section-label mb-3">Features</div>
        <h2 class="text-3xl sm:text-[34px] font-extrabold" style="letter-spacing: -0.02em">
          Set it and forget it.
        </h2>
      </div>
      <div class="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
        <FeatureCard
          v-for="f in feats"
          :key="f.title"
          :icon="f.icon"
          :title="f.title"
          :desc="f.desc"
        />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { IconName } from '@/types'
import FeatureCard from './FeatureCard.vue'

const feats: { icon: IconName; title: string; desc: string }[] = [
  {
    icon: 'refresh',
    title: 'Auto-reschedules',
    desc: 'Postponed or moved matches? Your calendar updates automatically — no manual edits, ever.',
  },
  {
    icon: 'trophy',
    title: 'Playoffs & cups',
    desc: 'Qualifying rounds, knockouts, and finals are all included in your single subscription link.',
  },
  {
    icon: 'devices',
    title: 'Works everywhere',
    desc: 'Apple Calendar, Google Calendar, Outlook — any app that supports the open iCal standard.',
  },
  {
    icon: 'globe',
    title: 'Correct timezones',
    desc: 'Kick-off times always show in your local timezone, wherever in the world you are watching.',
  },
  {
    icon: 'bell',
    title: 'Built-in reminders',
    desc: 'Every event includes a 1-hour heads-up reminder so you never miss the opening whistle.',
  },
  {
    icon: 'zap',
    title: 'Instant updates',
    desc: 'We poll for schedule changes throughout the day, keeping your calendar razor-sharp always.',
  },
]
</script>
