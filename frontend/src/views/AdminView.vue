<template>
  <Navbar @get-started="router.push('/')" />

  <main class="min-h-screen">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
      <p class="section-label mb-2">Admin</p>
      <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2" style="letter-spacing: -0.02em">
        Calendar subscriptions
      </h1>
      <p class="mb-8 max-w-xl" style="color: var(--ms-muted)">
        Every issued link, and whether a calendar app is still fetching it.
      </p>

      <form
        v-if="!data && !loading"
        class="glass-card rounded-2xl p-5 max-w-md"
        @submit.prevent="load()"
      >
        <label for="admin-token" class="block text-sm font-bold mb-2">Admin token</label>
        <input
          id="admin-token"
          v-model="token"
          type="password"
          autocomplete="current-password"
          placeholder="ADMIN_TOKEN"
          class="w-full bg-transparent rounded-xl px-4 py-3 text-[15px] outline-none mb-3"
          style="color: var(--ms-text); border: 1px solid rgba(255,255,255,.16)"
        />
        <p v-if="error" class="text-sm font-semibold mb-3" style="color: var(--ms-pink)">
          {{ error }}
        </p>
        <button
          type="submit"
          :disabled="!token.trim()"
          class="ms-btn-primary rounded-full w-full py-3 font-bold text-[15px] disabled:opacity-40"
        >
          Show dashboard
        </button>
      </form>

      <template v-if="loading">
        <div class="grid grid-cols-3 gap-3 mb-6" aria-hidden="true">
          <div v-for="n in 3" :key="`stat-skeleton-${n}`" class="glass-card rounded-2xl p-5">
            <span class="ms-skeleton block" style="width: 48px; height: 30px"></span>
            <span class="ms-skeleton block" style="width: 74%; height: 12px; margin-top: 10px"></span>
          </div>
        </div>
        <div class="glass-card rounded-[24px] overflow-hidden" aria-hidden="true">
          <div
            v-for="n in 5"
            :key="`row-skeleton-${n}`"
            class="flex items-center gap-3 px-4 sm:px-6 py-4 border-b border-white/[0.06] last:border-b-0"
          >
            <div class="min-w-0 flex-1">
              <span class="ms-skeleton block" style="width: 46%; height: 14px"></span>
              <span class="ms-skeleton block" style="width: 30%; height: 11px; margin-top: 7px"></span>
            </div>
            <span class="ms-skeleton flex-none" style="width: 62px; height: 22px; border-radius: 999px"></span>
          </div>
        </div>
      </template>

      <template v-else-if="data">
        <div class="grid grid-cols-3 gap-3 mb-6">
          <div class="glass-card rounded-2xl p-5">
            <div class="text-3xl font-extrabold tabular-nums">{{ data.active_count }}</div>
            <div class="text-xs font-semibold mt-1" style="color: rgba(244,247,251,.5)">
              Active in last {{ data.active_window_days }}d
            </div>
          </div>
          <div class="glass-card rounded-2xl p-5">
            <div class="text-3xl font-extrabold tabular-nums">{{ data.pending_count }}</div>
            <div class="text-xs font-semibold mt-1" style="color: rgba(244,247,251,.5)">
              Never fetched
            </div>
          </div>
          <div class="glass-card rounded-2xl p-5">
            <div class="text-3xl font-extrabold tabular-nums">{{ data.dormant_count }}</div>
            <div class="text-xs font-semibold mt-1" style="color: rgba(244,247,251,.5)">
              Gone quiet
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between gap-3 mb-3">
          <p class="text-sm font-semibold" style="color: rgba(244,247,251,.5)">
            {{ data.subscriptions.length }} issued
            {{ data.subscriptions.length === 1 ? 'link' : 'links' }}
          </p>
          <div class="flex items-center gap-2">
            <button class="filter-pill" @click="load()">Refresh</button>
            <button class="filter-pill" @click="signOut">Sign out</button>
          </div>
        </div>

        <div v-if="data.subscriptions.length" class="glass-card rounded-[24px] overflow-hidden">
          <div
            v-for="s in data.subscriptions"
            :key="s.token"
            class="flex items-center gap-3 px-4 sm:px-6 py-4 border-b border-white/[0.06] last:border-b-0"
          >
            <div class="min-w-0 flex-1">
              <div class="font-bold text-sm break-words">{{ s.team }}</div>
              <div class="text-xs font-semibold mt-0.5 break-words" style="color: rgba(244,247,251,.5)">
                {{ s.leagues.join(' · ') || 'All leagues' }}
              </div>
              <div class="text-xs font-semibold mt-1" style="color: rgba(244,247,251,.35)">
                {{ s.fetch_count }} {{ s.fetch_count === 1 ? 'fetch' : 'fetches' }}
                · {{ lastSeenLabel(s) }}
                <template v-if="s.last_user_agent"> · {{ s.last_user_agent }}</template>
              </div>
            </div>
            <span class="sub-pill flex-none" :class="statusOf(s)">{{ statusOf(s) }}</span>
          </div>
        </div>

        <div v-else class="text-center py-16">
          <p class="font-semibold">No links issued yet</p>
          <p class="text-sm mt-1" style="color: rgba(244,247,251,.5)">
            Links created before subscriber tracking existed don't appear here.
          </p>
        </div>
      </template>
    </div>
  </main>

  <Footer />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { CalendarSubscription, SubscriptionDashboard } from '@/types'
import { fetchSubscriptionDashboard } from '@/services/sports'
import Navbar from '@/components/Navbar.vue'
import Footer from '@/components/Footer.vue'

const STORAGE_KEY = 'ms-admin-token'

const router = useRouter()

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

function statusOf(s: CalendarSubscription): 'active' | 'pending' | 'dormant' {
  if (s.active) return 'active'
  return s.last_seen ? 'dormant' : 'pending'
}

function lastSeenLabel(s: CalendarSubscription): string {
  if (!s.last_seen) return 'never fetched'
  const then = new Date(s.last_seen).getTime()
  const mins = Math.max(0, Math.round((Date.now() - then) / 60_000))
  if (mins < 60) return `last fetch ${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 48) return `last fetch ${hours}h ago`
  return `last fetch ${Math.round(hours / 24)}d ago`
}

onMounted(() => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    token.value = saved
    load()
  }
})
</script>

<style scoped src="./AdminView.css"></style>
