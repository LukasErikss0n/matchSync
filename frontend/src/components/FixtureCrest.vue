<template>
  <!-- A club's real crest on a light shield. Club badges are almost universally
       drawn to sit on white, so the tile stays light regardless of the club —
       only the no-icon fallback uses the synthesised club colour. -->
  <div
    class="fx-crest flex items-center justify-center overflow-hidden"
    :style="showIcon
      ? { background: 'rgba(255,255,255,.94)', border: '1px solid rgba(255,255,255,.2)', boxShadow: SHADOW }
      : { background: club.color, border: '1px solid rgba(255,255,255,.2)', boxShadow: SHADOW }"
  >
    <!-- Rendered via background-image, not <img>: several PL crests are SVGs
         with no width/height on their root element, only a viewBox. Chromium
         then rasterises an <img> of one of those at a fixed ~116x150 default
         box and stretches that bitmap to fit — visibly blurry at this tile's
         size. background-size:contain rasterises at the real display size
         instead, so it stays crisp at any tile size. -->
    <div
      v-if="showIcon"
      class="fx-crest-bg"
      :style="{ backgroundImage: `url(${icon})` }"
      role="img"
      :aria-label="club.monogram"
    ></div>
    <!-- Invisible — exists purely to get a real load/error event, since a
         CSS background-image has no equivalent of <img>'s @error. -->
    <img
      v-if="icon"
      :src="icon"
      alt=""
      aria-hidden="true"
      class="fx-crest-probe"
      decoding="async"
      @error="failed = true"
      @load="failed = false"
    />
    <span v-if="!showIcon" class="fx-monogram" :style="{ color: club.ink }">{{ club.monogram }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ClubIdentity } from '@/utils/clubIdentity'

const props = defineProps<{ club: ClubIdentity; icon?: string | null }>()

const SHADOW = '0 20px 34px -14px rgba(0,0,0,.6)'

const failed = ref(false)
// The panel rotates through fixtures, so this instance gets reused for a
// different club — a previous load error must not stick.
watch(() => props.icon, () => (failed.value = false))

const showIcon = computed(() => !!props.icon && !failed.value)
</script>

<style scoped>
.fx-crest {
  width: var(--fx-crest-w);
  height: var(--fx-crest-h);
  border-radius: var(--fx-crest-radius);
  flex: none;
  position: relative;
}

.fx-crest-bg {
  position: absolute;
  inset: 4%;
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
}

.fx-crest-probe {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.fx-monogram {
  font-size: var(--fx-monogram);
  font-weight: 900;
  letter-spacing: 0.5px;
}
</style>
