<template>
  <Navbar @get-started="showModal = true" />

  <main class="min-h-screen px-4 sm:px-6 py-20 sm:py-28">
    <div class="max-w-lg mx-auto text-center fade-up">
      <p class="section-label mb-2">404</p>
      <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-3" style="letter-spacing: -0.02em">
        This page doesn't exist
      </h1>
      <p class="text-[15px] mb-9" style="color: var(--ms-muted)">
        The link may be out of date, or the address might have a typo. Every league calendar is
        still one click away from the home page.
      </p>
      <div class="flex flex-wrap items-center justify-center gap-3">
        <RouterLink to="/" class="ms-btn-primary rounded-2xl px-5 py-3 font-bold text-sm">
          Back to home
        </RouterLink>
        <RouterLink to="/matches" class="ms-btn-secondary rounded-2xl px-5 py-3 font-bold text-sm">
          Browse all matches
        </RouterLink>
      </div>
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

// The noindex meta and canonical removal are applied by the router's
// afterEach (see applyPageMeta), so this view only renders.
const showModal = ref(false)
</script>
