<template>
  <section id="sports" class="py-24 px-6" style="background: #f8fafc">
    <div class="max-w-5xl mx-auto">
      <div class="text-center mb-14">
        <div class="section-label mb-3">Supported sports</div>
        <h2 class="text-3xl font-black text-slate-900" style="letter-spacing: -0.02em">
          Whatever your sport, we've got it.
        </h2>
      </div>
      <div class="flex flex-wrap justify-center gap-4">
        <SportCard
          v-for="s in sports"
          :key="s.id"
          :sport="s"
          show-leagues
          @click="emit('getStarted')"
        />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Sport } from '@/types'
import { fetchSports } from '@/services/sports'
import SportCard from './SportCard.vue'

const emit = defineEmits<{ getStarted: [] }>()

const sports = ref<Sport[]>([])

onMounted(async () => {
  sports.value = await fetchSports()
})
</script>
