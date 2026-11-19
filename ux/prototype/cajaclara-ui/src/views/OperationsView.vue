<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatCard from '@/components/common/StatCard.vue'
import OperationFormModal from '@/components/operations/OperationFormModal.vue'
import OperationDetailModal from '@/components/operations/OperationDetailModal.vue'
import { getDefaultOperationMonth, getOperationDetail, getOperations } from '@/services/operationsService'
import { formatCLP, formatDate, getLocalDateString } from '@/utils/formatters'

const route = useRoute()
const router = useRouter()
const activeFilter = ref('all')
const channelFilter = ref('')
const searchQuery = ref('')
const periodFilter = ref(getDefaultOperationMonth())
const sortOrder = ref('-fecha')
const currentPage = ref(1)
const pageSize = 10
const operationPage = ref({
  count: 0,
  page: 1,
  pageSize,
  hasNext: false,
  hasPrevious: false,
  summary: { salesAmount: 0, expensesAmount: 0, totalCount: 0, pendingSalesAmount: 0 },
  results: []
})
const isLoading = ref(false)
const loadError = ref('')
const isFormOpen = ref(false)
const formMode = ref('venta')
const selectedOperation = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
const toastMessage = ref('')
const showToast = ref(false)
let toastTimeout
let loadTimeout
let loadSequence = 0
let detailSequence = 0

const tabs = [
  { id: 'all', label: 'Todas' },
  { id: 'venta', label: 'Ventas' },
  { id: 'gasto', label: 'Gastos en insumos' },
  { id: 'pendiente', label: 'Pendientes de pago' }
]

const summary = computed(() => operationPage.value.summary)
const filteredOperations = computed(() => operationPage.value.results.map((operation) => ({
  ...operation,
  displayStatus: operation.type === 'Venta' &&
    operation.paymentStatus === 'Pendiente' &&
    operation.paymentDueDate &&
    operation.paymentDueDate < getLocalDateString()
    ? 'Vencida'
    : operation.paymentStatus
})))
const totalPages = computed(() => Math.max(1, Math.ceil(operationPage.value.count / pageSize)))

async function loadOperations() {
  const requestSequence = ++loadSequence
  isLoading.value = true
  loadError.value = ''
  try {
    const result = await getOperations({
      month: periodFilter.value,
      type: ['venta', 'gasto'].includes(activeFilter.value) ? activeFilter.value : 'all',
      status: activeFilter.value === 'pendiente' ? 'pendiente' : '',
      channel: channelFilter.value,
      search: searchQuery.value,
      ordering: sortOrder.value,
      page: currentPage.value,
      pageSize
    })
    if (requestSequence !== loadSequence) return false
    operationPage.value = result
    return true
  } catch (error) {
    if (requestSequence === loadSequence) {
      loadError.value = error instanceof Error ? error.message : 'No se pudieron cargar las operaciones.'
    }
    return false
  } finally {
    if (requestSequence === loadSequence) isLoading.value = false
  }
}

function scheduleLoad(delay = 0) {
  window.clearTimeout(loadTimeout)
  loadTimeout = window.setTimeout(loadOperations, delay)
}

watch([activeFilter, channelFilter, periodFilter, sortOrder], () => {
  currentPage.value = 1
  scheduleLoad()
})
watch(searchQuery, () => {
  currentPage.value = 1
  scheduleLoad(250)
})
watch(currentPage, () => scheduleLoad())
scheduleLoad()

const openForm = (mode = 'venta') => {
  formMode.value = mode
  isFormOpen.value = true
}

const clearNewOperationQuery = () => {
  if (!route.query.nueva) return
  const query = { ...route.query }
  delete query.nueva
  router.replace({ path: route.path, query })
}

const closeForm = () => {
  isFormOpen.value = false
  clearNewOperationQuery()
}

watch(() => route.query.nueva, (value) => {
  if (value === 'venta' || value === 'venta-pendiente' || value === 'gasto') {
    openForm(value)
  }
}, { immediate: true })

function notify(message) {
  toastMessage.value = message
  showToast.value = true
  window.clearTimeout(toastTimeout)
  toastTimeout = window.setTimeout(() => {
    showToast.value = false
  }, 3500)
}

