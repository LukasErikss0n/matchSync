<template>
  <button
    type="button"
    class="sport-card w-full max-w-[180px] mx-auto aspect-square rounded-2xl sm:rounded-[22px] px-2 flex flex-col items-center justify-center gap-1.5 sm:gap-2 cursor-pointer transition-all"
    :class="{ selected }"
    @click="emit('click')"
  >
    <!-- Icon and label are a fixed size at every breakpoint. They used to be
         smaller below `sm`, but the card is square and sized off its column,
         so on a phone it grows while the icon shrinks — the content ended up
         filling ~17% of the card against ~33% on a laptop, which read as
         large and empty. max-w keeps the card from ballooning past the
         160-180px it occupies on desktop. -->
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

// Deterministic pastel pick, matching the design's 3-color rotation
const PALETTE = ['#8ecdf2', '#f2b8c6', '#c9e8d2']
const iconColor = computed(() => {
  let hash = 0
  for (let i = 0; i < props.sport.id.length; i++) hash = (hash * 31 + props.sport.id.charCodeAt(i)) >>> 0
  return PALETTE[hash % PALETTE.length]
})
const iconBgTint = computed(() => `${iconColor.value}24`)
</script>
