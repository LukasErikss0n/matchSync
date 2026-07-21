<template>
  <footer class="border-t border-white/10 bg-black/25">
    <div class="max-w-6xl mx-auto px-6 py-12">
      <div class="grid md:grid-cols-12 gap-10 pb-10 border-b border-white/10">
        <div class="md:col-span-3">
          <div class="flex items-center gap-2.5 mb-3">
            <div
              class="w-[30px] h-[30px] rounded-[9px] flex items-center justify-center"
              style="background: rgb(19, 28, 46); border: 1px solid rgba(142, 205, 242, 0.35)"
            >
              <img src="/logo.svg" alt="MatchCalender" class="w-full h-full object-contain" loading="lazy" decoding="async" />
            </div>
            <span class="font-extrabold text-[15px]">
              Match<span class="ms-text-accent">Calender</span>
            </span>
          </div>
          <p class="text-[13.5px] leading-relaxed max-w-[320px]" style="color: var(--ms-muted)">
            Live, always-updated sports calendars for football, hockey, basketball and more.
            Subscribe once, stay current forever.
          </p>
        </div>
        <div class="md:col-span-2 flex flex-col gap-2.5">
          <div class="text-[11px] font-bold uppercase tracking-widest mb-1" style="color: var(--ms-muted-dim)">Product</div>
          <RouterLink
            v-for="l in productLinks"
            :key="l.label"
            :to="l.to"
            class="text-[13.5px] font-semibold transition-colors"
            style="color: rgba(244,247,251,.65)"
          >
            {{ l.label }}
          </RouterLink>
        </div>
        <div class="md:col-span-5">
          <div class="text-[11px] font-bold uppercase tracking-widest mb-3.5" style="color: var(--ms-muted-dim)">Leagues</div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-2.5">
            <RouterLink
              v-for="l in leagueLinks"
              :key="l.to"
              :to="l.to"
              class="text-[13px] font-semibold leading-snug transition-colors"
              style="color: rgba(244,247,251,.65)"
            >
              {{ l.label }} calendar
            </RouterLink>
          </div>
        </div>
        <div class="md:col-span-2 flex flex-col gap-2.5">
          <div class="text-[11px] font-bold uppercase tracking-widest mb-1" style="color: var(--ms-muted-dim)">Company</div>
          <RouterLink
            v-for="l in companyLinks"
            :key="l.label"
            :to="l.to"
            class="text-[13.5px] font-semibold transition-colors"
            style="color: rgba(244,247,251,.65)"
          >
            {{ l.label }}
          </RouterLink>
          <a
            href="mailto:info@matchcalender.io"
            class="text-[13.5px] font-semibold hover:opacity-80 transition-opacity ms-text-accent"
          >
            info@matchcalender.io
          </a>
        </div>
      </div>
      <div class="flex flex-col sm:flex-row items-center justify-between gap-2 pt-5">
        <p class="text-xs" style="color: var(--ms-muted-dim)">© 2026 MatchCalender. All rights reserved.</p>
        <p class="text-xs" style="color: var(--ms-muted-dim)">Built for fans, by fans.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import leaguePages from '@/data/leaguePages.json'

const productLinks = [
  { label: 'How it works', to: '/#how-it-works' },
  { label: 'Supported sports', to: '/#sports' },
  { label: 'API docs', to: '/api-docs' },
]
// Every league landing page, linked so crawlers reach them through the site
// (not only via sitemap.xml).
const leagueLinks = leaguePages.map((p) => ({ label: p.name, to: p.path }))
const companyLinks = [
  { label: 'Privacy policy', to: '/privacy' },
  { label: 'Terms of service', to: '/terms' },
]
</script>
