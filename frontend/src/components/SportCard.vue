<template>
  <button
    type="button"
    class="sport-card w-36 rounded-2xl border-2 border-slate-200 bg-white p-4 flex flex-col items-center gap-2 cursor-pointer transition-all"
    :class="{ selected }"
    @click="emit('click')"
  >
    <div class="w-8 h-8 feature-icon rounded-lg flex items-center justify-center">
      <Icon :name="sport.icon" />
    </div>
    <span class="text-sm font-semibold text-slate-700">{{ sport.label }}</span>
    <span v-if="showLeagues" class="text-xs text-slate-400">
      {{ sport.leagues.length }} leagues
    </span>
  </button>
</template>

<script setup lang="ts">
import type { Sport } from '@/types'
import Icon from './Icon.vue'

withDefaults(
  defineProps<{ sport: Sport; selected?: boolean; showLeagues?: boolean }>(),
  { selected: false, showLeagues: false }
)

const emit = defineEmits<{ click: [] }>()
</script>
