<template>
  <div class="admin-shell">
    <div v-if="booting" class="admin-boot">
      <div class="admin-boot-spinner" aria-hidden="true"></div>
      <p>Restoring session…</p>
    </div>

    <template v-else-if="data">
      <header class="admin-header">
        <RouterLink to="/" class="admin-brand">
          <div class="admin-brand-mark">
            <img src="/logo.svg" alt="MatchCalender" />
          </div>
          <div class="admin-brand-name">Match<b>Calender</b></div>
        </RouterLink>

        <div class="admin-header-right">
          <div class="admin-refresh-chip">
            <div class="admin-pulse"></div>
            updated {{ fetchedLabel }}
          </div>
          <button class="admin-btn admin-btn-ghost" :disabled="loading" @click="load()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-3-6.7"/><path d="M21 4v6h-6"/></svg>
            {{ loading ? 'Loading…' : 'Refresh' }}
          </button>
          <button class="admin-btn admin-btn-ghost" @click="signOut">Sign out</button>
        </div>
      </header>

      <main class="admin-main">
        <RouterView :data="data" :error="error" :loading="loading" />
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
import { computed, onMounted, ref } from 'vue'
import type { SubscriptionDashboard } from '@/types'
import { fetchSubscriptionDashboard } from '@/services/sports'

const STORAGE_KEY = 'ms-admin-token'

const savedToken = readSavedToken()

const token = ref(savedToken ?? '')
const data = ref<SubscriptionDashboard | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const fetchedAt = ref<Date | null>(null)

/* Read synchronously during setup, not in onMounted: if we wait, the first
   paint has no data yet and the password form flashes on every reload before
   the saved token is restored. Safe here — /admin is never prerendered and
   scripts/prerender.mjs does no SSR, so this only ever runs in a browser. */
const booting = ref(savedToken !== null)

function readSavedToken(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null // Private mode or storage disabled — fall through to the gate.
  }
}

const fetchedLabel = computed(() =>
  fetchedAt.value ? fetchedAt.value.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : '—',
)

async function load() {
  const value = token.value.trim()
  if (!value) return
  loading.value = true
  error.value = null
  try {
    data.value = await fetchSubscriptionDashboard(value)
    fetchedAt.value = new Date()
    // Outside the fetch's failure path: a storage write that throws must not
    // be reported as a bad token when the dashboard actually loaded.
    persistToken(value)
  } catch (e) {
    forgetToken()
    data.value = null
    error.value = e instanceof Error ? e.message : 'Could not load dashboard'
  } finally {
    loading.value = false
  }
}

function persistToken(value: string) {
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Storage unavailable — the session still works, it just won't survive a reload.
  }
}

function forgetToken() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Nothing to clear if storage is unavailable.
  }
}

function signOut() {
  forgetToken()
  token.value = ''
  data.value = null
  error.value = null
}

onMounted(async () => {
  if (savedToken) await load()
  booting.value = false
})
</script>

<style src="./admin.css"></style>
