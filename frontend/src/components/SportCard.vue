<template>
  <button
    type="button"
    class="sport-card w-full max-w-[180px] mx-auto aspect-square rounded-2xl sm:rounded-[22px] px-2 flex flex-col items-center justify-center gap-1.5 sm:gap-2 cursor-pointer transition-all"
    :class="{ selected }"
    @click="emit('click')"
  >
    <div
      class="w-[52px] h-[52px] rounded-xl flex items-center justify-center mb-1"
      :style="{ background: iconBgTint, border: `1px solid ${iconColor}4d` }"
    >
      <Icon :name="sport.icon" class="!w-6 !h-6" :style="{ color: iconColor }" />
    </div>
    <span class="text-[15px] font-extrabold">{{ sport.label }}</span>
    <span v-if="showLeagues" class="text-xs font-semibold" style="color: rgba(244,247,251,.5)">
      {{ sport.leagues.length }} leagues
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Sport } from '@/types'
import Icon from './Icon.vue'

const props = withDefaults(
  defineProps<{ sport: Sport; selected?: boolean; showLeagues?: boolean }>(),
  { selected: false, showLeagues: false }
)

const emit = defineEmits<{ click: [] }>()

const PALETTE = ['#8ecdf2', '#f2b8c6', '#c9e8d2']
const iconColor = computed(() => {
  if (props.sport.id === 'hockey') return '#8ecdf2'
  let hash = 0
  for (let i = 0; i < props.sport.id.length; i++) hash = (hash * 31 + props.sport.id.charCodeAt(i)) >>> 0
  return PALETTE[hash % PALETTE.length]
})
const iconBgTint = computed(() => `${iconColor.value}24`)
</script>
