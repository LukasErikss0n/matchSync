<template>
  <Navbar @get-started="openModal" />
  <Hero @get-started="openModal" />
  <HowItWorks @get-started="openModal" />
  <SportsGrid @get-started="openModal" />
  <Features />
  <Footer />
  <TeamSelectorModal v-if="showModal" @close="showModal = false" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Navbar from '@/components/Navbar.vue'
import Hero from '@/components/Hero.vue'
import HowItWorks from '@/components/HowItWorks.vue'
import SportsGrid from '@/components/SportsGrid.vue'
import Features from '@/components/Features.vue'
import Footer from '@/components/Footer.vue'
import TeamSelectorModal from '@/components/TeamSelectorModal.vue'

const showModal = ref(false)

function openModal() {
  showModal.value = true
}
</script>
