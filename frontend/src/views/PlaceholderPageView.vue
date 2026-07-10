<template>
  <Navbar @get-started="openSportModal" />

  <main class="min-h-screen flex items-center justify-center px-4 sm:px-6 py-16">
    <div class="glass-panel rounded-[30px] w-full max-w-xl px-8 py-10 text-center fade-up">
      <p class="section-label mb-2">{{ label }}</p>
      <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4" style="letter-spacing: -0.02em">
        {{ title }}
      </h1>
      <p class="mb-8" style="color: var(--ms-muted)">
        {{ description }}
      </p>
      <RouterLink to="/" class="ms-btn-primary inline-flex items-center gap-2 rounded-2xl px-5 py-3 font-bold text-sm">
        <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
        Back to home
      </RouterLink>
    </div>
  </main>

  <Footer />
  <TeamSelectorModal v-if="showModal" @close="showModal = false" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import Footer from '@/components/Footer.vue'
import TeamSelectorModal from '@/components/TeamSelectorModal.vue'

defineProps<{
  label: string
  title: string
  description: string
}>()

const showModal = ref(false)
function openSportModal() {
  showModal.value = true
}
</script>
