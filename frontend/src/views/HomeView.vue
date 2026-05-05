<template>
  <Navbar @get-started="openSport" />
  <Hero
    @get-started="openSport"
    @pick-sport="openWithSport"
    @pick-team="openWithTeam"
  />
  <HowItWorks @get-started="openSport" />
  <SportsGrid @get-started="openSport" />
  <Features />
  <Footer />
  <TeamSelectorModal
    v-if="showModal"
    :initial-sport="initialSport"
    :initial-team="initialTeam"
    @close="closeModal"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Team } from '@/types'
import Navbar from '@/components/Navbar.vue'
import Hero from '@/components/Hero.vue'
import HowItWorks from '@/components/HowItWorks.vue'
import SportsGrid from '@/components/SportsGrid.vue'
import Features from '@/components/Features.vue'
import Footer from '@/components/Footer.vue'
import TeamSelectorModal from '@/components/TeamSelectorModal.vue'

const showModal = ref(false)
const initialSport = ref<string | null>(null)
const initialTeam = ref<Team | null>(null)

function openSport() {
  initialSport.value = null
  initialTeam.value = null
  showModal.value = true
}

function openWithSport(sportId: string) {
  initialSport.value = sportId
  initialTeam.value = null
  showModal.value = true
}

function openWithTeam(payload: { sport: string; team: Team }) {
  initialSport.value = payload.sport
  initialTeam.value = payload.team
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  initialSport.value = null
  initialTeam.value = null
}
</script>
