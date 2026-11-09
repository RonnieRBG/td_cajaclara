<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StatCard from '@/components/common/StatCard.vue'
import NewOperationModal from '@/components/dashboard/NewOperationModal.vue'
import OperationDetailModal from '@/components/operations/OperationDetailModal.vue'
import { operations as mockOperations } from '@/data/operationsMock'
import { formatCLP, formatDate, getLocalDateString } from '@/utils/formatters'

const route = useRoute()
const router = useRouter()
const localOperations = ref(mockOperations.map(operation => ({
  ...operation,
  products: operation.products.map(product => ({ ...product }))
})))
const activeFilter = ref('todas')
const searchQuery = ref('')
const periodFilter = ref('2026-10')
const sortOrder = ref('recent')
const isFormOpen = ref(false)
const formMode = ref('venta')
const selectedOperation = ref(null)
const toastMessage = ref('')
const showToast = ref(false)
let toastTimeout

const tabs = [
  { id: 'todas', label: 'Todas' },
  { id: 'ventas', label: 'Ventas' },
  { id: 'gastos', label: 'Compras y gastos' },
  { id: 'pendientes', label: 'Pendientes de pago' }
]

const periodOptions = computed(() => {
  const currentMonth = getLocalDateString().slice(0, 7)
  const periods = new Set(['2026-10', currentMonth, ...localOperations.value.map(operation => operation.date.slice(0, 7))])
  return [...periods].sort((a, b) => b.localeCompare(a)).map(value => ({
    value,
    label: new Date(`${value}-01T12:00:00`).toLocaleDateString('es-CL', { month: 'long', year: 'numeric' })
      .replace(/^\p{L}/u, letter => letter.toLocaleUpperCase('es-CL'))
  }))
})

const getPaymentStatus = (operation) => {
  if (operation.paymentStatus === 'Vencida') return 'Vencida'
  if (
    operation.type === 'Venta' &&
    operation.paymentStatus === 'Pendiente' &&
    operation.paymentDueDate &&
    operation.paymentDueDate < getLocalDateString()
  ) return 'Vencida'
  return operation.paymentStatus
}

const periodOperations = computed(() => localOperations.value.filter(operation => (
  periodFilter.value === 'all' || operation.date.startsWith(periodFilter.value)
)))

const summary = computed(() => {
  const sales = periodOperations.value.filter(operation => operation.type === 'Venta')
  const expenses = periodOperations.value.filter(operation => operation.type === 'Compra' || operation.type === 'Otro gasto')
  const pendingSales = sales.filter(operation => ['Pendiente', 'Vencida'].includes(getPaymentStatus(operation)))
  return {
    sales: sales.reduce((total, operation) => total + Number(operation.amount || 0), 0),
    expenses: expenses.reduce((total, operation) => total + Number(operation.amount || 0), 0),
    count: periodOperations.value.length,
    pending: pendingSales.reduce((total, operation) => total + Number(operation.amount || 0), 0)
  }
})

const filteredOperations = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase('es-CL')
  return periodOperations.value
    .filter(operation => {
      if (activeFilter.value === 'ventas' && operation.type !== 'Venta') return false
      if (activeFilter.value === 'gastos' && operation.type === 'Venta') return false
      if (activeFilter.value === 'pendientes' && !['Pendiente', 'Vencida'].includes(getPaymentStatus(operation))) return false
      if (!query) return true
      const searchableText = [
        operation.invoiceId,
        operation.description,
        operation.customerOrSupplier,
        operation.type,
        ...operation.products.map(product => product.name)
      ].join(' ').toLocaleLowerCase('es-CL')
      return searchableText.includes(query)
    })
    .sort((a, b) => {
      const dateComparison = `${a.date} ${a.time || ''}`.localeCompare(`${b.date} ${b.time || ''}`)
      return sortOrder.value === 'recent' ? -dateComparison : dateComparison
    })
    .map(operation => ({ ...operation, displayStatus: getPaymentStatus(operation) }))
})

const syncPeriodSelectors = (value) => {
  periodFilter.value = value
}

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

const notify = (message) => {
  toastMessage.value = message
  showToast.value = true
  window.clearTimeout(toastTimeout)
  toastTimeout = window.setTimeout(() => {
    showToast.value = false
  }, 3500)
}