async function handleOperationSaved({ type }) {
  const refreshed = await loadOperations()
  notify(refreshed
    ? type === 'sale' ? 'Venta registrada correctamente.' : 'Gasto registrado correctamente.'
    : 'La operación se guardó, pero no se pudo actualizar el listado. Reintenta la carga.')
}

async function openOperationDetail(operation) {
  selectedOperation.value = operation
  detailError.value = ''
  detailLoading.value = true
  const requestSequence = ++detailSequence
  try {
    const detail = await getOperationDetail(operation)
    if (requestSequence === detailSequence) selectedOperation.value = detail
  } catch (error) {
    if (requestSequence === detailSequence) {
      detailError.value = error instanceof Error ? error.message : 'No se pudo cargar el detalle.'
    }
  } finally {
    if (requestSequence === detailSequence) detailLoading.value = false
  }
}

function closeOperationDetail() {
  detailSequence += 1
  selectedOperation.value = null
  detailError.value = ''
  detailLoading.value = false
}

function retryOperationDetail() {
  if (selectedOperation.value) openOperationDetail(selectedOperation.value)
}

onBeforeUnmount(() => {
  window.clearTimeout(loadTimeout)
  window.clearTimeout(toastTimeout)
  loadSequence += 1
  detailSequence += 1
})
</script>

