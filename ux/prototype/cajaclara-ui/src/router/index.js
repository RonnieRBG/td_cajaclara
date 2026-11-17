import { createRouter, createWebHistory } from 'vue-router'
import { nextTick } from 'vue'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import OperationsView from '@/views/OperationsView.vue'
import ReceivablesView from '@/views/ReceivablesView.vue'
import MonthlySummaryView from '@/views/MonthlySummaryView.vue'
import PlaceholderView from '@/views/PlaceholderView.vue'
import { useAuth } from '@/composables/useAuth'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { layout: 'auth', focusTarget: '#username' }
  },
  {
    path: '/dashboard',
    redirect: '/'
  },
  {
    path: '/operaciones',
    name: 'Operaciones',
    component: OperationsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/cobros',
    name: 'Cobros',
    component: ReceivablesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/resumen',
    name: 'Resumen',
    component: MonthlySummaryView,
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach(async (to) => {
  const auth = useAuth()
  const restored = await auth.restoreSession()

  if (to.name === 'Login' && restored) {
    return { name: 'Dashboard', replace: true }
  }

  if (to.meta.requiresAuth && !restored) {
    const query = { redirect: to.fullPath }
    if (auth.error.value?.code === 'CONNECTION_ERROR') query.reason = 'connection'
    if (auth.error.value?.code === 'SESSION_EXPIRED') query.reason = 'expired'
    return { name: 'Login', query, replace: true }
  }
})

router.afterEach(async (to, _from, failure) => {
  if (failure) return

  await nextTick()
  const focusTarget = (to.meta.focusTarget && document.querySelector(to.meta.focusTarget))
    ?? document.querySelector('#main-content h1')
    ?? document.querySelector('#main-content')
  if (focusTarget?.tagName === 'H1' && !focusTarget.hasAttribute('tabindex')) {
    focusTarget.setAttribute('tabindex', '-1')
  }
  focusTarget?.focus({ preventScroll: true })
})

if (typeof window !== 'undefined') {
  window.addEventListener('auth:session-expired', () => {
    const auth = useAuth()
    auth.expireSession()

    const currentRoute = router.currentRoute.value
    if (currentRoute.name === 'Login') return

    router.replace({
      name: 'Login',
      query: {
        reason: 'expired',
        redirect: currentRoute.fullPath
      }
    })
  })
}

export default router
