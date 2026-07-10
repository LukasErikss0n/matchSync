import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import MatchesView from '@/views/MatchesView.vue'
import PlaceholderPageView from '@/views/PlaceholderPageView.vue'
import { applyPageMeta } from '@/utils/seo'

const HOME_DESCRIPTION =
  'Subscribe once and get every fixture, reschedule and playoff round auto-synced to your calendar for football, hockey, basketball and more.'
const MATCHES_DESCRIPTION =
  'Browse every fixture and result by league or team, updated live and ready to sync to your calendar.'
const API_DOCS_DESCRIPTION =
  'Full API reference is coming soon. In the meantime, every calendar link you generate is a standard iCal feed you can subscribe to from any calendar app.'
const PRIVACY_DESCRIPTION =
  'Our full privacy policy is being finalized. MatchCalender only stores the sport, team and league selections needed to generate your calendar link.'
const TERMS_DESCRIPTION =
  'Our full terms of service are being finalized. Check back soon for the complete terms covering use of MatchCalender.'

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
      component: PlaceholderPageView,
      props: {
        label: 'Developers',
        title: 'API docs',
        description: API_DOCS_DESCRIPTION,
      },
      meta: {
        title: 'API docs | MatchCalender',
        description: API_DOCS_DESCRIPTION,
      },
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: PlaceholderPageView,
      props: {
        label: 'Legal',
        title: 'Privacy policy',
        description: PRIVACY_DESCRIPTION,
      },
      meta: {
        title: 'Privacy policy | MatchCalender',
        description: PRIVACY_DESCRIPTION,
      },
    },
    {
      path: '/terms',
      name: 'terms',
      component: PlaceholderPageView,
      props: {
        label: 'Legal',
        title: 'Terms of service',
        description: TERMS_DESCRIPTION,
      },
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
