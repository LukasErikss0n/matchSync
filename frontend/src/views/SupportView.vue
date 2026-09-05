<template>
  <main class="min-h-screen px-4 sm:px-6 py-10 sm:py-14">
    <div class="max-w-lg mx-auto fade-up">
      <!-- Header -->
      <div class="flex items-center gap-3 mb-8">
        <button
          class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 transition-colors"
          style="background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.16)"
          aria-label="Back"
          @click="goBack"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
            <path d="M15 5l-7 7 7 7" />
          </svg>
        </button>
        <h1 class="text-2xl font-extrabold tracking-tight" style="letter-spacing: -0.02em">
          Report something
        </h1>
      </div>

      <Transition name="stepin" mode="out-in">
        <!-- Confirmation state -->
        <div v-if="submitted" key="confirm" class="glass-card rounded-[17px] px-6 py-10 text-center stepin">
          <div
            class="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style="background: rgba(142, 205, 242, 0.14); border: 1px solid rgba(142, 205, 242, 0.3)"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8ecdf2" stroke-width="2.6">
              <path d="m5 12 5 5 9-10" />
            </svg>
          </div>
          <h2 class="text-xl font-extrabold mb-1.5" style="letter-spacing: -0.3px">Thanks, we will get right to it.</h2>
          <p class="text-sm font-medium" style="color: rgba(244, 247, 251, 0.6)">
            <template v-if="submittedEmail">
              We'll get back to you at <strong style="color: var(--ms-text)">{{ submittedEmail }}</strong>.
            </template>
            <template v-else>
              Thanks for flagging it, no reply requested.
            </template>
          </p>
          <RouterLink
            to="/"
            class="ms-btn-secondary inline-flex items-center gap-2 rounded-2xl px-5 py-3 font-bold text-sm mt-7"
          >
            Back to home
          </RouterLink>
        </div>

        <!-- Form -->
        <form v-else key="form" class="flex flex-col gap-6 stepin" @submit.prevent="handleSubmit">
          <!-- Type picker -->
          <div class="flex flex-col gap-2.5">
            <button
              v-for="opt in typeOptions"
              :key="opt.type"
              type="button"
              class="support-type-card glass-card rounded-[17px] px-4 py-3.5 flex items-center gap-3.5 text-left transition-all"
              :class="{ selected: supportType === opt.type }"
              @click="selectType(opt.type)"
            >
              <span
                class="w-9 h-9 rounded-[11px] flex items-center justify-center flex-shrink-0"
                :style="`background: ${opt.iconBg}; border: 1px solid ${opt.iconBorder}`"
              >
                <span v-html="opt.icon" />
              </span>
              <span class="min-w-0 flex-1">
                <span class="block font-bold text-[14.5px]">{{ opt.title }}</span>
                <span class="block text-xs mt-0.5" style="color: rgba(244, 247, 251, 0.5)">{{ opt.description }}</span>
              </span>
              <span
                class="support-radio w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                :class="{ selected: supportType === opt.type }"
              >
                <svg v-if="supportType === opt.type" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#08131f" stroke-width="3.2">
                  <path d="m5 12 5 5 9-10" />
                </svg>
              </span>
            </button>
          </div>

          <!-- What happened -->
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-widest mb-2" style="color: rgba(244, 247, 251, 0.45)">
              What happened?
            </label>
            <textarea
              v-model="supportText"
              rows="5"
              class="w-full rounded-[14px] px-4 py-3 text-[14.5px] outline-none resize-none glass-card"
              style="color: var(--ms-text)"
              :placeholder="textPlaceholder"
            />
          </div>

          <!-- Page (bug only) -->
          <div v-if="supportType === 'bug'" class="relative">
            <label class="block text-[11px] font-bold uppercase tracking-widest mb-2" style="color: rgba(244, 247, 251, 0.45)">
              Page
            </label>
            <button
              type="button"
              class="filter-pill w-full justify-between"
              @click="pageMenuOpen = !pageMenuOpen"
            >
              {{ supportPage ?? "Select a page" }}
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                class="transition-transform flex-shrink-0"
                :style="pageMenuOpen ? 'transform: rotate(180deg)' : ''"
              >
                <path d="m6 9 6 6 6-6" />
              </svg>
            </button>
            <div v-if="pageMenuOpen" class="filter-menu w-full">
              <button
                v-for="p in pageOptions"
                :key="p"
                type="button"
                class="filter-item"
                :class="{ chosen: supportPage === p }"
                @click="selectPage(p)"
              >
                {{ p }}
              </button>
            </div>
          </div>
          <div v-if="pageMenuOpen" class="fixed inset-0 z-10" @click="pageMenuOpen = false" />

          <!-- Want a response -->
          <div class="flex flex-col gap-3 rounded-[14px] px-4 py-3.5 glass-card">
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-2.5">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8ecdf2" stroke-width="2">
                  <rect x="2" y="5" width="20" height="14" rx="3" />
                  <path d="m3 7 9 6 9-6" />
                </svg>
                <span class="text-[13.5px] font-semibold">Want a response?</span>
              </div>
              <button
                type="button"
                class="support-toggle"
                :class="{ on: wantResponse }"
                role="switch"
                :aria-checked="wantResponse"
                @click="wantResponse = !wantResponse; emailError = ''"
              >
                <span class="support-toggle-knob" />
              </button>
            </div>
            <Transition name="stepin">
              <div v-if="wantResponse">
                <input
                  v-model="supportEmail"
                  type="text"
                  class="w-full rounded-xl px-3.5 py-2.5 text-[13.5px] outline-none"
                  style="background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(255, 255, 255, 0.14); color: var(--ms-text)"
                  placeholder="you@example.com"
                  @input="emailError = ''"
                />
                <p v-if="emailError" class="text-xs font-semibold mt-1.5" style="color: #f2a0a0">{{ emailError }}</p>
              </div>
            </Transition>
          </div>

          <p v-if="error" class="text-sm font-semibold" style="color: #f2a0a0">{{ error }}</p>

          <button
            type="submit"
            class="support-send-btn rounded-2xl w-full py-3.5 font-bold text-[15px] disabled:opacity-40"
            :disabled="!canSubmit || sending"
          >
            {{ sending ? "Sending…" : "Send report" }}
          </button>
        </form>
      </Transition>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import type { SupportType } from '@/types'
