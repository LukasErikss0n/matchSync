<template>
  <div class="relative flex items-center gap-2 px-7 py-4">
    <template v-for="(label, i) in labels" :key="label">
      <div class="flex items-center gap-1.5">
        <span
          class="step-indicator w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold relative"
          :class="i + 1 < currentStep ? 'done' : i + 1 === currentStep ? 'active' : 'idle'"
        >
          <Transition name="step-check">
            <span :key="i + 1 < currentStep ? 'check' : 'num'" class="step-check-inner">{{ i + 1 < currentStep ? '✓' : i + 1 }}</span>
          </Transition>
        </span>
        <span class="step-label text-xs font-medium" :class="{ 'is-current': i + 1 === currentStep }">
          {{ label }}
        </span>
      </div>
      <div v-if="i < labels.length - 1" class="step-track flex-1 h-px relative">
        <div class="step-track-fill absolute inset-0" :class="{ 'is-filled': i + 1 < currentStep }" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  currentStep: number
  labels: string[]
}>()
</script>

<style scoped src="./StepIndicator.css"></style>
