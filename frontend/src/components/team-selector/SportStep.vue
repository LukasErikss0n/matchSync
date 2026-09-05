<template>
  <div>
    <div class="grid grid-cols-2 gap-3 w-fit mx-auto mb-5">
      <template v-if="sportsLoading && sports.length === 0">
        <div v-for="n in 4" :key="`sport-skeleton-${n}`" class="w-26">
          <div class="w-full max-w-[180px] mx-auto aspect-square rounded-2xl sm:rounded-[22px] flex flex-col items-center justify-center gap-1.5 sm:gap-2">
            <span class="ms-skeleton" style="width: 52px; height: 52px; border-radius: 12px"></span>
            <span class="ms-skeleton" style="width: 56px; height: 13px; margin-top: 4px"></span>
          </div>
        </div>
      </template>
      <template v-else>
        <div v-for="s in sports" :key="s.id" class="w-26">
          <SportCard
            :sport="s"
            :selected="selectedSportId === s.id"
            @click="emit('select', s.id)"
          />
        </div>
      </template>
    </div>
    <button
      :disabled="!selectedSportId"
      class="ms-btn-primary rounded-2xl w-full py-3.5 font-bold text-[15px] disabled:opacity-40"
      @click="emit('continue')"
    >
      Continue
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Sport } from '@/types'
import SportCard from '../SportCard.vue'

defineProps<{
  sports: Sport[]
  sportsLoading: boolean
  selectedSportId: string | null
}>()

const emit = defineEmits<{
  select: [id: string]
  continue: []
}>()
</script>