import { sendSupportRequest } from '@/services/sports'

const router = useRouter()

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}

const bugIcon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f2a0a0" stroke-width="2"><path d="M9 9V7a3 3 0 0 1 6 0v2M6 10h12v6a6 6 0 0 1-12 0v-6zM3 13h3M18 13h3M8 5 6 3M16 5l2-2M9 18l-2 2M15 18l2 2"/></svg>`
const improvementIcon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f2cf78" stroke-width="2"><path d="M9 18h6M10 21h4M8 14a5 5 0 1 1 8 0c-.8.9-1.5 1.6-1.5 3h-5c0-1.4-.7-2.1-1.5-3z"/></svg>`
const otherIcon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="5" cy="12" r="1.6" fill="#a9e0b8"/><circle cx="12" cy="12" r="1.6" fill="#a9e0b8"/><circle cx="19" cy="12" r="1.6" fill="#a9e0b8"/></svg>`

const typeOptions: {
  type: SupportType
  title: string
  description: string
  icon: string
  iconBg: string
  iconBorder: string
}[] = [
  {
    type: 'bug',
    title: 'Bug',
    description: 'Something is broken or not working right',
    icon: bugIcon,
    iconBg: 'rgba(242, 160, 160, 0.14)',
    iconBorder: 'rgba(242, 160, 160, 0.3)',
  },
  {
    type: 'improvement',
    title: 'Improvement',
    description: 'An idea to make MatchCalender better',
    icon: improvementIcon,
    iconBg: 'rgba(242, 207, 120, 0.14)',
    iconBorder: 'rgba(242, 207, 120, 0.3)',
  },
  {
    type: 'other',
    title: 'Other',
    description: 'Anything else you want to tell us',
    icon: otherIcon,
    iconBg: 'rgba(169, 224, 184, 0.14)',
    iconBorder: 'rgba(169, 224, 184, 0.3)',
  },
]

const placeholders: Record<SupportType, string> = {
  bug: "What went wrong? What did you expect to happen instead?",
  improvement: 'What would you like to see changed or added?',
  other: "What's on your mind?",
}

const pageOptions = ['Home', 'Matches', 'Team selector', 'Calendar link', 'Other']

const supportType = ref<SupportType>('bug')
const supportText = ref('')
const supportPage = ref<string | null>(null)
const pageMenuOpen = ref(false)
const wantResponse = ref(false)
const supportEmail = ref('')
const submitted = ref(false)
const submittedEmail = ref('')
const sending = ref(false)
const error = ref('')
const emailError = ref('')

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const textPlaceholder = computed(() => placeholders[supportType.value])

function selectType(t: SupportType) {
  supportType.value = t
  if (t !== 'bug') {
    supportPage.value = null
    pageMenuOpen.value = false
  }
}

function selectPage(p: string) {
  supportPage.value = p
  pageMenuOpen.value = false
}

function detectDevice(): string {
  const ua = navigator.userAgent
  let os = 'Unknown device'
  if (/iPhone/.test(ua)) os = 'iPhone'
  else if (/iPad/.test(ua)) os = 'iPad'
  else if (/Android/.test(ua)) os = 'Android'
  else if (/Mac/.test(ua)) os = 'Mac'
  else if (/Windows/.test(ua)) os = 'Windows'
  else if (/CrOS/.test(ua)) os = 'ChromeOS'
  else if (/Linux/.test(ua)) os = 'Linux'

  let browser = 'Unknown browser'
  if (/Edg\//.test(ua)) browser = 'Edge'
  else if (/Chrome\//.test(ua)) browser = 'Chrome'
  else if (/Firefox\//.test(ua)) browser = 'Firefox'
  else if (/Safari\//.test(ua)) browser = 'Safari'

  return `${os} · ${browser}`
}
const device = detectDevice()

const canSubmit = computed(() => {
  if (!supportText.value.trim()) return false
  if (wantResponse.value && !supportEmail.value.trim()) return false
  return true
})

async function handleSubmit() {
  if (!canSubmit.value || sending.value) return
  emailError.value = ''
  if (wantResponse.value && !EMAIL_RE.test(supportEmail.value.trim())) {
    emailError.value = 'Not a valid email'
    return
  }
  sending.value = true
  error.value = ''
  try {
    await sendSupportRequest({
      type: supportType.value,
      text: supportText.value.trim(),
      page: supportType.value === 'bug' ? supportPage.value : null,
      device,
      email: wantResponse.value ? supportEmail.value.trim() : null,
    })
    submittedEmail.value = wantResponse.value ? supportEmail.value.trim() : ''
    submitted.value = true
  } catch {
    error.value = "Couldn't send your report — please try again in a moment."
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.support-type-card {
  border: 1px solid var(--ms-glass-border);
  cursor: pointer;
}

.support-type-card.selected {
  border-color: rgba(142, 205, 242, 0.5);
  background: rgba(142, 205, 242, 0.1);
}

.support-radio {
  border: 2px solid rgba(255, 255, 255, 0.22);
  background: transparent;
  transition: all 0.15s ease;
}

.support-radio.selected {
  border-color: var(--ms-blue);
  background: linear-gradient(160deg, var(--ms-blue), var(--ms-blue-dark));
}

.support-toggle {
  width: 42px;
  height: 25px;
  border-radius: 999px;
  box-sizing: border-box;
  padding: 2px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.14);
  flex-shrink: 0;
  transition: background 0.15s ease;
  position: relative;
}

.support-toggle.on {
  background: var(--ms-blue-dark);
  border-color: rgba(142, 205, 242, 0.5);
}

.support-toggle-knob {
  display: block;
  width: 21px;
  height: 21px;
  border-radius: 50%;
  background: white;
  transition: transform 0.15s ease;
}

.support-toggle.on .support-toggle-knob {
  transform: translateX(17px);
}

.support-send-btn {
  color: var(--ms-ink);
  background: linear-gradient(160deg, var(--ms-blue) 0%, var(--ms-blue-dark) 100%);
  border: none;
  box-shadow: 0 16px 32px -12px rgba(94, 178, 230, 0.55);
  transition: filter 0.15s ease;
}

.support-send-btn:hover:not(:disabled) {
  filter: brightness(1.06);
}

@media (prefers-reduced-motion: no-preference) {
  .stepin {
    animation: stepin 0.32s cubic-bezier(0.2, 0.9, 0.3, 1) forwards;
  }
}

@keyframes stepin {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* iOS Safari auto-zooms on focus when a field's font-size is under 16px —
   bump these to 16px on small screens only, so it never triggers. */
@media (max-width: 639px) {
  textarea,
  input[type="text"] {
    font-size: 16px;
  }
}
</style>
