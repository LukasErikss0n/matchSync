import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import leaguePages from '@/data/leaguePages.json'
import guidePages from '@/data/guidePages.json'
import { applyPageMeta } from '@/utils/seo'

// Only the home route (almost always the first thing a visitor loads) is
// eager. Everything else is a separate chunk, fetched on navigation — a
// homepage visitor was otherwise downloading and parsing MatchesView's whole
// dependency tree (MatchRow, StandingsModal, MatchPreviewModal, the team
// selector wizard, ...) plus every static/legal page before painting anything.
const MatchesView = () => import('@/views/MatchesView.vue')
const ApiDocsView = () => import('@/views/ApiDocsView.vue')
const PrivacyPolicyView = () => import('@/views/PrivacyPolicyView.vue')
const TermsOfServiceView = () => import('@/views/TermsOfServiceView.vue')
const SupportView = () => import('@/views/SupportView.vue')
const NotFoundView = () => import('@/views/NotFoundView.vue')
const GuideView = () => import('@/views/GuideView.vue')

const HOME_DESCRIPTION =
  'Subscribe once and get every fixture, reschedule and playoff round auto-synced to your calendar for football, hockey, basketball and more.'
const MATCHES_DESCRIPTION =
  'Browse every fixture and result by league or team, updated live and ready to sync to your calendar.'
const API_DOCS_DESCRIPTION =
  'Every calendar link generated on MatchCalender is a standard iCal feed you can subscribe to from any calendar app. See the feed URL format and parameters.'
const PRIVACY_DESCRIPTION =
  'MatchCalender only stores the sport, team and league selections needed to generate your calendar link. No accounts, no tracking, no ads.'
const TERMS_DESCRIPTION =
  'Read the terms covering personal use of MatchCalender, including sharing calendar links with friends and the restriction on commercial redistribution.'
const SUPPORT_DESCRIPTION =
  'Report a bug, suggest an improvement, or ask a question about MatchCalender.'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth', top: 96 }
    }
    // Query-only updates on the same path (e.g. the team-selector wizard
    // syncing its step/sport/team into the URL) shouldn't jerk the page
    // back to the top — only an actual page change should.
    if (to.path === from.path) return false
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: 'MatchCalender, live sports calendars that stay in sync',
        description: HOME_DESCRIPTION,
      },
    },
    {
      path: '/matches',
      name: 'matches',
      component: MatchesView,
      meta: {
        title: 'All matches, Fixtures & Results | MatchCalender',
        description: MATCHES_DESCRIPTION,
      },
    },
    {
      path: '/api-docs',
      name: 'api-docs',
      component: ApiDocsView,
      meta: {
        title: 'API docs | MatchCalender',
        description: API_DOCS_DESCRIPTION,
      },
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: PrivacyPolicyView,
      meta: {
        title: 'Privacy policy | MatchCalender',
        description: PRIVACY_DESCRIPTION,
      },
    },
    {
      path: '/terms',
      name: 'terms',
      component: TermsOfServiceView,
      meta: {
        title: 'Terms of service | MatchCalender',
        description: TERMS_DESCRIPTION,
      },
    },
    {
      path: '/support',
      name: 'support',
      component: SupportView,
      meta: {
        title: 'Help & feedback | MatchCalender',
        description: SUPPORT_DESCRIPTION,
      },
    },
    // Per-league landing pages — each reuses MatchesView, locked to one league
    // and given its own SEO title/description/H1 (see src/data/leaguePages.json).
    ...leaguePages.map((p) => ({
      path: p.path,
      name: `league-${p.slug}`,
      component: MatchesView,
      meta: {
        title: p.title,
        description: p.description,
        leagueSlug: p.slug,
        h1: p.h1,
        intro: p.intro,
        isLeaguePage: true,
      },
    })),
    // Operator-only. noindex because this must never reach a search result,
    // and lazily imported so the dashboard isn't part of the bundle every
    // visitor downloads. The real gate is the backend's ADMIN_TOKEN — this
    // route renders a token prompt, not data.
    {
      path: guidePages.en.path,
      name: 'guide',
      component: GuideView,
      props: { locale: 'en' },
      meta: {
        title: guidePages.en.title,
        description: guidePages.en.description,
      },
    },
    {
      path: guidePages.sv.path,
      name: 'guide-sv',
      component: GuideView,
      props: { locale: 'sv' },
      meta: {
        title: guidePages.sv.title,
        description: guidePages.sv.description,
      },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
      meta: {
        title: 'Subscriptions | MatchCalender',
        description: 'Operator dashboard.',
        noindex: true,
      },
    },
    // Catch-all. prod-server.mjs already answers 404 for anything not
    // prerendered; this renders something useful inside that response instead
    // of the blank shell an unmatched route would leave behind.
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
      meta: {
        title: 'Page not found | MatchCalender',
        description: HOME_DESCRIPTION,
      },
    },
  ]
})

router.afterEach((to) => {
  applyPageMeta({
    title: (to.meta.title as string) ?? 'MatchCalender',
    description: (to.meta.description as string) ?? HOME_DESCRIPTION,
    path: to.path,
    noindex: to.name === 'not-found' || to.meta.noindex === true,
  })
})

export default router
