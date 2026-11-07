<script setup>
import { ref } from 'vue'
import { mockData } from '@/data/dashboardMock'
import StatCard from '@/components/common/StatCard.vue'
import QuickActions from '@/components/common/QuickActions.vue'
import CashChart from '@/components/dashboard/CashChart.vue'
import OperationsSummary from '@/components/dashboard/OperationsSummary.vue'
import TopProducts from '@/components/dashboard/TopProducts.vue'
import PriorityCollections from '@/components/dashboard/PriorityCollections.vue'
import RecentOperations from '@/components/dashboard/RecentOperations.vue'
import NewOperationModal from '@/components/dashboard/NewOperationModal.vue'

// Modal state
const isModalOpen = ref(false)
const modalType = ref('VENTA_PAGADA')
const modalInitialData = ref(null)

// Toast notification state
const toastMessage = ref('')
const showToast = ref(false)

const triggerToast = (msg) => {
  toastMessage.value = msg
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3500)
}

const handleOpenModal = (type) => {
  modalType.value = type
  modalInitialData.value = null
  isModalOpen.value = true
}

const handlePayCollection = (item) => {
  modalType.value = 'VENTA_PAGADA'
  modalInitialData.value = {
    concepto: `Cobro de ${item.detalle}`,
    monto: item.monto,
    cliente: item.cliente
  }
  isModalOpen.value = true
}

const handleModalSuccess = (data) => {
  triggerToast(`Movimiento registrado: ${data.concepto} por $${data.monto?.toLocaleString('es-CL')}`)
}
</script>

<template>
  <div class="dashboard-view">
    <!-- Feedback Toast Notification -->
    <div v-if="showToast" class="toast-notification" role="status" aria-live="polite">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
      <span>{{ toastMessage }}</span>
    </div>

    <!-- Quick Actions Bar -->
    <section class="section-quick-actions" aria-label="Acciones rápidas de caja">
      <QuickActions @open-modal="handleOpenModal" />
    </section>

    <!-- Financial KPIs (4 Cards Grid) -->
    <section class="section-kpis" aria-label="Indicadores financieros clave del periodo">
      <div class="kpis-grid">
        <!-- Saldo del periodo (Hero Card) -->
        <StatCard
          title="Saldo del periodo"
          :amount="mockData.kpis.saldoPeriodo"
          subtitle="Ventas cobradas menos compras y gastos"
          variant="balance"
          trend="+18.4%"
          trendLabel="vs septiembre"
          tooltip="Es el dinero líquido disponible tras restar los gastos a los ingresos cobrados."
        />

        <!-- Ventas del mes -->
        <StatCard
          title="Ventas del mes"
          :amount="mockData.kpis.ventasMes"
          subtitle="Total de ingresos cobrados en caja"
          variant="income"
          trend="+12.5%"
          trendLabel="126 ventas"
          tooltip="Suma total de todas las ventas que ya ingresaron a la caja."
        />

        <!-- Compras y gastos -->
        <StatCard
          title="Compras y gastos"
          :amount="mockData.kpis.comprasGastos"
          subtitle="Reposición de mercadería y fletes"
          variant="expense"
          trend="-4.2%"
          trendLabel="41 salidas"
          tooltip="Suma de mercadería comprada más gastos operativos como transporte o insumos."
        />

        <!-- Dinero que te deben -->
        <StatCard
          title="Dinero que te deben"
          :amount="mockData.kpis.pendienteCobrar"
          subtitle="7 ventas pendientes por cobrar"
          variant="pending"
          badge="Atención requerida"
          tooltip="Monto pendiente de cobro de clientes que compraron al fiado."
        />
      </div>
    </section>

    <!-- Main Analytics & Operational Section (2 Columns Desktop) -->
    <div class="analytics-row">
      <!-- Left Column: Flow Chart & Recent Operations -->
      <div class="analytics-col-main">
        <CashChart :weeklyData="mockData.weeklyFlow" />
        <RecentOperations :operations="mockData.recentOperations" />
      </div>

      <!-- Right Column: Priority Collections, Activity Summary & Top Products -->
      <div class="analytics-col-side">
        <PriorityCollections
          :collections="mockData.priorityCollections"
          @pay-collection="handlePayCollection"
        />
        <OperationsSummary :summary="mockData.operationsSummary" />
        <TopProducts :products="mockData.topProducts" />
      </div>
    </div>

    <!-- Modal for New Operation / Collection -->
    <NewOperationModal
      :isOpen="isModalOpen"
      :initialType="modalType"
      :initialData="modalInitialData"
      @close="isModalOpen = false"
      @success="handleModalSuccess"
    />
  </div>
</template>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
  position: relative;
}

/* Toast */
.toast-notification {
  position: fixed;
  bottom: 80px;
  right: var(--space-6);
  background-color: var(--color-slate-900);
  color: white;
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xl);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: 0.875rem;
  font-weight: 500;
  z-index: 1200;
  animation: slideUp 0.2s ease-out;
}

.toast-notification svg {
  color: var(--color-emerald-400);
  flex-shrink: 0;
}

/* Section Quick Actions */
.section-quick-actions {
  width: 100%;
}

/* Section KPIs */
.section-kpis {
  width: 100%;
}

.kpis-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-5);
}

@media (min-width: 640px) {
  .kpis-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-5);
  }
}

@media (min-width: 1024px) {
  .kpis-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-5);
  }
}

/* 2-Column Analytics Layout */
.analytics-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-8);
  align-items: start;
}

@media (min-width: 1024px) {
  .analytics-row {
    grid-template-columns: 1.4fr 1fr;
    gap: var(--space-8);
  }
}

.analytics-col-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.analytics-col-side {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 767px) {
  .toast-notification {
    bottom: 75px;
    left: var(--space-4);
    right: var(--space-4);
  }
}
</style>
