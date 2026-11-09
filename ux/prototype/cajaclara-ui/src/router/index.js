import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import OperationsView from '@/views/OperationsView.vue'
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
    component: PlaceholderView
  },
  {
    path: '/resumen',
    name: 'Resumen',
    component: PlaceholderView
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

export default router