const handleSaveOperation = (operation) => {
  const nextNumber = String(localOperations.value.length + 1).padStart(4, '0')
  const prefix = operation.type === 'Venta'
    ? operation.paymentStatus === 'Pendiente' ? 'INV' : 'VTA'
    : operation.type === 'Compra' ? 'CMP' : 'GST'
  const savedOperation = {
    ...operation,
    id: `op-local-${Date.now()}`,
    invoiceId: `${prefix}-${nextNumber}`,
    time: new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', hour12: false }),
    products: operation.products.map(product => ({ ...product }))
  }
  localOperations.value = [savedOperation, ...localOperations.value]
  periodFilter.value = savedOperation.date.slice(0, 7)
  closeForm()
  notify('Operación registrada correctamente.')
}

const simulateEdit = () => notify('La edición de operaciones es una simulación del prototipo.')

const registerPayment = (operation) => {
  localOperations.value = localOperations.value.map(item => item.id === operation.id
    ? { ...item, paymentStatus: 'Pagada', paymentDueDate: null }
    : item)
  notify('Pago registrado correctamente.')
}
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
          <select :value="periodFilter" aria-label="Periodo de operaciones" @change="syncPeriodSelectors($event.target.value)">
            <option value="all">Todos los periodos</option>
            <option v-for="period in periodOptions" :key="period.value" :value="period.value">{{ period.label }}</option>
          </select>
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
      <StatCard title="Ventas del periodo" :amount="summary.sales" subtitle="Ventas registradas, pagadas o pendientes" variant="income" />
      <StatCard title="Compras y gastos" :amount="summary.expenses" subtitle="Salidas registradas en el periodo" variant="expense" />
      <StatCard title="Operaciones registradas" :amount="summary.count" subtitle="Ventas, compras y otros gastos" variant="balance" :format-as-currency="false" />
      <StatCard title="Ventas pendientes de pago" :amount="summary.pending" subtitle="Incluye cuentas vencidas" variant="pending" />
    </section>

    <section class="operations-panel" aria-labelledby="operations-list-title">
      <div class="operations-panel__header">
        <div>
          <span class="page-eyebrow">Actividad del negocio</span>
          <h2 id="operations-list-title">Listado de operaciones</h2>
        </div>
        <span class="result-count">{{ filteredOperations.length }} {{ filteredOperations.length === 1 ? 'resultado' : 'resultados' }}</span>
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
          <span class="sr-only">Buscar por producto, cliente, descripción o factura</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
          <input
            v-model="searchQuery"
            type="search"
            aria-label="Buscar por producto, cliente, descripción o factura"
            placeholder="Producto, cliente, descripción o factura"
          />
        </label>
        <label class="select-control">
          <span>Periodo</span>
          <select :value="periodFilter" @change="syncPeriodSelectors($event.target.value)">
            <option value="all">Todos los periodos</option>
            <option v-for="period in periodOptions" :key="period.value" :value="period.value">{{ period.label }}</option>
          </select>
        </label>
        <label class="select-control">
          <span>Ordenar por</span>
          <select v-model="sortOrder">
            <option value="recent">Fecha más reciente</option>
            <option value="oldest">Fecha más antigua</option>
          </select>
        </label>
      </div>

      <div v-if="filteredOperations.length" class="operations-table-wrap">
        <table class="operations-table">
          <caption class="sr-only">Operaciones del negocio con fecha, contraparte, detalle, canal, monto, estado y acciones</caption>
          <thead>
            <tr>
              <th scope="col">Fecha</th>
              <th scope="col">Operación</th>
              <th scope="col">Cliente o proveedor</th>
              <th scope="col">Detalle</th>
              <th scope="col">Canal</th>
              <th scope="col" class="amount-heading">Monto</th>
              <th scope="col">Estado</th>
              <th scope="col"><span class="sr-only">Acciones</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="operation in filteredOperations" :key="operation.id">
              <td class="date-cell">{{ formatDate(operation.date) }}<small>{{ operation.time }}</small></td>
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
                  <button type="button" aria-label="Ver detalle" @click="selectedOperation = operation">Ver</button>
                  <button type="button" aria-label="Editar (simulación)" @click="simulateEdit">Editar</button>
                  <button
                    v-if="operation.type === 'Venta' && ['Pendiente', 'Vencida'].includes(operation.displayStatus)"
                    type="button"
                    class="pay-action"
                    @click="registerPayment(operation)"
                  >Registrar pago</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="filteredOperations.length" class="operation-cards">
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
            <div><dt>Cliente o proveedor</dt><dd>{{ operation.customerOrSupplier || 'No informado' }}</dd></div>
            <div><dt>Canal</dt><dd>{{ operation.channel === '—' ? 'No aplica' : operation.channel }}</dd></div>
          </dl>
          <div class="operation-card__actions">
            <button type="button" @click="selectedOperation = operation">Ver detalle</button>
            <button type="button" @click="simulateEdit">Editar</button>
            <button
              v-if="operation.type === 'Venta' && ['Pendiente', 'Vencida'].includes(operation.displayStatus)"
              type="button"
              @click="registerPayment(operation)"
            >Registrar pago</button>
          </div>
        </article>
      </div>

      <div v-if="!filteredOperations.length" class="empty-state" role="status">
        <span class="empty-state__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM8 9h8m-8 4h5" /></svg>
        </span>
        <p>{{ searchQuery.trim() ? 'No encontramos operaciones que coincidan con tu búsqueda.' : 'No hay operaciones para los filtros seleccionados.' }}</p>
        <button v-if="searchQuery" type="button" class="text-action" @click="searchQuery = ''">Limpiar búsqueda</button>
      </div>
    </section>

    <NewOperationModal :is-open="isFormOpen" :initial-mode="formMode" @close="closeForm" @save="handleSaveOperation" />
    <OperationDetailModal :is-open="Boolean(selectedOperation)" :operation="selectedOperation" @close="selectedOperation = null" />
  </div>
