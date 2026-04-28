<template>
  <span class="w-5 h-5 inline-block" v-html="paths[name]" />
</template>

<script setup lang="ts">
import type { IconName } from '@/types'

defineProps<{ name: IconName }>()

const svg = (inner: string) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-full h-full">${inner}</svg>`

const paths: Record<IconName, string> = {
  football: svg('<circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 00-6.88 2.77L12 12l7.07-4.08A10 10 0 0012 2z"/><path d="M2.05 13A10 10 0 0012 22a10 10 0 007.95-3.95L12 12z"/><circle cx="12" cy="12" r="2"/>'),
  hockey: svg('<path d="M5 20h14"/><path d="M5 20c0-4 2-7 7-10"/><path d="M19 20c0-4-2-7-7-10"/><ellipse cx="12" cy="10" rx="3" ry="1.5"/><line x1="8" y1="4" x2="16" y2="4"/><line x1="12" y1="4" x2="12" y2="8"/>'),
  basketball: svg('<circle cx="12" cy="12" r="10"/><path d="M4.93 4.93a10 10 0 0014.14 14.14"/><path d="M19.07 4.93A10 10 0 004.93 19.07"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/>'),
  baseball: svg('<circle cx="12" cy="12" r="10"/><path d="M4.93 4.93c1.5 2.5 2.07 5.07 1.57 7.57"/><path d="M19.07 4.93c-1.5 2.5-2.07 5.07-1.57 7.57"/><path d="M4.93 19.07c1.5-2.5 2.07-5.07 1.57-7.57"/><path d="M19.07 19.07c-1.5-2.5-2.07-5.07-1.57-7.57"/>'),
  amfootball: svg('<ellipse cx="12" cy="12" rx="9" ry="6"/><path d="M3 12h18"/><path d="M12 6v12"/><path d="M8.5 8.5l7 7"/><path d="M15.5 8.5l-7 7"/>'),
  rugby: svg('<ellipse cx="12" cy="12" rx="8" ry="5" transform="rotate(45 12 12)"/><line x1="12" y1="4.34" x2="12" y2="19.66"/><line x1="4.34" y1="12" x2="19.66" y2="12"/>'),
  refresh: svg('<path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>'),
  trophy: svg('<path d="M6 9H4.5a2.5 2.5 0 010-5H6"/><path d="M18 9h1.5a2.5 2.5 0 000-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0012 0V2z"/>'),
  devices: svg('<rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><path d="M12 18h.01"/>'),
  globe: svg('<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>'),
  bell: svg('<path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>'),
  zap: svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'),
  link: svg('<path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>'),
  calendar: svg('<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>'),
  search: svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'),
}
</script>
