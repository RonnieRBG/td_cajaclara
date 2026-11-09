import { createRouter, createWebHistory } from 'vue-router'
import { nextTick } from 'vue'
import DashboardView from '@/views/DashboardView.vue'
import OperationsView from '@/views/OperationsView.vue'
import ReceivablesView from '@/views/ReceivablesView.vue'
import MonthlySummaryView from '@/views/MonthlySummaryView.vue'
import PlaceholderView from '@/views/PlaceholderView.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView
  },
  {
    path: '/dashboard',
    redirect: '/'
  },
  {
    path: '/operaciones',
    name: 'Operaciones',
    component: OperationsView
  },
  {
    path: '/cobros',
    name: 'Cobros',
    component: ReceivablesView
  },
  {
    path: '/resumen',
    name: 'Resumen',
    component: MonthlySummaryView
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

router.afterEach(async (_to, _from, failure) => {
  if (failure) return

  await nextTick()
  const focusTarget = document.querySelector('#main-content h1') ?? document.querySelector('#main-content')
  if (focusTarget?.tagName === 'H1' && !focusTarget.hasAttribute('tabindex')) {
    focusTarget.setAttribute('tabindex', '-1')
  }
  focusTarget?.focus({ preventScroll: true })
})

export default router