</template>

<style scoped>
.operations-view { display: flex; min-width: 0; flex-direction: column; gap: 24px; }
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; }
.page-heading__copy { min-width: 0; }
.page-eyebrow { color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.page-heading h1 { margin: 4px 0 6px; color: var(--color-text); font-size: clamp(1.65rem, 3vw, 2rem); font-weight: 800; letter-spacing: -.04em; line-height: 1.15; }
.page-heading p { max-width: 560px; color: var(--color-text-secondary); font-size: .95rem; }
.page-heading__actions { display: flex; align-items: flex-end; justify-content: flex-end; gap: 10px; }
.period-control, .select-control { display: flex; min-width: 166px; flex-direction: column; gap: 5px; color: var(--color-text-secondary); font-size: .7rem; font-weight: 700; }
.period-control select, .select-control select { min-height: 44px; padding: 8px 30px 8px 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); color: var(--color-text); font: inherit; font-size: .8rem; }
.action-button { min-height: 44px; }
.action-button svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.operations-panel { min-width: 0; padding: 24px; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface); box-shadow: var(--shadow-card); }
.operations-panel__header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.operations-panel__header h2 { margin-top: 3px; color: var(--color-text); font-size: 1.15rem; }
.result-count { color: var(--color-text-secondary); font-size: .8rem; font-weight: 700; }
.filter-tabs { display: flex; gap: 6px; margin: 18px 0; overflow-x: auto; border-bottom: 1px solid var(--color-border); }
.filter-tabs button { position: relative; min-height: 44px; padding: 8px 12px; color: var(--color-text-secondary); font-size: .82rem; font-weight: 700; white-space: nowrap; }
.filter-tabs button.is-active { color: var(--color-brand-primary); }
.filter-tabs button.is-active::after { position: absolute; right: 10px; bottom: -1px; left: 10px; height: 3px; border-radius: 3px 3px 0 0; background: var(--color-brand-primary); content: ''; }
.filter-controls { display: grid; grid-template-columns: minmax(240px, 2fr) minmax(165px, 1fr) minmax(165px, 1fr); gap: 12px; margin-bottom: 18px; }
.search-control { display: flex; min-width: 0; min-height: 44px; align-items: center; gap: 9px; padding: 0 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); }
.search-control svg { width: 18px; height: 18px; flex: 0 0 18px; fill: none; stroke: var(--color-text-muted); stroke-width: 1.8; stroke-linecap: round; }
.search-control input { width: 100%; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--color-text); font: inherit; font-size: .82rem; }
.select-control { min-width: 0; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
.operations-table-wrap { width: 100%; overflow-x: auto; }
.operations-table { width: 100%; border-collapse: collapse; table-layout: auto; }
.operations-table th { padding: 12px 10px; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); font-size: .68rem; font-weight: 800; letter-spacing: .04em; text-align: left; text-transform: uppercase; white-space: nowrap; }
.operations-table td { max-width: 250px; padding: 14px 10px; border-bottom: 1px solid var(--color-border-subtle); color: var(--color-text); font-size: .78rem; vertical-align: middle; }
.operations-table tbody tr:last-child td { border-bottom: 0; }
.date-cell, .detail-cell, .party-cell { overflow-wrap: anywhere; }
.date-cell { white-space: nowrap; }
.date-cell small, .detail-cell small { display: block; margin-top: 3px; color: var(--color-text-secondary); font-size: .7rem; }
.detail-cell strong { display: block; font-size: .77rem; }
.operation-type { display: inline-flex; align-items: center; gap: 6px; font-size: .76rem; font-weight: 700; white-space: nowrap; }
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
.operations-toast { position: fixed; right: 24px; bottom: 24px; z-index: 1200; display: flex; align-items: center; gap: 10px; max-width: min(440px, calc(100vw - 32px)); padding: 14px 18px; border: 1px solid #a7f3d0; border-radius: var(--radius-md); background: #ecfdf5; color: #065f46; box-shadow: var(--shadow-lg); font-size: .86rem; font-weight: 700; }
.operations-toast svg { width: 20px; height: 20px; flex: 0 0 20px; fill: none; stroke: currentColor; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
@media (max-width: 1200px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .page-heading { align-items: flex-start; flex-direction: column; }
  .page-heading__actions { width: 100%; justify-content: flex-start; }
  .operations-table-wrap { display: none; }
  .operation-cards { display: grid; gap: 12px; }
  .operation-card { min-width: 0; padding: 16px; border: 1px solid var(--color-border); border-radius: var(--radius-md); }
  .operation-card__top, .operation-card__heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
  .operation-card__heading { margin-top: 12px; }
  .operation-card__heading h3 { font-size: .9rem; overflow-wrap: anywhere; }
  .operation-card__heading p { margin-top: 4px; color: var(--color-text-secondary); font-size: .72rem; }
  .operation-card__heading > strong { flex: 0 0 auto; font-size: .85rem; white-space: nowrap; }
  .operation-card__meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--color-border-subtle); }
  .operation-card__meta dt { color: var(--color-text-secondary); font-size: .68rem; }
  .operation-card__meta dd { margin-top: 2px; color: var(--color-text); font-size: .76rem; font-weight: 700; overflow-wrap: anywhere; }
  .operation-card__actions { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--color-border-subtle); }
  .operation-card__actions button { min-height: 44px; padding: 8px 10px; border-radius: 7px; color: var(--color-brand-primary); font-size: .74rem; font-weight: 800; }
  .operation-card__actions button:hover { background: var(--color-brand-primary-light); }
}
@media (max-width: 760px) {
  .operations-view { gap: 18px; }
  .page-heading__actions { flex-wrap: wrap; }
  .page-heading__actions .period-control { flex-basis: 100%; }
  .page-heading__actions .action-button { flex: 1 1 170px; }
  .filter-controls { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .search-control { grid-column: 1 / -1; }
  .operations-panel { padding: 18px; }
}
@media (max-width: 520px) {
  .summary-grid { grid-template-columns: 1fr; gap: 12px; }
  .operations-panel { padding: 16px 12px; }
  .operations-panel__header { align-items: flex-start; flex-direction: column; gap: 6px; }
  .filter-tabs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 14px -4px; overflow: visible; }
  .filter-tabs button { padding: 8px 9px; font-size: .76rem; white-space: normal; }
  .filter-controls { grid-template-columns: 1fr; }
  .search-control { grid-column: auto; }
  .page-heading__actions .action-button { flex: 1 1 100%; }
  .operation-card { padding: 14px; }
  .operation-card__heading { flex-direction: column; }
  .operation-card__heading > strong { align-self: flex-start; }
  .operation-card__meta { grid-template-columns: 1fr; }
  .operation-card__actions button { flex: 1 1 auto; }
  .operations-toast { right: 16px; bottom: 82px; left: 16px; max-width: none; }
}
</style>
