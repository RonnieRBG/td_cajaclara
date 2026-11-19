<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { ApiError } from '@/services/apiClient'
import { getDashboardData } from '@/services/dashboardService'
import { getFilterOptions, getPeriodRange, USE_MOCKS } from '@/services/optionsService'
import StatCard from '@/components/common/StatCard.vue'
import QuickActions from '@/components/common/QuickActions.vue'
import CashChart from '@/components/dashboard/CashChart.vue'
import OperationsSummary from '@/components/dashboard/OperationsSummary.vue'
import TopProducts from '@/components/dashboard/TopProducts.vue'
import PriorityCollections from '@/components/dashboard/PriorityCollections.vue'
import RecentOperations from '@/components/dashboard/RecentOperations.vue'
import NewOperationModal from '@/components/dashboard/NewOperationModal.vue'

const filterOptions = ref(null)
const selectedPeriod = ref('')
const selectedChannel = ref('')
const dashboardData = ref(null)
const loading = ref(false)
const error = ref(null)
const setActivePeriod = inject('setActivePeriod', () => {})
let requestSequence = 0

const periodLabel = computed(() => {
  const period = filterOptions.value?.periods.find(item => item.value === selectedPeriod.value)
  if (!period) return ''
  return `${period.label.charAt(0).toLocaleUpperCase('es-CL')}${period.label.slice(1)} de ${period.year}`
})
watch(periodLabel, setActivePeriod, { immediate: true })
const numberFormatter = new Intl.NumberFormat('es-CL', { maximumFractionDigits: 0 })

const errorMessage = computed(() => {
  if (error.value instanceof ApiError && error.value.code === 'SESSION_EXPIRED') {
    return 'Tu sesión expiró. Inicia sesión nuevamente para volver a consultar el Dashboard.'
  }
  if (error.value instanceof ApiError && error.value.code === 'NETWORK_ERROR') {
    return 'No se pudo conectar con el Backend. Verifica que esté disponible e inténtalo de nuevo.'
  }
  return error.value?.message || 'No se pudo cargar el Dashboard.'
})

const isModalOpen = ref(false)
const modalType = ref('VENTA_PAGADA')
const modalInitialData = ref(null)

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

const loadDashboard = async () => {
  const sequence = ++requestSequence
  loading.value = true
  error.value = null

  try {
    if (!filterOptions.value) filterOptions.value = await getFilterOptions()
    if (!selectedPeriod.value) selectedPeriod.value = filterOptions.value.initialPeriod

    const period = filterOptions.value.periods.find(item => item.value === selectedPeriod.value)
    if (!period) {
      dashboardData.value = null
      return
    }

    const range = getPeriodRange(filterOptions.value, period.year, period.month)
    const result = await getDashboardData({
      ...range,
      channel: selectedChannel.value,
      period: selectedPeriod.value
    })
    if (sequence === requestSequence) dashboardData.value = result
  } catch (requestError) {
    if (sequence === requestSequence) error.value = requestError
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

onMounted(loadDashboard)
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

    <section class="dashboard-controls" aria-label="Filtros del Dashboard">
      <label for="dashboard-period">Periodo</label>
      <select id="dashboard-period" v-model="selectedPeriod" :disabled="loading" @change="loadDashboard">
        <option v-for="period in filterOptions?.periods ?? []" :key="period.value" :value="period.value">
          {{ period.label }} {{ period.year }}
        </option>
      </select>
      <template v-if="!USE_MOCKS">
        <label for="dashboard-channel">Canal</label>
        <select id="dashboard-channel" v-model="selectedChannel" :disabled="loading" @change="loadDashboard">
          <option value="">Todos los canales</option>
          <option v-for="type in filterOptions?.types ?? []" :key="type.value" :value="type.value">
            {{ type.label }}
          </option>
        </select>
      </template>
      <span v-if="periodLabel" class="dashboard-period-label">{{ periodLabel }}</span>
      <p v-if="selectedChannel" class="dashboard-filter-note">
        El canal se aplica a ventas; las alertas de cobro no se filtran por canal.
      </p>
    </section>

    <p v-if="USE_MOCKS" class="data-source-notice" role="note">Modo de demostración: datos simulados.</p>
    <p v-if="loading" class="dashboard-state" role="status" aria-live="polite">Cargando datos del Dashboard…</p>
    <div v-else-if="error" class="dashboard-state dashboard-state--error" role="alert">
      <p>{{ errorMessage }}</p>
      <button type="button" class="btn btn-primary" @click="loadDashboard">Reintentar</button>
    </div>
    <p v-else-if="!dashboardData || !dashboardData.hasMovements" class="dashboard-state" role="status">
      No hay movimientos disponibles para este periodo.
    </p>
    <template v-else>
    <section v-if="USE_MOCKS" class="section-quick-actions" aria-label="Acciones rápidas de caja">
      <QuickActions @open-modal="handleOpenModal" />
    </section>

    <section class="section-kpis" aria-label="Indicadores financieros clave del periodo">
      <div class="kpis-grid">
        <StatCard
          title="Saldo del periodo"
          :amount="dashboardData.kpis.balance"
          :subtitle="periodLabel"
          variant="balance"
          tooltip="Es el dinero líquido disponible tras restar los gastos a los ingresos cobrados."
        />

        <StatCard
          title="Entradas de caja"
          :amount="dashboardData.kpis.sales"
          subtitle="Ventas al contado y cobros del periodo"
          variant="income"
          tooltip="Suma total de todas las ventas que ya ingresaron a la caja."
        />

        <StatCard
          title="Gastos en insumos"
          :amount="dashboardData.kpis.expenses"
          subtitle="Salidas registradas en el periodo"
          variant="expense"
          tooltip="Monto de gastos en insumos devuelto por Backend."
        />

        <StatCard
          title="Cobros prioritarios"
          :amount="dashboardData.kpis.priorityCollections"
          :subtitle="`${numberFormatter.format(dashboardData.operationsSummary.priorityCollections)} alertas`"
          variant="pending"
          badge="Atención requerida"
          tooltip="Monto incluido en las alertas de cobro devueltas por Backend."
        />
      </div>
    </section>

    <section class="dashboard-grid" aria-label="Análisis principal de caja">
      <div class="dashboard-grid__wrapper dashboard-grid__chart">
        <CashChart
          class="dashboard-grid__card"
          :weeklyData="dashboardData.weeklyFlow"
          :subtitle="`Flujo de caja de ${periodLabel}`"
        />
      </div>
      <div class="dashboard-grid__wrapper dashboard-grid__collections">
        <PriorityCollections
          class="dashboard-grid__card"
          :collections="dashboardData.collections"
          :total-count="dashboardData.operationsSummary.priorityCollections"
          :allow-pay="USE_MOCKS"
          @pay-collection="handlePayCollection"
        />
      </div>
      <RecentOperations
        class="dashboard-grid__recent"
        :operations="dashboardData.recentOperations"
      />
      <div class="dashboard-grid__wrapper dashboard-grid__summary">
        <OperationsSummary
          class="dashboard-grid__card"
          :summary="{
            totalVentas: dashboardData.operationsSummary.sales,
            totalGastos: dashboardData.operationsSummary.expenses,
            unidadesVendidas: dashboardData.operationsSummary.units,
            cuentasPendientes: dashboardData.operationsSummary.priorityCollections
          }"
          :period-label="periodLabel"
        />
      </div>
      <div class="dashboard-grid__wrapper dashboard-grid__products">
        <TopProducts
          class="dashboard-grid__card"
          :products="dashboardData.topProducts"
          subtitle="Unidades vendidas en el periodo seleccionado"
        />
      </div>
    </section>
    </template>

    <NewOperationModal
      v-if="USE_MOCKS"
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
  min-width: 0;
  flex-direction: column;
  gap: var(--layout-section-gap);
  position: relative;
}

