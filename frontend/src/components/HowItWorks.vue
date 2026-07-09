<template>
  <section id="how-it-works" class="py-24 px-6">
    <div class="max-w-5xl mx-auto">
      <div class="text-center mb-16">
        <div class="section-label mb-3">How it works</div>
        <h2 class="text-3xl sm:text-[34px] font-extrabold" style="letter-spacing: -0.02em">
          Three steps. No app needed.
        </h2>
      </div>
      <div class="grid md:grid-cols-3 gap-4.5">
        <FeatureCard
          v-for="s in steps"
          :key="s.n"
          :icon="s.icon"
          :title="s.title"
          :desc="s.desc"
          :step="s.n"
        />
      </div>
      <div class="text-center mt-12">
        <button
          class="ms-btn-primary rounded-2xl px-10 py-3.5 text-[15px] font-bold"
          @click="emit('getStarted')"
        >
          Pick your team
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { IconName } from '@/types'
import FeatureCard from './FeatureCard.vue'

const emit = defineEmits<{ getStarted: [] }>()

const steps: { n: string; title: string; desc: string; icon: IconName }[] = [
  {
    n: '1',
    title: 'Pick your team',
    desc: 'Choose your sport, league, and favourite team from our database of 3+ leagues worldwide.',
    icon: 'search',
  },
  {
    n: '2',
    title: 'Get your calendar link',
    desc: 'We generate a unique webcal:// link just for your team. One link, one subscription.',
    icon: 'link',
  },
  {
    n: '3',
    title: 'Subscribe once',
    desc: 'Tap "Add to Apple Calendar" or "Add to Google Calendar". Every match syncs automatically — for the whole season.',
    icon: 'calendar',
  },
]
</script>
