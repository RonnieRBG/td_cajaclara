<script setup>
import { ref } from 'vue'
import { mockData } from '@/data/dashboardMock'
import AppSidebar from '@/components/common/AppSidebar.vue'
import AppHeader from '@/components/common/AppHeader.vue'
import AppBottomNav from '@/components/common/AppBottomNav.vue'

const isSidebarOpen = ref(false)

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const closeSidebar = () => {
  isSidebarOpen.value = false
}
</script>

<template>
  <div class="app-layout">
    <!-- Skip link for keyboard accessibility -->
    <a href="#main-content" class="skip-link">Saltar al contenido principal</a>

    <!-- Sidebar navigation (Desktop permanent, Mobile/Tablet drawer) -->
    <AppSidebar
      :isOpen="isSidebarOpen"
      :pendingCount="mockData.operationsSummary.cuentasPendientes"
      @close="closeSidebar"
    />

    <!-- Main Workspace Container -->
    <div class="app-wrapper">
      <!-- Top Bar Header -->
      <AppHeader
        :businessName="mockData.business.name"
        :period="mockData.business.period"
        :ownerName="mockData.business.owner"
        :ownerInitials="mockData.business.initials"
        @toggle-sidebar="toggleSidebar"
      />

      <!-- Main Page Content -->
      <main id="main-content" class="app-main">
        <router-view />
      </main>
    </div>

    <!-- Bottom Navigation Bar for Mobile -->
    <AppBottomNav :pendingCount="mockData.operationsSummary.cuentasPendientes" />
  </div>
</template>

<style scoped>
.app-layout {
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
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: var(--sidebar-width);
  transition: margin-left var(--transition-normal);
}

.app-main {
  flex: 1;
  padding: var(--space-6) var(--space-6) var(--space-12) var(--space-6);
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

@media (max-width: 1023px) {
  .app-wrapper {
    margin-left: 0;
  }

  .app-main {
    padding: var(--space-4) var(--space-4) calc(var(--space-12) + 60px) var(--space-4);
  }
}

@media (max-width: 640px) {
  .app-main {
    padding: var(--space-3) var(--space-3) calc(var(--space-10) + 60px) var(--space-3);
  }
}
</style>
