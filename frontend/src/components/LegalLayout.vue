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

<style scoped>
.legal-content :deep(h2) {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  margin-bottom: 0.75rem;
}

.legal-content :deep(p),
.legal-content :deep(li) {
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--ms-muted);
}

.legal-content :deep(ul) {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-left: 1.25rem;
  list-style: disc;
}

.legal-content :deep(strong) {
  color: var(--ms-text);
  font-weight: 700;
}

.legal-content :deep(a) {
  color: var(--ms-blue);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
}

/* Inline URL fragments (e.g. the &id= parameter in the privacy policy).
   Wraps rather than overflows — these appear mid-sentence on a phone. */
.legal-content :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.9em;
  color: var(--ms-blue);
  background: rgba(142, 205, 242, 0.1);
  border: 1px solid rgba(142, 205, 242, 0.22);
  border-radius: 6px;
  padding: 1px 6px;
  overflow-wrap: anywhere;
}
</style>
