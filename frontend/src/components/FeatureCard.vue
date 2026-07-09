<template>
  <div class="glass-card rounded-[24px] p-6 relative overflow-hidden transition-colors hover:border-[rgba(142,205,242,.4)]">
    <div
      class="absolute inset-0 pointer-events-none"
      style="background-image: linear-gradient(115deg, rgba(142,205,242,.08) 0 34%, transparent 34%)"
    ></div>
    <div class="relative w-[46px] h-[46px] rounded-[14px] feature-icon flex items-center justify-center mb-4">
      <Icon :name="icon" class="!w-[21px] !h-[21px]" />
    </div>
    <div v-if="step" class="relative text-[11px] font-bold uppercase mb-1.5" style="letter-spacing: 1.5px; color: rgba(244,247,251,.45)">
      Step {{ step }}
    </div>
    <h3 class="relative text-[17px] sm:text-[18px] font-extrabold mb-1.5" style="letter-spacing: -0.2px">{{ title }}</h3>
    <p class="relative text-sm leading-relaxed" style="color: var(--ms-muted)">{{ desc }}</p>
  </div>
</template>

<script setup lang="ts">
import type { IconName } from '@/types'
import Icon from './Icon.vue'

defineProps<{
  icon: IconName
  title: string
  desc: string
  step?: string
}>()
</script>
