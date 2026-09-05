<template>
  <Navbar @get-started="openSport" />
  <main>
    <Hero
      @get-started="openSport"
      @pick-sport="openWithSport"
      @pick-team="openWithTeam"
    />
    <WeekMatches />
    <SportsGrid @pick-sport="openWithSport" />
    <HowItWorks @get-started="openSport" />
    <Features />
  </main>
  <Footer />
  <TeamSelectorModal
    v-if="showModal"
    :initial-sport="initialSport"
    :initial-team="initialTeam"
    @close="closeModal"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Team } from '@/types'
import Navbar from '@/components/Navbar.vue'
import Hero from '@/components/Hero.vue'
import HowItWorks from '@/components/HowItWorks.vue'
import SportsGrid from '@/components/SportsGrid.vue'
import WeekMatches from '@/components/WeekMatches.vue'
import Features from '@/components/Features.vue'
import Footer from '@/components/Footer.vue'
import TeamSelectorModal from '@/components/TeamSelectorModal.vue'

const route = useRoute()
const router = useRouter()

const showModal = ref(false)
const initialSport = ref<string | null>(null)
const initialTeam = ref<Team | null>(null)

// Reopen the wizard if the URL still carries its state (page reload while open).
onMounted(() => {
  if (route.query.wstep || route.query.wsport || route.query.wteam) {
    showModal.value = true
  }
})

function clearWizardQuery() {
  const query = { ...route.query }
  delete query.wstep
  delete query.wsport
  delete query.wteam
  router.replace({ query })
}

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
  clearWizardQuery()
}
</script>
