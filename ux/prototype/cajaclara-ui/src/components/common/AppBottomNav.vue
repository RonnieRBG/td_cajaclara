<script setup>
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  pendingCount: {
    type: Number,
    default: 7
  }
})

const route = useRoute()
const router = useRouter()

const navItems = [
  {
    path: '/',
    label: 'Caja',
    icon: 'dashboard'
  },
  {
    path: '/operaciones',
    label: 'Movimientos',
    icon: 'cash'
  },
  {
    path: '/cobros',
    label: 'Cobros',
    icon: 'receipt',
    badge: true
  },
  {
    path: '/resumen',
    label: 'Resumen',
    icon: 'chart'
  }
]

const isActive = (itemPath) => {
  if (itemPath === '/') {
    return route.path === '/' || route.path === '/dashboard'
  }
  return route.path.startsWith(itemPath)
}

const navigateTo = (path) => {
  router.push(path)
}
</script>

<template>
  <nav class="bottom-nav" aria-label="Navegación móvil inferior">
    <div class="bottom-nav-container">
      <button
        v-for="item in navItems"
        :key="item.path"
        type="button"
        :class="['bottom-nav-item', { 'active': isActive(item.path) }]"
        @click="navigateTo(item.path)"
      >
        <span class="icon-wrap">
          <!-- Dashboard icon -->
          <svg v-if="item.icon === 'dashboard'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1.5" />
            <rect x="14" y="3" width="7" height="7" rx="1.5" />
            <rect x="14" y="14" width="7" height="7" rx="1.5" />
            <rect x="3" y="14" width="7" height="7" rx="1.5" />
          </svg>
          <!-- Movimientos icon -->
          <svg v-else-if="item.icon === 'cash'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23" />
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
          <!-- Cobros icon -->
          <svg v-else-if="item.icon === 'receipt'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z" />
            <line x1="8" y1="8" x2="16" y2="8" />
            <line x1="8" y1="12" x2="14" y2="12" />
          </svg>
          <!-- Resumen icon -->
          <svg v-else-if="item.icon === 'chart'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="6" y1="20" x2="6" y2="14" />
          </svg>

          <!-- Notification badge -->
          <span v-if="item.badge && pendingCount > 0" class="badge-dot" :title="`${pendingCount} pendientes`">
            {{ pendingCount }}
          </span>
        </span>
        <span class="label">{{ item.label }}</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.bottom-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  min-width: 0;
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
  z-index: 1030;
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.bottom-nav-container {
  display: flex;
  width: 100%;
  min-width: 0;
  height: var(--layout-bottom-nav-height);
  justify-content: space-around;
  align-items: center;
  max-width: 600px;
  margin: 0 auto;
}

.bottom-nav-item {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 100%;
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  padding: var(--space-1) 0;
  position: relative;
}

.icon-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-dot {
  position: absolute;
  top: -4px;
  right: -9px;
  background-color: var(--color-amber-500);
  color: white;
  font-size: 0.62rem;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  box-shadow: 0 0 0 1.5px var(--color-surface);
}

.bottom-nav-item.active {
  color: var(--color-primary-600);
  font-weight: 700;
}

.bottom-nav-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 25%;
  right: 25%;
  height: 2.5px;
  background-color: var(--color-primary-600);
  border-radius: 0 0 2px 2px;
}

@media (max-width: 767px) {
  .bottom-nav {
    display: block;
  }
}
</style>
