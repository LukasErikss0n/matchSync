<template>
  <section class="ms-gradient-hero py-24 px-6">
    <div class="max-w-4xl mx-auto text-center">
      <p class="text-xs font-bold uppercase mb-7 ms-text-accent" style="letter-spacing: 0.15em">
        Always up to date &nbsp;·&nbsp; Reschedules auto-sync
      </p>
      <h1
        class="text-5xl md:text-6xl font-black text-slate-900 leading-tight mb-6"
        style="letter-spacing: -0.03em"
      >
        Your team's schedule, live in your calendar.
      </h1>
      <p class="text-xl text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed">
        Subscribe to a live, always-updated calendar for any football, hockey, basketball team — and
        more. Every match, reschedule, and playoff round syncs automatically.
      </p>
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <button
          class="btn ms-btn-primary rounded-full px-8 py-3 text-base font-semibold shadow-md"
          @click="emit('getStarted')"
        >
          Pick your team — it's free
        </button>
        <a
          href="#how-it-works"
          class="btn btn-outline rounded-full px-8 py-3 text-base font-semibold text-slate-600 hover:bg-slate-50"
          style="border-color: #94a3b8"
        >
          See how it works
        </a>
      </div>
      <div class="flex items-center justify-center gap-8 mt-14">
        <div v-for="[n, l] in stats" :key="n" class="text-center">
          <div class="text-2xl font-black text-slate-900">{{ n }}</div>
          <div class="text-xs text-slate-600 mt-0.5 font-medium">{{ l }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const emit = defineEmits<{ getStarted: [] }>()

const stats: [string, string][] = [
  ['Free', 'Always & forever'],
  ['iCal', 'Universal standard'],
  ['Live', 'Reschedules included'],
]
</script>
