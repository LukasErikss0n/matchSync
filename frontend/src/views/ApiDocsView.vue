<template>
  <Navbar @get-started="showModal = true" />

  <main class="min-h-screen px-4 sm:px-6 py-14 sm:py-16">
    <div class="max-w-3xl mx-auto fade-up">
      <p class="section-label mb-2">Developers</p>
      <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2" style="letter-spacing: -0.02em">
        API docs
      </h1>
      <p class="text-sm mb-10" style="color: var(--ms-muted-dim)">
        The calendar feed is the only public, unauthenticated endpoint — everything else powers the
        site itself and isn't open for third-party use yet.
      </p>

      <div class="docs-content flex flex-col gap-8">
        <section>
          <h2>Calendar feed</h2>
          <p>
            Every calendar link generated on this site is a standard iCal (<code>.ics</code>) feed.
            You can subscribe to it in Google Calendar, Apple Calendar, Outlook or any app that
            supports iCal/webcal URLs, and it stays in sync on its own — no polling logic or auth
            needed on your end.
          </p>
          <pre><code>GET /api/calendar/{sport}/{team_slug}.ics?leagues={league_slug,...}</code></pre>
          <p>No API key required. Responds with <code>Content-Type: text/calendar</code>.</p>
          <ul>
            <li><strong>sport</strong> — sport slug, e.g. <code>football</code>.</li>
            <li><strong>team_slug</strong> — team slug, e.g. <code>arsenal</code>.</li>
            <li>
              <strong>leagues</strong> — optional, comma-separated league slugs to restrict the feed
              to (e.g. only Champions League, not domestic league). Omit it to include every league
              the team competes in.
            </li>
          </ul>
          <p>Example:</p>
          <pre><code>GET /api/calendar/football/arsenal.ics?leagues=premier-league,uefa-champions-league</code></pre>
          <p>
            The feed only ever contains upcoming fixtures, refreshes hourly
            (<code>REFRESH-INTERVAL</code> / <code>X-PUBLISHED-TTL</code> of 1 hour), and each event
            carries a stable UID so reschedules update the existing entry in your calendar instead
            of duplicating it.
          </p>
        </section>

        <section>
          <h2>Getting a feed URL</h2>
          <p>
            Team and league slugs aren't published as a static list, so the easiest way to get a
            correct feed URL is to pick your team on the
            <RouterLink to="/">home page</RouterLink> — it builds the exact URL above for you.
          </p>
        </section>

        <section>
          <h2>Everything else is private</h2>
          <p>
            The REST endpoints behind the site (<code>/api/sports</code>, <code>/api/teams</code>,
            <code>/api/matches</code>, <code>/api/matches/featured</code>,
            <code>/api/leagues/{'{'}slug{'}'}/season-stats</code>) require an
            <code>X-API-Key</code> header and are reserved for the frontend itself — there's no
            public developer key issuance at this time.
          </p>
        </section>

        <section>
          <h2>Questions</h2>
          <p>
            Need something the calendar feed doesn't cover? Email
            <a href="mailto:info@matchcalender.io">info@matchcalender.io</a>.
          </p>
        </section>
      </div>

      <RouterLink
        to="/"
        class="ms-btn-secondary inline-flex items-center gap-2 rounded-2xl px-5 py-3 font-bold text-sm mt-12"
      >
        <svg viewBox="0 0 16 16" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
        Back to home
      </RouterLink>
    </div>
  </main>

  <Footer />
  <TeamSelectorModal v-if="showModal" @close="showModal = false" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import Footer from '@/components/Footer.vue'
import TeamSelectorModal from '@/components/TeamSelectorModal.vue'

const showModal = ref(false)
</script>

<style scoped>
.docs-content :deep(h2) {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  margin-bottom: 0.75rem;
}

.docs-content :deep(p),
.docs-content :deep(li) {
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--ms-muted);
}

.docs-content :deep(p + p),
.docs-content :deep(pre + p) {
  margin-top: 0.75rem;
}

.docs-content :deep(ul) {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-left: 1.25rem;
  list-style: disc;
  margin-top: 0.75rem;
}

.docs-content :deep(strong) {
  color: var(--ms-text);
  font-weight: 700;
}

.docs-content :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.85em;
  color: var(--ms-text);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 5px;
  padding: 0.1em 0.4em;
}

.docs-content :deep(pre) {
  margin-top: 0.75rem;
  padding: 0.9rem 1.1rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  overflow-x: auto;
}

.docs-content :deep(pre code) {
  background: none;
  border: none;
  padding: 0;
  font-size: 13px;
}

.docs-content :deep(a) {
  color: var(--ms-blue);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
