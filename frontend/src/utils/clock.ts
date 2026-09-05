import { ref } from 'vue'

export const nowMs = ref(Date.now())

if (typeof window !== 'undefined') {
  window.setInterval(() => {
    nowMs.value = Date.now()
  }, 30_000)
}
