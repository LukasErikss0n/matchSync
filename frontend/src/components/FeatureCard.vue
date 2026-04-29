<template>
  <div class="rounded-2xl border border-slate-100 bg-white p-7 shadow-sm hover:shadow-md transition-shadow">
    <div class="w-10 h-10 feature-icon rounded-xl flex items-center justify-center mb-4">
      <Icon :name="icon" />
    </div>
    <div v-if="step" class="text-xs font-bold text-slate-300 mb-2 tracking-widest">
      STEP {{ step }}
    </div>
    <h3 class="text-lg font-bold text-slate-900 mb-1.5">{{ title }}</h3>
    <p class="text-slate-500 text-sm leading-relaxed">{{ desc }}</p>
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
