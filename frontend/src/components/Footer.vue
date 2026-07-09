<template>
  <footer class="border-t border-white/10 bg-black/25">
    <div class="max-w-6xl mx-auto px-6 py-12">
      <div class="grid md:grid-cols-3 gap-10 pb-10 border-b border-white/10">
        <div>
          <div class="flex items-center gap-2.5 mb-3">
            <div
              class="w-[30px] h-[30px] rounded-[9px] flex items-center justify-center"
              style="background: linear-gradient(160deg, var(--ms-blue), var(--ms-blue-dark))"
            >
              <img src="/matchSync_bg.png" alt="MatchSync" class="w-full h-full rounded-[9px] object-cover" loading="lazy" decoding="async" />
            </div>
            <span class="font-extrabold text-[15px]">
              Match<span class="ms-text-accent">Sync</span>
            </span>
          </div>
          <p class="text-[13.5px] leading-relaxed max-w-[320px]" style="color: var(--ms-muted)">
            Live, always-updated sports calendars for football, hockey, basketball and more.
            Subscribe once, stay current forever.
          </p>
        </div>
        <div class="flex flex-col gap-2.5">
          <div class="text-[11px] font-bold uppercase tracking-widest mb-1" style="color: var(--ms-muted-dim)">Product</div>
          <a
            v-for="l in productLinks"
            :key="l"
            href="#"
            class="text-[13.5px] font-semibold transition-colors"
            style="color: rgba(244,247,251,.65)"
          >
            {{ l }}
          </a>
        </div>
        <div class="flex flex-col gap-2.5">
          <div class="text-[11px] font-bold uppercase tracking-widest mb-1" style="color: var(--ms-muted-dim)">Company</div>
          <a
            v-for="l in companyLinks"
            :key="l"
            href="#"
            class="text-[13.5px] font-semibold transition-colors"
            style="color: rgba(244,247,251,.65)"
          >
            {{ l }}
          </a>
          <a
            href="mailto:hello@matchsync.io"
            class="text-[13.5px] font-semibold hover:opacity-80 transition-opacity ms-text-accent"
          >
            hello@matchsync.io
          </a>
        </div>
      </div>
      <div class="flex flex-col sm:flex-row items-center justify-between gap-2 pt-5">
        <p class="text-xs" style="color: var(--ms-muted-dim)">© 2026 MatchSync. All rights reserved.</p>
        <p class="text-xs" style="color: var(--ms-muted-dim)">Built for fans, by fans.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const productLinks = ['How it works', 'Supported sports', 'API docs']
const companyLinks = ['Privacy policy', 'Terms of service']
</script>