<template>
  <div class="operations-view">
    <div v-if="showToast" class="operations-toast" role="status" aria-live="polite">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg>
      <span>{{ toastMessage }}</span>
    </div>

    <header class="page-heading">
      <div class="page-heading__copy">
        <span class="page-eyebrow">Almacén La Esquina</span>
        <h1>Compras y ventas</h1>
        <p>Consulta y registra las entradas y salidas de dinero de tu negocio.</p>
      </div>
      <div class="page-heading__actions">
        <label class="period-control">
          <span>Periodo</span>
          <input
            v-model="periodFilter"
            type="month"
            required
            aria-label="Periodo de operaciones"
            @change="periodFilter = $event.target.value || getDefaultOperationMonth()"
          />
        </label>
        <button type="button" class="btn btn-primary action-button" @click="openForm('venta')">
          <span aria-hidden="true">＋</span> Nueva venta
        </button>
        <button type="button" class="btn btn-secondary action-button" @click="openForm('gasto')">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>
          Registrar gasto
        </button>
      </div>
    </header>

    <section class="summary-grid" aria-label="Resumen de operaciones del periodo">
      <StatCard title="Ventas del periodo" :amount="summary.salesAmount" subtitle="Ventas registradas, pagadas o pendientes" variant="income" />
      <StatCard title="Gastos en insumos" :amount="summary.expensesAmount" subtitle="Salidas registradas en el periodo" variant="expense" />
      <StatCard title="Operaciones registradas" :amount="summary.totalCount" subtitle="Ventas y gastos del periodo" variant="balance" :format-as-currency="false" />
      <StatCard title="Ventas pendientes de pago" :amount="summary.pendingSalesAmount" subtitle="Incluye cuentas vencidas" variant="pending" />
    </section>

    <section class="operations-panel" aria-labelledby="operations-list-title">
      <div class="operations-panel__header">
        <div>
          <span class="page-eyebrow">Actividad del negocio</span>
          <h2 id="operations-list-title">Listado de operaciones</h2>
        </div>
        <span class="result-count">{{ operationPage.count }} {{ operationPage.count === 1 ? 'resultado' : 'resultados' }}</span>
      </div>

      <div class="filter-tabs" role="tablist" aria-label="Filtrar operaciones por tipo">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          role="tab"
          :aria-selected="activeFilter === tab.id"
          :class="{ 'is-active': activeFilter === tab.id }"
          @click="activeFilter = tab.id"
        >{{ tab.label }}</button>
      </div>

      <div class="filter-controls">
        <label class="search-control">
          <span class="sr-only">Buscar por cliente, producto o factura</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
          <input
            v-model="searchQuery"
            type="search"
            aria-label="Buscar por cliente, producto o factura"
            placeholder="Cliente, producto o factura"
          />
        </label>
        <label class="select-control">
          <span>Canal</span>
          <select v-model="channelFilter">
            <option value="">Todos los canales</option>
            <option value="Física">Física</option>
            <option value="En Línea">En Línea</option>
          </select>
        </label>
        <label class="select-control">
          <span>Ordenar por</span>
          <select v-model="sortOrder">
            <option value="-fecha">Fecha más reciente</option>
            <option value="fecha">Fecha más antigua</option>
            <option value="-monto">Mayor monto</option>
            <option value="monto">Menor monto</option>
          </select>
        </label>
      </div>

      <p v-if="isLoading" class="list-status" role="status">Cargando operaciones…</p>
      <div v-if="loadError" class="list-error" role="alert">
        <span>{{ loadError }}</span>
        <button type="button" class="text-action" @click="loadOperations">Reintentar</button>
      </div>

      <div v-if="filteredOperations.length && !loadError" class="operations-table-wrap">
        <table class="operations-table">
          <caption class="sr-only">Operaciones del negocio con fecha, contraparte, detalle, canal, monto, estado y acciones</caption>
          <thead>
            <tr>
              <th scope="col">Fecha</th>
              <th scope="col">Operación</th>
              <th scope="col">Cliente o producto</th>
              <th scope="col">Detalle</th>
              <th scope="col">Canal</th>
              <th scope="col" class="amount-heading">Monto</th>
              <th scope="col">Estado</th>
              <th scope="col"><span class="sr-only">Acciones</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="operation in filteredOperations" :key="operation.id">
              <td class="date-cell">
                {{ formatDate(operation.date) }}
                <small v-if="operation.time">{{ operation.time }}</small>
              </td>
              <td>
                <span :class="['operation-type', operation.type === 'Venta' ? 'type-sale' : 'type-expense']">
                  <svg v-if="operation.type === 'Venta'" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M7 7h10v10" /></svg>
                  <svg v-else viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>
                  {{ operation.type }}
                </span>
              </td>
              <td class="party-cell">{{ operation.customerOrSupplier || 'No informado' }}</td>
              <td class="detail-cell">
                <strong>{{ operation.description }}</strong>
                <small>{{ operation.invoiceId }}</small>
              </td>
              <td>{{ operation.channel === '—' ? 'No aplica' : operation.channel }}</td>
              <td :class="['amount-cell', operation.type === 'Venta' ? 'amount-income' : 'amount-expense']">
                {{ operation.type === 'Venta' ? '+' : '−' }}{{ formatCLP(operation.amount) }}
              </td>
              <td>
                <span :class="['status-badge', `status-${operation.displayStatus.toLocaleLowerCase('es-CL').replace('á', 'a')}`]">
                  <svg v-if="operation.displayStatus === 'Pagada'" viewBox="0 0 20 20" aria-hidden="true"><path d="m4 10 4 4 8-8" /></svg>
                  <svg v-else-if="operation.displayStatus === 'Vencida'" viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v7m0 4h.01M3 17h14L10 3 3 17Z" /></svg>
                  <svg v-else-if="operation.displayStatus === 'Pendiente'" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7" /><path d="M10 6v4l3 2" /></svg>
                  <svg v-else viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3h7l4 4v10H5zM12 3v5h4" /></svg>
                  {{ operation.displayStatus }}
                </span>
              </td>
              <td>
                <div class="row-actions">
                  <button type="button" aria-label="Ver detalle" @click="openOperationDetail(operation)">Ver</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="filteredOperations.length && !loadError" class="operation-cards">
        <article v-for="operation in filteredOperations" :key="operation.id" class="operation-card">
          <div class="operation-card__top">
            <span :class="['operation-type', operation.type === 'Venta' ? 'type-sale' : 'type-expense']">{{ operation.type }}</span>
            <span :class="['status-badge', `status-${operation.displayStatus.toLocaleLowerCase('es-CL').replace('á', 'a')}`]">
              <span aria-hidden="true">{{ operation.displayStatus === 'Pagada' ? '✓' : operation.displayStatus === 'Vencida' ? '!' : '◷' }}</span>
              {{ operation.displayStatus }}
            </span>
          </div>
          <div class="operation-card__heading">
            <div>
              <h3>{{ operation.description }}</h3>
              <p>{{ operation.invoiceId }} · {{ formatDate(operation.date) }}<template v-if="operation.time">, {{ operation.time }}</template></p>
            </div>
            <strong :class="operation.type === 'Venta' ? 'amount-income' : 'amount-expense'">
              {{ operation.type === 'Venta' ? '+' : '−' }}{{ formatCLP(operation.amount) }}
            </strong>
          </div>
          <dl class="operation-card__meta">
            <div><dt>Cliente o producto</dt><dd>{{ operation.customerOrSupplier || 'No informado' }}</dd></div>
            <div><dt>Canal</dt><dd>{{ operation.channel === '—' ? 'No aplica' : operation.channel }}</dd></div>
          </dl>
          <div class="operation-card__actions">
            <button type="button" @click="openOperationDetail(operation)">Ver detalle</button>
          </div>
        </article>
      </div>

      <nav v-if="operationPage.count > pageSize && !loadError" class="pagination" aria-label="Paginación de operaciones">
        <button type="button" class="btn btn-secondary" :disabled="!operationPage.hasPrevious || isLoading" @click="currentPage -= 1">
          Anterior
        </button>
        <span aria-live="polite">Página {{ currentPage }} de {{ totalPages }}</span>
        <button type="button" class="btn btn-secondary" :disabled="!operationPage.hasNext || isLoading" @click="currentPage += 1">
          Siguiente
        </button>
      </nav>

      <div v-if="!isLoading && !loadError && !filteredOperations.length" class="empty-state" role="status">
        <span class="empty-state__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM8 9h8m-8 4h5" /></svg>
        </span>
        <p>{{ searchQuery.trim() ? 'No encontramos operaciones que coincidan con tu búsqueda.' : 'No hay operaciones para los filtros seleccionados.' }}</p>
        <button v-if="searchQuery" type="button" class="text-action" @click="searchQuery = ''">Limpiar búsqueda</button>
      </div>
    </section>

    <OperationFormModal
      :is-open="isFormOpen"
      :initial-mode="formMode"
      @close="closeForm"
      @saved="handleOperationSaved"
    />
    <OperationDetailModal
      :is-open="Boolean(selectedOperation)"
      :operation="selectedOperation"
      :is-loading="detailLoading"
      :error="detailError"
      @close="closeOperationDetail"
      @retry="retryOperationDetail"
    />
  </div>
