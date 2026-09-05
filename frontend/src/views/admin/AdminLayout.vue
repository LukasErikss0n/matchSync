<template>
  <div class="admin-shell">
    <template v-if="data">
      <aside class="admin-sidebar">
        <RouterLink to="/" class="admin-brand">
          <div class="admin-brand-mark">
            <img src="/logo.svg" alt="MatchCalender" />
          </div>
          <div class="admin-brand-name">Match<b>Calender</b></div>
        </RouterLink>

        <div class="admin-nav-section">Overview</div>
        <nav class="admin-nav">
          <RouterLink to="/admin">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12l9-9 9 9"/><path d="M5 10v10h14V10"/></svg>
            Analytics
          </RouterLink>
          <RouterLink to="/admin/leagues">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 010 18"/><path d="M12 3a14 14 0 000 18"/></svg>
            Leagues
          </RouterLink>
        </nav>

        <div class="admin-nav-section">Operations</div>
        <nav class="admin-nav">
          <RouterLink to="/admin/teams">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.9"/><path d="M16 3.1a4 4 0 010 7.8"/></svg>
            Teams
          </RouterLink>
        </nav>

        <div class="admin-sidebar-foot">
          <button class="admin-btn admin-btn-ghost admin-btn-sm" @click="signOut">Sign out</button>
        </div>
      </aside>

      <main class="admin-main">
        <RouterView v-if="data" :data="data" :error="error" :loading="loading" @refresh="load" />
      </main>
    </template>

    <div v-else class="admin-gate">
      <form class="admin-gate-card" @submit.prevent="load()">
        <label for="admin-token">Admin token</label>
        <input
          id="admin-token"
          v-model="token"
          type="password"
          autocomplete="current-password"
          placeholder="ADMIN_TOKEN"
        />
        <p v-if="error" class="admin-gate-error">{{ error }}</p>
        <button type="submit" class="admin-btn admin-btn-primary" :disabled="!token.trim() || loading">
          {{ loading ? 'Checking…' : 'Show dashboard' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { SubscriptionDashboard } from '@/types'
import { fetchSubscriptionDashboard } from '@/services/sports'

const STORAGE_KEY = 'ms-admin-token'

const token = ref('')
const data = ref<SubscriptionDashboard | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  const value = token.value.trim()
  if (!value) return
  loading.value = true
  error.value = null
  try {
    data.value = await fetchSubscriptionDashboard(value)
    localStorage.setItem(STORAGE_KEY, value)
  } catch (e) {
    localStorage.removeItem(STORAGE_KEY)
    data.value = null
    error.value = e instanceof Error ? e.message : 'Could not load dashboard'
  } finally {
    loading.value = false
  }
}

function signOut() {
  localStorage.removeItem(STORAGE_KEY)
  token.value = ''
  data.value = null
  error.value = null
}

onMounted(() => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    token.value = saved
    load()
  }
})
</script>

<style src="./admin.css"></style>
