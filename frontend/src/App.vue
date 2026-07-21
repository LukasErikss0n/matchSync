<template>
  <!-- Key by path so switching between league landing pages (which share
       MatchesView) remounts and re-selects the locked league. Query-only
       navigation (subscribe wizard, ?filter=) keeps the same instance. -->
  <RouterView :key="route.path" />
</template>

<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'

const route = useRoute()
</script>
