<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  pendingCount: {
    type: Number,
    default: 7
  }
})

const emit = defineEmits(['close'])

const route = useRoute()
const router = useRouter()

const navItems = [
  {
    name: 'Dashboard',
    path: '/',
    icon: 'dashboard',
    label: 'Inicio / Caja'
  },
  {
    name: 'Operaciones',
    path: '/operaciones',
    icon: 'cash',
    label: 'Compras y ventas'
  },
  {
    name: 'Cobros',
    path: '/cobros',
    icon: 'receipt',
    label: 'Cuentas por cobrar',
    badge: true
  },
  {
    name: 'Resumen',
    path: '/resumen',
    icon: 'chart',
    label: 'Resumen mensual'
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
  emit('close')
}
</script>

<template>
  <div>
    <!-- Backdrop for mobile/tablet drawer -->
    <div
      v-if="isOpen"
      class="sidebar-backdrop"
      @click="$emit('close')"
      aria-hidden="true"
    />

    <aside :class="['app-sidebar', { 'is-open': isOpen }]">
      <!-- Sidebar Brand Header -->
      <div class="sidebar-brand">
        <div class="brand-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="3" />
            <path d="M6 8h12" />
            <path d="M6 12h8" />
            <circle cx="17" cy="12" r="1" fill="currentColor" />
            <path d="M6 16h4" />
          </svg>
        </div>
        <div class="brand-info">
          <span class="brand-title">CajaClara</span>
          <span class="brand-tagline">Caja registradora digital</span>
        </div>
        <button
          type="button"
          class="sidebar-close-btn"
          @click="$emit('close')"
          aria-label="Cerrar menú lateral"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- Navigation Section -->
      <nav class="sidebar-nav" aria-label="Navegación principal">
        <div class="nav-section-title">GESTIÓN DE CAJA</div>
        <ul class="nav-list">
          <li v-for="item in navItems" :key="item.path">
            <button
              type="button"
              :class="['nav-link', { 'active': isActive(item.path) }]"
              @click="navigateTo(item.path)"
            >
              <!-- Icons -->
              <span class="nav-icon" aria-hidden="true">
                <svg v-if="item.icon === 'dashboard'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="7" height="7" rx="1.5" />
                  <rect x="14" y="3" width="7" height="7" rx="1.5" />
                  <rect x="14" y="14" width="7" height="7" rx="1.5" />
                  <rect x="3" y="14" width="7" height="7" rx="1.5" />
                </svg>
                <svg v-else-if="item.icon === 'cash'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="1" x2="12" y2="23" />
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
                <svg v-else-if="item.icon === 'receipt'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z" />
                  <line x1="8" y1="8" x2="16" y2="8" />
                  <line x1="8" y1="12" x2="14" y2="12" />
                  <line x1="8" y1="16" x2="12" y2="16" />
                </svg>
                <svg v-else-if="item.icon === 'chart'" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                  <line x1="2" y1="20" x2="22" y2="20" />
                </svg>
              </span>

              <span class="nav-text">{{ item.label }}</span>

              <span v-if="item.badge && pendingCount > 0" class="nav-badge" :title="`${pendingCount} cuentas por cobrar pendientes`">
                {{ pendingCount }}
              </span>
            </button>
          </li>
        </ul>
      </nav>

      <!-- Micronegocio Banner Footer -->
      <div class="sidebar-footer">
        <div class="business-card">
          <div class="business-avatar" aria-hidden="true">
            AE
          </div>
          <div class="business-details">
            <span class="business-name">Almacén La Esquina</span>
            <span class="business-role">Administrador</span>
          </div>
        </div>
        <div class="sidebar-help">
          <span class="help-dot"></span>
          <span>Caja operando en vivo</span>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.sidebar-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(2px);
  z-index: 1040;
}

.app-sidebar {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  width: var(--sidebar-width);
  background-color: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  z-index: 1050;
  transition: transform var(--transition-normal);
}

.sidebar-brand {
  height: var(--header-height);
  padding: 0 var(--space-5);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.brand-icon {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, var(--color-primary-600) 0%, var(--color-primary-700) 100%);
  color: white;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}

.brand-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  flex: 1;
  min-width: 0;
}

.brand-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--color-primary-800);
  letter-spacing: -0.02em;
}

.brand-tagline {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  font-weight: 500;
}

.sidebar-close-btn {
  display: none;
  background: none;
  border: none;
  color: var(--color-text-muted);
  padding: var(--space-1);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.sidebar-close-btn:hover {
  background-color: var(--color-surface-hover);
  color: var(--color-text);
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-5) var(--space-3);
  overflow-y: auto;
}

.nav-section-title {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  padding: 0 var(--space-3) var(--space-2);
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-link {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: 0.925rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-link:hover {
  background-color: var(--color-primary-50);
  color: var(--color-primary-700);
}

.nav-link.active {
  background-color: var(--color-primary-100);
  color: var(--color-primary-800);
  font-weight: 600;
}

.nav-link.active .nav-icon {
  color: var(--color-primary-600);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  transition: color var(--transition-fast);
  flex-shrink: 0;
}

.nav-text {
  flex: 1;
}

.nav-badge {
  background-color: var(--color-amber-100);
  color: var(--color-amber-800);
  border: 1px solid var(--color-amber-300);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.sidebar-footer {
  padding: var(--space-4) var(--space-4);
  border-top: 1px solid var(--color-border);
  background-color: var(--color-surface-subtle);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.business-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.business-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  font-weight: 700;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.business-details {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
  min-width: 0;
}

.business-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.business-role {
  font-size: 0.72rem;
  color: var(--color-text-muted);
}

.sidebar-help {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.75rem;
  color: var(--color-emerald-700);
  font-weight: 500;
  padding: var(--space-1) var(--space-2);
  background-color: var(--color-emerald-50);
  border-radius: var(--radius-sm);
}

.help-dot {
  width: 7px;
  height: 7px;
  border-radius: var(--radius-full);
  background-color: var(--color-emerald-500);
  box-shadow: 0 0 0 2px var(--color-emerald-200);
}

/* Tablet & Mobile Breakpoints */
@media (max-width: 1023px) {
  .app-sidebar {
    transform: translateX(-100%);
    box-shadow: var(--shadow-lg);
  }

  .app-sidebar.is-open {
    transform: translateX(0);
  }

  .sidebar-backdrop {
    display: block;
  }

  .sidebar-close-btn {
    display: flex;
  }
}
</style>