</template>

<style scoped>
.operations-view { display: flex; min-width: var(--content-min-width); flex-direction: column; gap: var(--layout-section-gap); }
.page-heading { display: flex; min-width: var(--content-min-width); align-items: flex-end; justify-content: space-between; gap: var(--layout-card-gap); }
.page-heading__copy { min-width: 0; }
.page-eyebrow { color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.page-heading h1 { margin: 4px 0 6px; color: var(--color-text); font-size: clamp(1.65rem, 3vw, 2rem); font-weight: 800; letter-spacing: -.04em; line-height: 1.15; }
.page-heading p { max-width: 560px; color: var(--color-text-secondary); font-size: .95rem; }
.page-heading__actions { display: flex; min-width: var(--content-min-width); flex-wrap: wrap; align-items: flex-end; justify-content: flex-end; gap: var(--layout-control-gap); }
.period-control, .select-control { display: flex; min-width: 0; flex: 1 1 10rem; flex-direction: column; gap: var(--space-1); color: var(--color-text-secondary); font-size: .7rem; font-weight: 700; }
.period-control input, .period-control select, .select-control select { width: 100%; max-width: 100%; min-width: 0; min-height: var(--control-min-height); padding: 8px 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); color: var(--color-text); font: inherit; font-size: .8rem; }
.action-button { min-width: 0; min-height: var(--control-min-height); }
.action-button svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
.summary-grid { display: grid; min-width: var(--content-min-width); grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--layout-control-gap); }
.operations-panel { min-width: var(--content-min-width); padding: var(--space-6); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface); box-shadow: var(--shadow-card); }
.operations-panel__header { display: flex; min-width: var(--content-min-width); align-items: center; justify-content: space-between; gap: var(--layout-control-gap); }
.operations-panel__header > div { min-width: var(--content-min-width); }
.operations-panel__header h2 { margin-top: 3px; color: var(--color-text); font-size: 1.15rem; }
.result-count { color: var(--color-text-secondary); font-size: .8rem; font-weight: 700; }
.filter-tabs { display: flex; min-width: var(--content-min-width); gap: var(--space-1); margin: var(--space-4) 0; overflow-x: auto; border-bottom: 1px solid var(--color-border); }
.filter-tabs button { position: relative; min-width: 0; min-height: var(--control-min-height); padding: 8px var(--layout-control-gap); color: var(--color-text-secondary); font-size: .82rem; font-weight: 700; white-space: nowrap; }
.filter-tabs button.is-active { color: var(--color-brand-primary); }
.filter-tabs button.is-active::after { position: absolute; right: 10px; bottom: -1px; left: 10px; height: 3px; border-radius: 3px 3px 0 0; background: var(--color-brand-primary); content: ''; }
.filter-controls { display: grid; min-width: var(--content-min-width); grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1fr); gap: var(--layout-control-gap); margin-bottom: var(--space-4); }
.search-control { display: flex; min-width: var(--content-min-width); min-height: var(--control-min-height); align-items: center; gap: var(--space-2); padding: 0 var(--layout-control-gap); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); }
.search-control svg { width: 18px; height: 18px; flex: 0 0 18px; fill: none; stroke: var(--color-text-muted); stroke-width: 1.8; stroke-linecap: round; }
.search-control input { width: 100%; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--color-text); font: inherit; font-size: .82rem; }
.select-control { min-width: 0; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
.operations-table-wrap { width: 100%; max-width: 100%; min-width: var(--content-min-width); overflow-x: auto; }
.operations-table { width: 100%; border-collapse: collapse; table-layout: auto; }
.operations-table th { padding: 12px 10px; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); font-size: .68rem; font-weight: 800; letter-spacing: .04em; text-align: left; text-transform: uppercase; white-space: nowrap; }
.operations-table td { max-width: 250px; padding: 14px 10px; border-bottom: 1px solid var(--color-border-subtle); color: var(--color-text); font-size: .78rem; vertical-align: middle; }
.operations-table tbody tr:last-child td { border-bottom: 0; }
.date-cell, .detail-cell, .party-cell { overflow-wrap: anywhere; }
.date-cell { white-space: nowrap; }
.date-cell small, .detail-cell small { display: block; margin-top: 3px; color: var(--color-text-secondary); font-size: .7rem; }
.detail-cell strong { display: block; font-size: .77rem; }
.operation-type { display: inline-flex; min-width: 0; align-items: center; gap: var(--space-1); font-size: .76rem; font-weight: 700; white-space: nowrap; }
.operation-type svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.type-sale, .amount-income { color: var(--color-emerald-700); }
.type-expense, .amount-expense { color: #b4233b; }
.amount-cell { font-weight: 800; white-space: nowrap; }
.amount-heading { text-align: right !important; }
.status-badge { display: inline-flex; min-height: 27px; align-items: center; gap: 5px; padding: 4px 8px; border: 1px solid transparent; border-radius: var(--radius-pill); font-size: .68rem; font-weight: 800; white-space: nowrap; }
.status-badge svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.status-pagada { color: #047857; background: #ecfdf5; border-color: #a7f3d0; }
.status-pendiente { color: #92400e; background: #fffbeb; border-color: #fde68a; }
.status-vencida { color: #b91c1c; background: #fef2f2; border-color: #fecaca; }
.status-registrada { color: #475569; background: #f1f5f9; border-color: #cbd5e1; }
.row-actions { display: flex; flex-wrap: wrap; gap: 4px; }
.row-actions button { min-height: 36px; padding: 5px 7px; border-radius: 6px; color: var(--color-brand-primary); font-size: .69rem; font-weight: 800; white-space: nowrap; }
.row-actions button:hover { background: var(--color-brand-primary-light); }
.row-actions .pay-action { color: #92400e; }
.operation-cards { display: none; }
.empty-state { display: flex; min-height: 260px; flex-direction: column; align-items: center; justify-content: center; gap: 12px; padding: 24px; text-align: center; }
.empty-state p { max-width: 380px; color: var(--color-text-secondary); font-size: .9rem; }
.empty-state__icon { display: grid; width: 52px; height: 52px; place-items: center; border-radius: 50%; background: var(--color-brand-primary-light); color: var(--color-brand-primary); }
.empty-state__icon svg { width: 25px; height: 25px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.list-status, .list-error { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: var(--layout-control-gap); padding: var(--layout-card-gap); border-radius: var(--radius-md); background: var(--color-bg-subtle); color: var(--color-text-secondary); font-size: .88rem; }
.list-error { background: #fef2f2; color: #991b1b; }
.pagination { display: flex; align-items: center; justify-content: center; gap: var(--layout-control-gap); margin-top: var(--layout-card-gap); color: var(--color-text-secondary); font-size: .84rem; }
.pagination .btn { min-height: var(--control-min-height); }
.operations-toast { position: fixed; right: var(--layout-gutter-tablet); bottom: var(--layout-control-gap); z-index: 1200; display: flex; min-width: var(--content-min-width); align-items: center; gap: var(--layout-control-gap); max-width: min(27.5rem, calc(100vw - var(--space-8))); padding: var(--layout-control-gap) var(--layout-card-gap); border: 1px solid #a7f3d0; border-radius: var(--radius-md); background: #ecfdf5; color: #065f46; box-shadow: var(--shadow-lg); font-size: .86rem; font-weight: 700; }
.operations-toast svg { width: 20px; height: 20px; flex: 0 0 20px; fill: none; stroke: currentColor; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
@media (max-width: 1200px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .page-heading { align-items: flex-start; flex-direction: column; }
  .page-heading__actions { width: 100%; justify-content: flex-start; }
  .operations-table-wrap { display: none; }
  .operation-cards { display: grid; gap: var(--layout-control-gap); }
  .operation-card { min-width: var(--content-min-width); padding: var(--layout-control-gap); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
  .operation-card__top, .operation-card__heading { display: flex; min-width: var(--content-min-width); align-items: flex-start; justify-content: space-between; gap: var(--layout-control-gap); }
  .operation-card__heading { margin-top: var(--layout-control-gap); }
  .operation-card__heading h3 { font-size: .9rem; overflow-wrap: anywhere; }
  .operation-card__heading p { margin-top: 4px; color: var(--color-text-secondary); font-size: .72rem; }
  .operation-card__heading > strong { flex: 0 0 auto; font-size: .85rem; white-space: nowrap; }
  .operation-card__meta { display: grid; min-width: var(--content-min-width); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--layout-control-gap); margin-top: var(--layout-control-gap); padding-top: var(--layout-control-gap); border-top: 1px solid var(--color-border-subtle); }
  .operation-card__meta dt { color: var(--color-text-secondary); font-size: .68rem; }
  .operation-card__meta dd { margin-top: 2px; color: var(--color-text); font-size: .76rem; font-weight: 700; overflow-wrap: anywhere; }
  .operation-card__actions { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--layout-control-gap); padding-top: var(--space-2); border-top: 1px solid var(--color-border-subtle); }
  .operation-card__actions button { min-height: var(--control-min-height); padding: var(--space-2) var(--layout-control-gap); border-radius: 7px; color: var(--color-brand-primary); font-size: .74rem; font-weight: 800; }
  .operation-card__actions button:hover { background: var(--color-brand-primary-light); }
}
@media (max-width: 760px) {
  .operations-view { gap: var(--layout-card-gap); }
  .page-heading__actions { flex-wrap: wrap; }
  .page-heading__actions .period-control { flex-basis: 100%; }
  .page-heading__actions .action-button { flex: 1 1 170px; }
  .filter-controls { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .search-control { grid-column: 1 / -1; }
  .operations-panel { padding: var(--space-4); }
}
@media (max-width: 520px) {
  .summary-grid { grid-template-columns: 1fr; gap: 12px; }
  .operations-panel { padding: var(--layout-control-gap); }
  .operations-panel__header { align-items: flex-start; flex-direction: column; gap: 6px; }
  .filter-tabs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: var(--layout-control-gap) 0; overflow: visible; }
  .filter-tabs button { padding: 8px 9px; font-size: .76rem; white-space: normal; }
  .filter-controls { grid-template-columns: 1fr; }
  .search-control { grid-column: auto; }
  .page-heading__actions .action-button { flex: 1 1 100%; }
  .operation-card { padding: 14px; }
  .operation-card__heading { flex-direction: column; }
  .operation-card__heading > strong { align-self: flex-start; }
  .operation-card__meta { grid-template-columns: 1fr; }
  .operation-card__actions button { flex: 1 1 auto; }
  .operations-toast { right: var(--layout-gutter-mobile); bottom: calc(var(--layout-bottom-nav-height) + var(--layout-control-gap)); left: var(--layout-gutter-mobile); max-width: none; }
  .pagination { flex-wrap: wrap; }
}
</style>
