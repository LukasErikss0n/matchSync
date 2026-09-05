<template>
  <Navbar @get-started="showModal = true" />

  <main class="min-h-screen px-4 sm:px-6 py-14 sm:py-16">
    <div class="max-w-3xl mx-auto fade-up">
      <p class="section-label mb-2">{{ page.label }}</p>
      <h1
        class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-3"
        style="letter-spacing: -0.02em"
      >
        {{ page.h1 }}
      </h1>
      <p class="text-[15px] mb-10" style="color: var(--ms-muted); line-height: 1.7">
        {{ page.intro }}
      </p>

      <!-- Anchor list: gives the page an internal link target per question, which
           is also what a "jump to answer" citation in an AI answer points at. -->
      <nav class="glass-card rounded-[17px] px-5 py-4 mb-10">
        <ul class="flex flex-col gap-2">
          <li v-for="s in page.sections" :key="`toc-${s.id}`">
            <a :href="`#${s.id}`" class="guide-toc-link text-[14px] font-semibold">{{ s.q }}</a>
          </li>
        </ul>
      </nav>

      <div class="flex flex-col gap-10">
        <section v-for="s in page.sections" :key="s.id" :id="s.id" class="scroll-mt-24">
          <h2
            class="text-xl sm:text-[22px] font-extrabold tracking-tight mb-3"
            style="letter-spacing: -0.015em"
          >
            {{ s.q }}
          </h2>
          <p v-for="(p, i) in s.a" :key="`${s.id}-p-${i}`" class="guide-body mb-3">{{ p }}</p>
          <ol v-if="s.steps" class="guide-steps flex flex-col gap-2 mt-4">
            <li v-for="(step, i) in s.steps" :key="`${s.id}-step-${i}`">{{ step }}</li>
          </ol>
        </section>
      </div>

      <RouterLink
        to="/"
        class="ms-btn-secondary inline-flex items-center gap-2 rounded-2xl px-5 py-3 font-bold text-sm mt-12"
      >
        <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
        {{ page.lang === 'sv' ? 'Tillbaka till startsidan' : 'Back to home' }}
      </RouterLink>
    </div>
  </main>

  <Footer />
  <TeamSelectorModal v-if="showModal" @close="showModal = false" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import Footer from '@/components/Footer.vue'
import TeamSelectorModal from '@/components/TeamSelectorModal.vue'
import guidePages from '@/data/guidePages.json'

// Same JSON that scripts/prerender.mjs bakes into the static HTML, so the
// crawler-visible copy and the hydrated copy can't drift apart.
const props = defineProps<{ locale: 'en' | 'sv' }>()

const page = computed(() => guidePages[props.locale])

const showModal = ref(false)
</script>

<style scoped>
.guide-body {
  font-size: 15px;
  line-height: 1.75;
  color: var(--ms-muted);
}

.guide-steps {
  counter-reset: guide-step;
  padding-left: 0;
  list-style: none;
}

.guide-steps li {
  counter-increment: guide-step;
  position: relative;
  padding-left: 2.25rem;
  font-size: 15px;
  line-height: 1.7;
  color: var(--ms-muted);
}

.guide-steps li::before {
  content: counter(guide-step);
  position: absolute;
  left: 0;
  top: 1px;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  color: var(--ms-blue);
  background: rgba(142, 205, 242, 0.12);
  border: 1px solid rgba(142, 205, 242, 0.28);
}

.guide-toc-link {
  color: var(--ms-blue);
  text-decoration: none;
}

.guide-toc-link:hover {
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