.dashboard-controls {
  display: flex;
  min-width: 0;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.dashboard-controls label {
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
  font-weight: 700;
}

.dashboard-controls select {
  min-height: var(--control-min-height);
  max-width: 100%;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
}

.dashboard-period-label {
  margin-left: auto;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  font-weight: 600;
}

.dashboard-filter-note {
  flex-basis: 100%;
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

.data-source-notice,
.dashboard-state {
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

.data-source-notice {
  font-size: 0.8125rem;
}

.dashboard-state--error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
  border-color: var(--color-danger, #b91c1c);
}

/* Toast */
.toast-notification {
  position: fixed;
  bottom: calc(var(--layout-bottom-nav-height) + var(--space-4));
  right: var(--layout-gutter-tablet);
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
  min-width: 0;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--layout-card-gap);
}

@media (min-width: 640px) {
  .kpis-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1280px) {
  .kpis-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.dashboard-grid {
  display: grid;
  min-width: 0;
  grid-template-columns: minmax(0, 1fr);
  grid-template-areas:
    "chart"
    "collections"
    "recent"
    "summary"
    "products";
  gap: var(--layout-card-gap);
  align-items: start;
}

.dashboard-grid__chart { grid-area: chart; }
.dashboard-grid__collections { grid-area: collections; }
.dashboard-grid__recent { grid-area: recent; }
.dashboard-grid__summary { grid-area: summary; }
.dashboard-grid__products { grid-area: products; }

.dashboard-grid__wrapper {
  display: flex;
  min-width: 0;
  height: auto;
}

.dashboard-grid__recent,
.dashboard-grid__card {
  width: 100%;
  height: auto;
}

@media (min-width: 1280px) {
  .dashboard-grid {
    grid-template-columns: minmax(0, 2fr) minmax(20rem, 1fr);
    grid-template-areas:
      "chart collections"
      "recent recent"
      "summary products";
    align-items: stretch;
  }

  .dashboard-grid__wrapper,
  .dashboard-grid__card {
    height: 100%;
  }
}

@media (max-width: 1279px) {
  .dashboard-grid {
    align-items: start;
  }

  .dashboard-grid__wrapper,
  .dashboard-grid__card {
    height: auto;
  }
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
    bottom: calc(var(--layout-bottom-nav-height) + var(--layout-control-gap));
    left: var(--layout-gutter-mobile);
    right: var(--layout-gutter-mobile);
  }
}
</style>
