<template>
  <footer class="border-t border-slate-100 bg-white">
    <div class="max-w-6xl mx-auto px-6 py-12">
      <div class="grid md:grid-cols-3 gap-10 pb-10 border-b border-slate-100">
        <div>
          <div class="flex items-center gap-2 mb-3">
            <img src="/matchSync_bg.png" alt="MatchSync" class="h-7 w-7 rounded-lg object-cover" loading="lazy" decoding="async" />
            <span class="font-bold text-slate-800">
              Match<span class="ms-text-accent">Sync</span>
            </span>
          </div>
          <p class="text-sm text-slate-500 leading-relaxed">
            Live, always-updated sports calendars for football, hockey, basketball and more.
            Subscribe once, stay current forever.
          </p>
        </div>
        <div class="flex flex-col gap-2">
          <div class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">Product</div>
          <a
            v-for="l in productLinks"
            :key="l"
            href="#"
            class="text-sm text-slate-500 hover:text-slate-800 transition-colors"
          >
            {{ l }}
          </a>
        </div>
        <div class="flex flex-col gap-2">
          <div class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">Company</div>
          <a
            v-for="l in companyLinks"
            :key="l"
            href="#"
            class="text-sm text-slate-500 hover:text-slate-800 transition-colors"
          >
            {{ l }}
          </a>
          <a
            href="mailto:hello@matchsync.io"
            class="text-sm hover:opacity-80 transition-opacity ms-text-accent"
          >
            hello@matchsync.io
          </a>
        </div>
      </div>
      <div class="flex flex-col sm:flex-row items-center justify-between gap-2 pt-6">
        <p class="text-xs text-slate-400">© 2026 MatchSync. All rights reserved.</p>
        <p class="text-xs text-slate-400">Built for fans, by fans.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const productLinks = ['How it works', 'Supported sports', 'API docs']
const companyLinks = ['Privacy policy', 'Terms of service']
</script>
