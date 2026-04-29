<template>
  <nav class="ms-nav sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <img src="/matchSync_bg.png" alt="MatchSync" class="h-8 w-8 rounded-lg object-cover" />
        <span class="font-bold text-lg tracking-tight text-slate-900">
          Match<span class="ms-text-accent">Sync</span>
        </span>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="btn btn-sm ms-btn-primary rounded-full px-5 text-sm hidden sm:flex"
          @click="emit('getStarted')"
        >
          Get your calendar
        </button>
        <button
          class="md:hidden flex flex-col gap-1.5 p-2 rounded-lg hover:bg-slate-100 transition-colors"
          aria-label="Menu"
          @click="menuOpen = !menuOpen"
        >
          <span
            class="block w-5 h-0.5 bg-slate-700 transition-all duration-200"
            :class="{ 'rotate-45 translate-y-2': menuOpen }"
          />
          <span
            class="block w-5 h-0.5 bg-slate-700 transition-all duration-200"
            :class="{ 'opacity-0': menuOpen }"
          />
          <span
            class="block w-5 h-0.5 bg-slate-700 transition-all duration-200"
            :class="{ '-rotate-45 -translate-y-2': menuOpen }"
          />
        </button>
      </div>
    </div>
    <div
      v-if="menuOpen"
      class="md:hidden absolute top-full left-0 right-0 bg-white border-t border-slate-100 shadow-lg py-3 px-6 flex flex-col gap-1"
    >
      <button
        class="btn ms-btn-primary rounded-full mt-2 font-semibold text-sm"
        @click="onMobileCta"
      >
        Get your calendar
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ getStarted: [] }>()

const menuOpen = ref(false)

function onMobileCta() {
  menuOpen.value = false
  emit('getStarted')
}
</script>
