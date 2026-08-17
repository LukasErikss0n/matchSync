<template>
  <section id="sports" class="py-20 sm:py-24 px-6">
    <div class="max-w-5xl mx-auto">
      <div class="text-center mb-14">
        <div class="section-label mb-3">Sports</div>
        <h2 class="text-3xl sm:text-[34px] font-extrabold" style="letter-spacing: -0.02em">
          Your sport? We've got it.
        </h2>
      </div>
      <div class="grid grid-cols-2 sm:flex sm:flex-wrap sm:justify-center gap-3 sm:gap-4 max-w-md sm:max-w-none mx-auto">
        <div v-for="s in sports" :key="s.id" class="sm:w-40">
          <SportCard :sport="s" show-leagues @click="emit('pickSport', s.id)" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Sport } from '@/types'
import { fetchSports } from '@/services/sports'
import SportCard from './SportCard.vue'

const emit = defineEmits<{ pickSport: [id: string] }>()

const sports = ref<Sport[]>([])

onMounted(async () => {
  sports.value = await fetchSports()
})
</script>
