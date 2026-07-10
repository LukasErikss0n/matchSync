import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import MatchesView from '@/views/MatchesView.vue'
import PlaceholderPageView from '@/views/PlaceholderPageView.vue'


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
      component: HomeView
    },
    {
      path: '/matches',
      name: 'matches',
      component: MatchesView
    },
    {
      path: '/api-docs',
      name: 'api-docs',
      component: PlaceholderPageView,
      props: {
        label: 'Developers',
        title: 'API docs',
        description: 'Full API reference is coming soon. In the meantime, every calendar link you generate is a standard iCal feed you can subscribe to from any calendar app.',
      },
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: PlaceholderPageView,
      props: {
        label: 'Legal',
        title: 'Privacy policy',
        description: 'Our full privacy policy is being finalized. MatchCalender only stores the sport, team and league selections needed to generate your calendar link.',
      },
    },
    {
      path: '/terms',
      name: 'terms',
      component: PlaceholderPageView,
      props: {
        label: 'Legal',
        title: 'Terms of service',
        description: 'Our full terms of service are being finalized. Check back soon for the complete terms covering use of MatchCalender.',
      },
    },
  ]
})

export default router
