<template>
  <div class="py-10 flex flex-col items-center text-center" role="status" aria-live="polite">
    <div class="icl-badge w-16 h-16 rounded-2xl flex items-center justify-center mb-5" style="background: #131c2e">
      <div class="icl-spinner" aria-hidden="true">
        <span class="icl-spinner-bar" style="transform: rotate(0deg); animation-delay: 0s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(30deg); animation-delay: -1.1s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(60deg); animation-delay: -1s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(90deg); animation-delay: -0.9s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(120deg); animation-delay: -0.8s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(150deg); animation-delay: -0.7s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(180deg); animation-delay: -0.6s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(210deg); animation-delay: -0.5s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(240deg); animation-delay: -0.4s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(270deg); animation-delay: -0.3s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(300deg); animation-delay: -0.2s"></span>
        <span class="icl-spinner-bar" style="transform: rotate(330deg); animation-delay: -0.1s"></span>
      </div>
      <svg class="icl-check icl-check-1" viewBox="0 0 24 24" width="26" height="26" fill="none" aria-hidden="true">
        <path d="M5 12.5l4.5 4.5L19 7" stroke="#8ecdf2" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="icl-phases relative h-5 text-sm font-semibold" style="color: rgba(244,247,251,.75); min-width: 220px">
      <span class="icl-phase icl-phase-a">Grabbing fixtures…</span>
      <span class="icl-phase icl-phase-b">Syncing your calendar…</span>
      <span class="icl-phase icl-phase-c">All set!</span>
    </div>
  </div>
</template>

<style scoped src="./CalendarLinkLoading.css"></style>
