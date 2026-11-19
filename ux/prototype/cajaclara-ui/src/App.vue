<script setup>
import { computed, provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mockData } from '@/data/dashboardMock'
import AppSidebar from '@/components/common/AppSidebar.vue'
import AppHeader from '@/components/common/AppHeader.vue'
import AppBottomNav from '@/components/common/AppBottomNav.vue'
import { useAuth } from '@/composables/useAuth'
import { getCollectionAlertCount } from '@/services/receivablesService'
import { DEMO_ACCESS_ENABLED, USE_MOCKS } from '@/services/optionsService'

const isSidebarOpen = ref(false)
const route = useRoute()
const router = useRouter()
const { user, logout } = useAuth()
const isAuthLayout = computed(() => route.meta.layout === 'auth')
const pendingCount = ref(USE_MOCKS ? mockData.operationsSummary.cuentasPendientes : null)
const pendingCountError = ref('')
const activePeriod = ref(USE_MOCKS ? mockData.business.period : '')
let countRequestSequence = 0

async function refreshCollectionAlertCount() {
  if (USE_MOCKS) return

  const sequence = ++countRequestSequence
  pendingCountError.value = ''
  try {
    const count = await getCollectionAlertCount()
    if (sequence === countRequestSequence) pendingCount.value = count
  } catch (error) {
    if (sequence === countRequestSequence) {
      pendingCountError.value = error.message || 'No se pudo actualizar el indicador de cobros.'
    }
  }
}

provide('refreshCollectionAlertCount', refreshCollectionAlertCount)
provide('setActivePeriod', (period) => {
  if (!USE_MOCKS) activePeriod.value = period || ''
})

watch([user, isAuthLayout], ([currentUser, authLayout]) => {
  if (USE_MOCKS) return
  if (currentUser && !authLayout) {
    refreshCollectionAlertCount()
  } else {
    countRequestSequence += 1
    pendingCount.value = null
    pendingCountError.value = ''
  }
}, { immediate: true })

watch(() => route.path, () => {
  if (!USE_MOCKS) activePeriod.value = ''
})

// TODO: eliminar acceso demo temporal.
const isDemoSession = computed(() => DEMO_ACCESS_ENABLED && user.value?.isDemo === true)
const profileName = computed(() => user.value?.nombre || user.value?.username || 'Usuario')
const profileInitials = computed(() => (
  profileName.value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'U'
))

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const closeSidebar = () => {
  isSidebarOpen.value = false
}

const handleLogout = async () => {
  const loggedOut = await logout()
  await router.replace({
    name: 'Login',
    query: loggedOut ? {} : { reason: 'logout-error' }
  })
}
</script>

<template>
  <RouterView v-if="isAuthLayout" />

  <div v-else class="app-layout">
    <!-- Skip link for keyboard accessibility -->
    <a href="#main-content" class="skip-link">Saltar al contenido principal</a>

    <!-- Sidebar navigation (Desktop permanent, Mobile/Tablet drawer) -->
    <AppSidebar
      :isOpen="isSidebarOpen"
      :pendingCount="pendingCount"
      :userName="profileName"
      :userEmail="user?.email || ''"
      :userInitials="profileInitials"
      @close="closeSidebar"
    />

    <!-- Main Workspace Container -->
    <div class="app-wrapper">
      <!-- Top Bar Header -->
      <AppHeader
        :businessName="mockData.business.name"
        :period="USE_MOCKS ? mockData.business.period : activePeriod"
        :period-label="USE_MOCKS ? mockData.business.period : ''"
        :show-period="USE_MOCKS || Boolean(activePeriod)"
        :ownerName="profileName"
        :ownerEmail="user?.email || ''"
        :ownerInitials="profileInitials"
        @toggle-sidebar="toggleSidebar"
        @logout="handleLogout"
      />

      <div v-if="pendingCountError" class="layout-api-error" role="alert">
        <span>{{ pendingCountError }}</span>
        <button type="button" @click="refreshCollectionAlertCount">Reintentar</button>
      </div>

      <div v-if="isDemoSession" class="demo-banner" role="status">
        Modo demostración: datos simulados
      </div>

      <!-- Main Page Content -->
      <main id="main-content" class="app-main" tabindex="-1">
        <router-view />
      </main>
    </div>

    <!-- Bottom Navigation Bar for Mobile -->
    <AppBottomNav :pendingCount="pendingCount" />
  </div>
</template>

<style scoped>
.app-layout {
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  display: flex;
  background-color: var(--color-background);
}

.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--color-primary-600);
  color: white;
  padding: var(--space-2) var(--space-4);
  z-index: 2000;
  transition: top 0.2s ease;
  font-weight: 600;
  border-radius: 0 0 var(--radius-md) 0;
}

.skip-link:focus {
  top: 0;
}

.app-wrapper {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  min-width: var(--content-min-width);
  margin-left: var(--layout-sidebar-width);
  transition: margin-left var(--transition-normal);
}

.app-main {
  flex: 1;
  min-width: var(--content-min-width);
  padding: var(--layout-gutter-desktop) var(--layout-gutter-desktop) var(--space-12);
  max-width: var(--layout-content-max);
  width: 100%;
  margin: 0 auto;
}

.demo-banner {
  padding: var(--space-2) var(--layout-gutter-desktop);
  background: #ecfdf5;
  color: #065f46;
  font-size: 0.875rem;
  font-weight: 700;
  text-align: center;
}

.layout-api-error {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--layout-control-gap);
  padding: var(--space-2) var(--layout-gutter-desktop);
  background: var(--color-danger-light);
  color: var(--color-danger);
  font-size: 0.82rem;
  font-weight: 600;
}

.layout-api-error button {
  color: inherit;
  font-weight: 800;
  text-decoration: underline;
}

@media (max-width: 1200px) {
  .app-main {
    padding: var(--layout-gutter-tablet) var(--layout-gutter-tablet) var(--space-12);
  }

  .demo-banner {
    padding-inline: var(--layout-gutter-tablet);
  }

  .layout-api-error {
    padding-inline: var(--layout-gutter-tablet);
  }
}

@media (max-width: 1023px) {
  .app-wrapper {
    margin-left: 0;
  }

  .app-main {
    padding: var(--layout-gutter-tablet) var(--layout-gutter-tablet) calc(var(--space-12) + var(--layout-bottom-nav-height));
  }
}

@media (max-width: 640px) {
  .app-main {
    padding: var(--layout-gutter-mobile) var(--layout-gutter-mobile) calc(var(--space-10) + var(--layout-bottom-nav-height));
  }

  .demo-banner {
    padding-inline: var(--layout-gutter-mobile);
  }

  .layout-api-error {
    padding-inline: var(--layout-gutter-mobile);
  }
}
</style>
