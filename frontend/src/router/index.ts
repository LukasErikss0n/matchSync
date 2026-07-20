import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import MatchesView from '@/views/MatchesView.vue'
import ApiDocsView from '@/views/ApiDocsView.vue'
import PrivacyPolicyView from '@/views/PrivacyPolicyView.vue'
import TermsOfServiceView from '@/views/TermsOfServiceView.vue'
import { applyPageMeta } from '@/utils/seo'

const HOME_DESCRIPTION =
  'Subscribe once and get every fixture, reschedule and playoff round auto-synced to your calendar for football, hockey, basketball and more.'
const MATCHES_DESCRIPTION =
  'Browse every fixture and result by league or team, updated live and ready to sync to your calendar.'
const API_DOCS_DESCRIPTION =
  'Every calendar link generated on MatchCalender is a standard iCal feed you can subscribe to from any calendar app — see the feed URL format and parameters.'
const PRIVACY_DESCRIPTION =
  'MatchCalender only stores the sport, team and league selections needed to generate your calendar link — no accounts, no tracking, no ads.'
const TERMS_DESCRIPTION =
  'Read the terms covering personal use of MatchCalender, including sharing calendar links with friends and the restriction on commercial redistribution.'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth', top: 96 }
    }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: 'MatchCalender — Live sports calendars that stay in sync',
        description: HOME_DESCRIPTION,
      },
    },
    {
      path: '/matches',
      name: 'matches',
      component: MatchesView,
      meta: {
        title: 'All matches — Fixtures & Results | MatchCalender',
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
  ]
})

router.afterEach((to) => {
  applyPageMeta({
    title: (to.meta.title as string) ?? 'MatchCalender',
    description: (to.meta.description as string) ?? HOME_DESCRIPTION,
    path: to.path,
  })
})

export default router
