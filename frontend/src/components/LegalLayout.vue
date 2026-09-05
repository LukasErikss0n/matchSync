<template>
  <Navbar @get-started="showModal = true" />

  <main class="min-h-screen px-4 sm:px-6 py-14 sm:py-16">
    <div class="max-w-3xl mx-auto fade-up">
      <p class="section-label mb-2">Legal</p>
      <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2" style="letter-spacing: -0.02em">
        {{ title }}
      </h1>
      <p class="text-sm mb-10" style="color: var(--ms-muted-dim)">Last updated {{ updated }}</p>

      <div class="legal-content flex flex-col gap-8">
        <slot />
      </div>

      <RouterLink
        to="/"
        class="ms-btn-secondary inline-flex items-center gap-2 rounded-2xl px-5 py-3 font-bold text-sm mt-12"
      >
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
  title: string
  updated: string
}>()

const showModal = ref(false)
</script>

<style scoped src="./LegalLayout.css"></style>
