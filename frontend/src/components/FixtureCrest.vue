<template>
  <div
    class="fx-crest flex items-center justify-center overflow-hidden"
    :style="showIcon
      ? { background: 'rgba(255,255,255,.94)', border: '1px solid rgba(255,255,255,.2)', boxShadow: SHADOW }
      : { background: club.color, border: '1px solid rgba(255,255,255,.2)', boxShadow: SHADOW }"
  >
    <div
      v-if="showIcon"
      class="fx-crest-bg"
      :style="{ backgroundImage: `url(${icon})` }"
      role="img"
      :aria-label="club.monogram"
    ></div>
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
watch(() => props.icon, () => (failed.value = false))

const showIcon = computed(() => !!props.icon && !failed.value)
</script>

<style scoped src="./FixtureCrest.css"></style>
