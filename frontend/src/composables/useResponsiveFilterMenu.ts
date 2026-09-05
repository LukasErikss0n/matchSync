import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const NARROW_BREAKPOINT_PX = 639

export function useResponsiveFilterMenu() {
  const open = ref<'league' | 'team' | null>(null)
  const leagueBtn = ref<HTMLButtonElement | null>(null)
  const teamBtn = ref<HTMLButtonElement | null>(null)
  const isNarrowScreen = ref(false)
  const menuTop = ref(0)

  function updateIsNarrowScreen() {
    isNarrowScreen.value = window.innerWidth <= NARROW_BREAKPOINT_PX
  }

  const menuPositionStyle = computed(() =>
    isNarrowScreen.value
      ? {
          position: 'fixed' as const,
          top: `${menuTop.value}px`,
          left: '0.75rem',
          right: '0.75rem',
          maxWidth: 'none',
          minWidth: '0',
          maxHeight: `${Math.max(160, window.innerHeight - menuTop.value - 12)}px`,
        }
      : {},
  )

  watch(open, (which) => {
    if (!isNarrowScreen.value) return
    if (which) {
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
      document.body.style.overflow = 'hidden'
      if (scrollbarWidth > 0) document.body.style.paddingRight = `${scrollbarWidth}px`
    } else {
      document.body.style.overflow = ''
      document.body.style.paddingRight = ''
    }
  })

  function toggle(which: 'league' | 'team') {
    const wasOpen = open.value === which
    open.value = wasOpen ? null : which
    if (wasOpen) return
    nextTick(() => {
      const btn = which === 'league' ? leagueBtn.value : teamBtn.value
      if (btn) menuTop.value = btn.getBoundingClientRect().bottom + 8
    })
  }

  onMounted(() => {
    updateIsNarrowScreen()
    window.addEventListener('resize', updateIsNarrowScreen)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateIsNarrowScreen)
    document.body.style.overflow = ''
    document.body.style.paddingRight = ''
  })

  return { open, leagueBtn, teamBtn, menuPositionStyle, toggle }
}
