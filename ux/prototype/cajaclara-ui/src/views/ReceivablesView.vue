<script setup>
import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import BadgeStatus from '@/components/common/BadgeStatus.vue'
import ReceivableDetailModal from '@/components/receivables/ReceivableDetailModal.vue'
import PaymentModal from '@/components/receivables/PaymentModal.vue'
import { formatCLP, formatDate, getLocalDateString } from '@/utils/formatters'
import { USE_MOCKS } from '@/services/optionsService'
import {
  getCollectionAlerts,
  getReceivableDetail,
  getReceivables,
  getReceivablesSummary,
  payReceivable,
  revertReceivablePayment
} from '@/services/receivablesService'

const accounts = ref([])
const summary = ref(null)
const summaryLoading = ref(false)
const summaryError = ref('')
const isLoading = ref(false)
const loadError = ref('')
const resultCount = ref(0)
const alerts = ref([])
const alertsLoading = ref(false)
const alertsError = ref('')
const activeFilter = ref('all')
const searchQuery = ref('')
const sortOrder = ref('earliest')
const currentPage = ref(1)
const pageSize = 10
const selectedAccount = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
const paymentAccount = ref(null)
const paymentMode = ref('pay')
const paymentSaving = ref(false)
const paymentError = ref('')
const showToast = ref(false)
const toastMessage = ref('')
let toastTimeout
let searchTimeout
let accountRequestSequence = 0
let summaryRequestSequence = 0
let skipPageReload = false
const refreshCollectionAlertCount = inject('refreshCollectionAlertCount', () => {
  throw new Error('No está disponible la actualización del indicador lateral de cobros.')
})

const alertByAccount = computed(() => Object.fromEntries(
  alerts.value.map((alert) => [String(alert.id), alert])
))
const tabs = [
  { id: 'all', label: 'Todas' },
  { id: 'pending', label: 'Pendientes' },
  { id: 'overdue', label: 'Vencidas' },
  { id: 'paid', label: 'Pagadas' }
]
const statusByFilter = {
  pending: 'PENDIENTE',
  overdue: 'VENCIDA',
  paid: 'PAGADA'
}

const filteredAccounts = computed(() => {
  if (!USE_MOCKS) return accounts.value

  const query = searchQuery.value.trim().toLocaleLowerCase('es-CL')
  return accounts.value
    .filter(account => activeFilter.value === 'all' || account.displayStatus === statusByFilter[activeFilter.value])
    .filter(account => !query || `${account.clientName} ${account.invoiceId}`.toLocaleLowerCase('es-CL').includes(query))
    .sort((a, b) => {
      const result = a.dueDate.localeCompare(b.dueDate)
      return sortOrder.value === 'earliest' ? result : -result
    })
})
const displayedCount = computed(() => USE_MOCKS ? filteredAccounts.value.length : resultCount.value)
const totalPages = computed(() => Math.max(
  1,
  Math.ceil((USE_MOCKS ? filteredAccounts.value.length : resultCount.value) / pageSize)
))
const pageAccounts = computed(() => {
  if (!USE_MOCKS) return accounts.value
  const start = (currentPage.value - 1) * pageSize
  return filteredAccounts.value.slice(start, start + pageSize)
})
const noAccounts = computed(() => USE_MOCKS
  ? accounts.value.length === 0
  : summary.value?.totalCount === 0
)

function tabCount(filter) {
  if (!summary.value) return 0
  if (filter === 'all') return summary.value.totalCount
  if (filter === 'pending') return summary.value.pendingOnlyCount
  if (filter === 'overdue') return summary.value.overdueCount
  return summary.value.paidCount
}

watch([activeFilter, sortOrder], () => {
  if (currentPage.value !== 1) {
    skipPageReload = true
    currentPage.value = 1
  }
  if (!USE_MOCKS) loadAccounts()
})
watch(currentPage, () => {
  if (skipPageReload) {
    skipPageReload = false
    return
  }
  if (!USE_MOCKS) loadAccounts()
})
watch(searchQuery, () => {
  if (USE_MOCKS) {
    currentPage.value = 1
    return
  }
  window.clearTimeout(searchTimeout)
  if (currentPage.value !== 1) {
    skipPageReload = true
    currentPage.value = 1
  }
  searchTimeout = window.setTimeout(loadAccounts, 300)
})
watch(totalPages, (pages) => {
  if (currentPage.value > pages) currentPage.value = pages
})

const daysUntilDue = (date) => {
  const today = new Date(`${getLocalDateString()}T00:00:00`)
  const dueDate = new Date(`${date}T00:00:00`)
  return Math.round((dueDate - today) / 86400000)
}

const dueAlert = (account) => {
  const days = daysUntilDue(account.dueDate)
  if (account.displayStatus === 'PAGADA') return ''
  if (days < 0) return `Vencida hace ${Math.abs(days)} ${Math.abs(days) === 1 ? 'día' : 'días'}`
  if (days === 0) return 'Vence hoy'
  if (days <= 7) return `Vence en ${days} ${days === 1 ? 'día' : 'días'}`
  return ''
}

async function loadAccounts() {
  const sequence = ++accountRequestSequence
  isLoading.value = true
  loadError.value = ''
  try {
    const data = await getReceivables({
      filter: statusByFilter[activeFilter.value] || 'all',
      search: searchQuery.value,
      sortOrder: sortOrder.value,
      page: currentPage.value
    })
    if (sequence !== accountRequestSequence) return
    accounts.value = data.results
    resultCount.value = data.count
  } catch (error) {
    if (sequence === accountRequestSequence) {
      loadError.value = error.message || 'No se pudieron cargar las cuentas por cobrar.'
    }
  } finally {
    if (sequence === accountRequestSequence) isLoading.value = false
  }
}

async function loadSummary() {
  const sequence = ++summaryRequestSequence
  summaryLoading.value = true
  summaryError.value = ''
  try {
    const data = await getReceivablesSummary()
    if (sequence === summaryRequestSequence) summary.value = data
  } catch (error) {
    if (sequence === summaryRequestSequence) {
      summaryError.value = error.message || 'No se pudieron cargar los indicadores de cobros.'
    }
  } finally {
    if (sequence === summaryRequestSequence) summaryLoading.value = false
  }
}

async function loadAlerts() {
  alertsLoading.value = true
  alertsError.value = ''
  try {
    alerts.value = await getCollectionAlerts()
    if (selectedAccount.value) {
      selectedAccount.value = {
        ...selectedAccount.value,
        suggestedMessage: alertByAccount.value[String(selectedAccount.value.id)]?.suggestedMessage || null
      }
    }
  } catch (error) {
    alertsError.value = error.message || 'No se pudieron cargar los recordatorios sugeridos.'
  } finally {
    alertsLoading.value = false
  }
}

async function openDetail(account) {
  selectedAccount.value = {
    ...account,
    suggestedMessage: alertByAccount.value[String(account.id)]?.suggestedMessage || null
  }
  detailError.value = ''
  detailLoading.value = true
  try {
    const detail = await getReceivableDetail(account)
    if (String(selectedAccount.value?.id) === String(account.id)) {
      selectedAccount.value = {
        ...detail,
        suggestedMessage: alertByAccount.value[String(account.id)]?.suggestedMessage || null
      }
    }
  } catch (error) {
    detailError.value = error.message || 'No se pudo cargar el detalle de la cuenta.'
  } finally {
    detailLoading.value = false
  }
}

function retryDetail() {
  if (selectedAccount.value) openDetail(selectedAccount.value)
}

const notify = (message) => {
  toastMessage.value = message
  showToast.value = true
  window.clearTimeout(toastTimeout)
  toastTimeout = window.setTimeout(() => {
    showToast.value = false
  }, 3500)
}

function openPayment(account, mode) {
  paymentAccount.value = account
  paymentMode.value = mode
  paymentError.value = ''
}

async function savePayment({ date }) {
  if (!paymentAccount.value) return
  paymentSaving.value = true
  paymentError.value = ''
  const savedMode = paymentMode.value
  const accountId = paymentAccount.value.id
  try {
    if (savedMode === 'pay') {
      await payReceivable(accountId, date)
    } else {
      await revertReceivablePayment(accountId)
    }
  } catch (error) {
    paymentError.value = error.message || 'No se pudo guardar el cambio.'
    paymentSaving.value = false
    return
  }

  paymentAccount.value = null
  paymentSaving.value = false
  notify(savedMode === 'pay' ? 'Pago completo registrado.' : 'Pago revertido.')
  await Promise.all([
    loadAccounts(),
    loadSummary(),
    loadAlerts(),
    refreshCollectionAlertCount()
  ])
  await nextTick()
  document.querySelector('#receivables-list-title')?.focus()
}

async function copyReminder(account) {
  const message = account.suggestedMessage ||
    alertByAccount.value[String(account.id)]?.suggestedMessage
  if (!message) return
  try {
    if (!navigator.clipboard?.writeText) throw new Error('El navegador no permite copiar al portapapeles.')
    await navigator.clipboard.writeText(message)
    notify('Recordatorio sugerido copiado.')
  } catch {
    notify('No se pudo copiar el recordatorio. Puedes copiar el texto desde el detalle de la cuenta.')
  }
}

onMounted(() => {
  loadAccounts()
  loadSummary()
  loadAlerts()
})
onBeforeUnmount(() => {
  window.clearTimeout(toastTimeout)
  window.clearTimeout(searchTimeout)
})
</script>

<template>
  <div class="receivables-view">
    <div v-if="showToast" class="receivables-toast" role="status" aria-live="polite">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg>
      <span>{{ toastMessage }}</span>
    </div>

    <header class="page-heading">
      <div class="page-heading__copy">
        <span class="page-eyebrow">Almacén La Esquina</span>
        <h1>Cuentas por cobrar</h1>
        <p>Controla las ventas pendientes y registra los pagos de tus clientes</p>
      </div>
    </header>

    <section v-if="summary" class="summary-grid" aria-label="Resumen de cuentas por cobrar">
      <StatCard title="Total pendiente" :amount="summary.pendingAmount" subtitle="Incluye cuentas vencidas" variant="pending" />
      <StatCard title="Total vencido" :amount="summary.overdueAmount" subtitle="Monto fuera de plazo" variant="expense" />
      <StatCard title="Cuentas pendientes" :value="summary.pendingCount" subtitle="Pendientes o vencidas" variant="pending" :format-as-currency="false" />
      <StatCard title="Cuentas pagadas" :value="summary.paidCount" subtitle="Cuentas completamente pagadas" variant="income" :format-as-currency="false" />
    </section>
    <div v-else-if="summaryLoading" class="receivables-feedback" role="status" aria-live="polite">
      Cargando indicadores de cobros…
    </div>
    <div v-if="summaryError" class="receivables-feedback receivables-feedback--error" role="alert">
      <span>{{ summaryError }}</span>
      <button type="button" class="btn btn-secondary" @click="loadSummary">Reintentar indicadores</button>
    </div>

    <div v-if="alertsLoading" class="receivables-feedback" role="status" aria-live="polite">
      Cargando recordatorios sugeridos…
    </div>
    <div v-else-if="alertsError" class="receivables-feedback receivables-feedback--error" role="alert">
      <span>{{ alertsError }}</span>
      <button type="button" class="btn btn-secondary" @click="loadAlerts">Reintentar recordatorios</button>
    </div>

    <section class="receivables-panel" aria-labelledby="receivables-list-title">
      <div class="panel-heading">
        <div>
          <span class="page-eyebrow">Seguimiento de clientes</span>
          <h2 id="receivables-list-title" tabindex="-1">Listado de cuentas</h2>
        </div>
        <span class="result-count">{{ displayedCount }} {{ displayedCount === 1 ? 'cuenta' : 'cuentas' }}</span>
      </div>

      <div class="filter-tabs" role="group" aria-label="Filtrar cuentas por estado">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          :aria-pressed="activeFilter === tab.id"
          :class="{ 'is-active': activeFilter === tab.id }"
          @click="activeFilter = tab.id"
        >{{ tab.label }} ({{ tabCount(tab.id) }})</button>
      </div>

      <div class="filter-controls">
        <label class="search-control">
          <span>Buscar por cliente o factura</span>
          <div class="search-input">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
            <input v-model="searchQuery" type="search" aria-label="Buscar por cliente o factura" placeholder="Nombre del cliente o número de factura" />
          </div>
        </label>
        <label class="sort-control">
          <span>Ordenar por fecha de vencimiento</span>
          <select v-model="sortOrder">
            <option value="earliest">Vencimiento más próximo</option>
            <option value="latest">Vencimiento más lejano</option>
          </select>
        </label>
      </div>

      <div v-if="isLoading" class="empty-state" role="status" aria-live="polite">
        <h3>Cargando cuentas por cobrar…</h3>
      </div>
      <div v-else-if="loadError" class="empty-state" role="alert">
        <h3>No se pudieron cargar las cuentas</h3>
        <p>{{ loadError }}</p>
        <button type="button" class="btn btn-secondary" @click="loadAccounts">Reintentar</button>
      </div>
      <div v-else-if="noAccounts" class="empty-state">
        <span class="empty-icon" aria-hidden="true">◇</span>
        <h3>Aún no tienes cuentas por cobrar</h3>
        <p>Las ventas pendientes aparecerán aquí.</p>
      </div>
      <div v-else-if="filteredAccounts.length === 0" class="empty-state">
        <span class="empty-icon" aria-hidden="true">⌕</span>
        <h3>No encontramos cuentas para los filtros seleccionados</h3>
        <p>Prueba con otros filtros o busca por nombre de cliente o factura.</p>
      </div>

      <template v-else-if="filteredAccounts.length > 0">
        <div class="table-wrap">
          <table class="receivables-table">
            <caption class="sr-only">Cuentas por cobrar con cliente, factura, descripción, fechas, monto, estado y acciones</caption>
            <thead>
              <tr>
                <th scope="col">Cliente</th>
                <th scope="col">Factura</th>
                <th scope="col">Descripción o productos</th>
                <th scope="col">Emisión</th>
                <th scope="col">Vencimiento</th>
                <th scope="col" class="align-right">Monto</th>
                <th scope="col">Estado</th>
                <th scope="col"><span class="sr-only">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="account in pageAccounts" :key="account.id">
                <td class="client-cell">{{ account.clientName }}<small>{{ account.contact }}</small></td>
                <td class="invoice-cell">{{ account.invoiceId }}</td>
                <td class="description-cell">
                  <strong>{{ account.description || 'Detalle disponible en la factura' }}</strong>
                  <small>{{ account.products?.map(product => product.name).join(', ') }}</small>
                </td>
                <td>{{ formatDate(account.issuedDate) }}</td>
                <td class="due-cell">{{ formatDate(account.dueDate) }}<small v-if="dueAlert(account)">{{ dueAlert(account) }}</small></td>
                <td class="amount-cell">{{ formatCLP(account.amount) }}</td>
                <td>
                  <BadgeStatus :status="account.displayStatus">
                    <svg v-if="account.displayStatus === 'PAGADA'" viewBox="0 0 20 20" aria-hidden="true"><path d="m4 10 4 4 8-8" /></svg>
                    <svg v-else-if="account.displayStatus === 'VENCIDA'" viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v7m0 4h.01M3 17h14L10 3 3 17Z" /></svg>
                    <svg v-else viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7" /><path d="M10 6v4l3 2" /></svg>
                    {{ account.displayStatus }}
                  </BadgeStatus>
                </td>
                <td>
                  <div class="row-actions">
                    <button type="button" @click="openDetail(account)">Ver detalle</button>
                    <button
                      v-if="alertByAccount[String(account.id)]?.suggestedMessage"
                      type="button"
                      @click="copyReminder({ ...account, suggestedMessage: alertByAccount[String(account.id)].suggestedMessage })"
                    >Copiar recordatorio</button>
                    <button v-if="account.displayStatus !== 'PAGADA'" type="button" @click="openPayment(account, 'pay')">Registrar pago completo</button>
                    <button v-else type="button" @click="openPayment(account, 'revert')">Revertir pago</button>
                    <router-link class="row-action-link" to="/operaciones">Ver operación</router-link>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="account-cards">
          <article v-for="account in pageAccounts" :key="account.id" class="account-card">
            <div class="account-card__header">
              <div class="account-card__identity">
                <h3>{{ account.clientName }}</h3>
                <span>{{ account.invoiceId }} · {{ account.contact }}</span>
              </div>
              <BadgeStatus :status="account.displayStatus">
                <svg v-if="account.displayStatus === 'PAGADA'" viewBox="0 0 20 20" aria-hidden="true"><path d="m4 10 4 4 8-8" /></svg>
                <svg v-else-if="account.displayStatus === 'VENCIDA'" viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v7m0 4h.01M3 17h14L10 3 3 17Z" /></svg>
                <svg v-else viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7" /><path d="M10 6v4l3 2" /></svg>
                {{ account.displayStatus }}
              </BadgeStatus>
            </div>
            <p class="account-card__description">
              {{ account.description || 'Detalle disponible en la factura' }}
              <span v-if="account.products?.length"> · {{ account.products.map(product => product.name).join(', ') }}</span>
            </p>
            <dl class="account-card__facts">
              <div><dt>Fecha de emisión</dt><dd>{{ formatDate(account.issuedDate) }}</dd></div>
              <div><dt>Fecha de vencimiento</dt><dd>{{ formatDate(account.dueDate) }}<small v-if="dueAlert(account)">{{ dueAlert(account) }}</small></dd></div>
              <div><dt>Monto</dt><dd>{{ formatCLP(account.amount) }}</dd></div>
            </dl>
            <div class="card-actions">
              <button type="button" class="btn btn-secondary" @click="openDetail(account)">Ver detalle</button>
              <button
                v-if="alertByAccount[String(account.id)]?.suggestedMessage"
                type="button"
                class="btn btn-secondary"
                @click="copyReminder({ ...account, suggestedMessage: alertByAccount[String(account.id)].suggestedMessage })"
              >Copiar recordatorio</button>
              <button v-if="account.displayStatus !== 'PAGADA'" type="button" class="btn btn-primary" @click="openPayment(account, 'pay')">Registrar pago completo</button>
              <button v-else type="button" class="btn btn-primary" @click="openPayment(account, 'revert')">Revertir pago</button>
              <router-link class="btn btn-secondary" to="/operaciones">Ver operación</router-link>
            </div>
          </article>
        </div>

        <nav v-if="totalPages > 1" class="pagination" aria-label="Paginación de cuentas por cobrar">
          <button type="button" class="btn btn-secondary" :disabled="currentPage === 1" @click="currentPage -= 1">
            Página anterior
          </button>
          <span aria-live="polite">Página {{ currentPage }} de {{ totalPages }}</span>
          <button type="button" class="btn btn-secondary" :disabled="currentPage === totalPages" @click="currentPage += 1">
            Página siguiente
          </button>
        </nav>
      </template>
    </section>

    <ReceivableDetailModal
      :is-open="Boolean(selectedAccount)"
      :account="selectedAccount"
      :is-loading="detailLoading"
      :error="detailError"
      @close="selectedAccount = null"
      @retry="retryDetail"
      @copy-reminder="copyReminder(selectedAccount)"
    />
    <PaymentModal
      :is-open="Boolean(paymentAccount)"
      :account="paymentAccount"
      :mode="paymentMode"
      :is-saving="paymentSaving"
      :error="paymentError"
      @close="paymentAccount = null"
      @confirm="savePayment"
    />
  </div>
</template>

<style scoped>
.receivables-view { display: flex; min-width: var(--content-min-width); flex-direction: column; gap: var(--layout-section-gap); }
.page-heading { display: flex; min-width: var(--content-min-width); align-items: flex-end; justify-content: space-between; gap: var(--layout-card-gap); }
.page-heading__copy { min-width: var(--content-min-width); }
.page-eyebrow { color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.page-heading h1 { margin: var(--space-1) 0 var(--space-2); color: var(--color-text); font-size: clamp(1.65rem, 3vw, 2rem); font-weight: 800; letter-spacing: -.04em; line-height: 1.15; }
.page-heading p { max-width: 38rem; color: var(--color-text-secondary); font-size: .95rem; }
.receivables-feedback { display: flex; min-width: var(--content-min-width); align-items: center; justify-content: space-between; flex-wrap: wrap; gap: var(--layout-control-gap); padding: var(--layout-control-gap); border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-secondary); font-size: .82rem; }
.receivables-feedback--error { border-color: var(--color-danger); color: var(--color-danger); }
.summary-grid { display: grid; min-width: var(--content-min-width); grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--layout-control-gap); }
.receivables-panel { min-width: var(--content-min-width); padding: var(--layout-card-gap); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface); box-shadow: var(--shadow-card); }
.panel-heading { display: flex; min-width: var(--content-min-width); align-items: center; justify-content: space-between; gap: var(--layout-control-gap); }
.panel-heading h2 { margin-top: var(--space-1); color: var(--color-text); font-size: 1.15rem; }
.result-count { color: var(--color-text-secondary); font-size: .8rem; font-weight: 700; white-space: nowrap; }
.filter-tabs { display: flex; min-width: var(--content-min-width); gap: var(--space-1); margin: var(--space-4) 0; overflow-x: auto; border-bottom: 1px solid var(--color-border); }
.filter-tabs button { position: relative; min-height: var(--control-min-height); padding: var(--space-2) var(--layout-control-gap); color: var(--color-text-secondary); font-size: .82rem; font-weight: 700; white-space: nowrap; }
.filter-tabs button.is-active { color: var(--color-brand-primary); }
.filter-tabs button.is-active::after { position: absolute; right: var(--space-2); bottom: -1px; left: var(--space-2); height: 3px; border-radius: 3px 3px 0 0; background: var(--color-brand-primary); content: ''; }
.filter-controls { display: grid; min-width: var(--content-min-width); grid-template-columns: minmax(0, 2fr) minmax(14rem, 1fr); gap: var(--layout-control-gap); margin-bottom: var(--space-4); }
.search-control, .sort-control { display: flex; min-width: var(--content-min-width); flex-direction: column; gap: var(--space-1); color: var(--color-text-secondary); font-size: .75rem; font-weight: 700; }
.search-input { display: flex; min-width: var(--content-min-width); min-height: var(--control-min-height); align-items: center; gap: var(--space-2); padding: 0 var(--layout-control-gap); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); }
.search-input svg { width: 18px; height: 18px; flex: 0 0 18px; fill: none; stroke: var(--color-text-muted); stroke-width: 1.8; stroke-linecap: round; }
.search-input input { width: 100%; min-width: var(--content-min-width); border: 0; outline: 0; background: transparent; color: var(--color-text); font: inherit; font-weight: 500; }
.sort-control select { width: 100%; min-width: var(--content-min-width); min-height: var(--control-min-height); padding: var(--space-2) var(--layout-control-gap); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); color: var(--color-text); font: inherit; font-weight: 500; }
.table-wrap { width: 100%; max-width: 100%; min-width: var(--content-min-width); overflow-x: auto; }
.receivables-table { width: 100%; min-width: 66rem; border-collapse: collapse; }
.receivables-table th { padding: var(--layout-control-gap) var(--space-2); border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); font-size: .68rem; font-weight: 800; letter-spacing: .04em; text-align: left; text-transform: uppercase; white-space: nowrap; }
.receivables-table td { max-width: 16rem; padding: var(--layout-control-gap) var(--space-2); border-bottom: 1px solid var(--color-border-subtle); color: var(--color-text); font-size: .78rem; vertical-align: middle; }
.receivables-table tbody tr:last-child td { border-bottom: 0; }
.client-cell, .description-cell, .due-cell { overflow-wrap: anywhere; }
.client-cell { font-weight: 700; }
.client-cell small, .description-cell small, .due-cell small, .account-card__facts small { display: block; margin-top: var(--space-1); color: var(--color-text-secondary); font-size: .7rem; font-weight: 500; }
.invoice-cell { color: var(--color-text-secondary); font-variant-numeric: tabular-nums; white-space: nowrap; }
.description-cell strong { display: block; }
.align-right, .amount-cell { text-align: right !important; white-space: nowrap; }
.amount-cell { font-weight: 800 !important; }
.due-cell small { color: var(--color-warning); }
:deep(.badge-status) { gap: var(--space-1); }
:deep(.badge-status svg) { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.row-actions { display: flex; flex-wrap: wrap; gap: var(--space-1); }
.row-action-link, .row-actions button { display: inline-flex; min-height: var(--control-min-height); align-items: center; padding: var(--space-2); border-radius: var(--radius-sm); color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; white-space: nowrap; }
.row-action-link:hover, .row-actions button:hover { background: var(--color-brand-primary-light); }
.account-cards { display: none; }
.empty-state { display: flex; min-height: 15rem; flex-direction: column; align-items: center; justify-content: center; gap: var(--layout-control-gap); padding: var(--layout-card-gap); text-align: center; }
.empty-state h3 { color: var(--color-text); font-size: 1rem; }
.empty-state p { color: var(--color-text-secondary); font-size: .85rem; }
.empty-icon { display: grid; width: 3rem; height: 3rem; place-items: center; border-radius: 50%; background: var(--color-brand-primary-light); color: var(--color-brand-primary); font-size: 1.5rem; }
.pagination { display: flex; min-width: var(--content-min-width); align-items: center; justify-content: center; flex-wrap: wrap; gap: var(--layout-control-gap); margin-top: var(--layout-card-gap); }
.pagination span { color: var(--color-text-secondary); font-size: .82rem; font-weight: 700; }
.receivables-toast { position: fixed; right: var(--layout-gutter-tablet); bottom: var(--layout-control-gap); z-index: 1200; display: flex; min-width: var(--content-min-width); align-items: center; gap: var(--layout-control-gap); max-width: min(27.5rem, calc(100vw - var(--space-8))); padding: var(--layout-control-gap) var(--layout-card-gap); border: 1px solid var(--color-brand-primary-border); border-radius: var(--radius-md); background: var(--color-brand-primary-light); color: var(--color-brand-primary); box-shadow: var(--shadow-lg); font-size: .86rem; font-weight: 700; }
.receivables-toast svg { width: 20px; height: 20px; flex: 0 0 20px; fill: none; stroke: currentColor; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
.card:focus-within, .receivables-panel:focus-within { outline: 0; }
@media (max-width: 1200px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 900px) {
  .filter-controls { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .table-wrap { display: none; }
  .account-cards { display: grid; min-width: var(--content-min-width); gap: var(--layout-control-gap); }
  .account-card { min-width: var(--content-min-width); padding: var(--layout-card-gap); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
  .account-card__header { display: flex; min-width: var(--content-min-width); align-items: flex-start; justify-content: space-between; gap: var(--layout-control-gap); }
  .account-card__identity { min-width: var(--content-min-width); }
  .account-card__header h3 { color: var(--color-text); font-size: .95rem; overflow-wrap: anywhere; }
  .account-card__identity > span { color: var(--color-text-secondary); font-size: .75rem; }
  .account-card__description { margin-top: var(--layout-control-gap); color: var(--color-text-secondary); font-size: .82rem; overflow-wrap: anywhere; }
  .account-card__facts { display: grid; min-width: var(--content-min-width); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--layout-control-gap); margin-top: var(--layout-control-gap); padding-top: var(--layout-control-gap); border-top: 1px solid var(--color-border-subtle); }
  .account-card__facts > div { min-width: var(--content-min-width); }
  .account-card__facts dt { color: var(--color-text-secondary); font-size: .7rem; }
  .account-card__facts dd { margin-top: var(--space-1); color: var(--color-text); font-size: .8rem; font-weight: 700; overflow-wrap: anywhere; }
  .card-actions { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--layout-control-gap); padding-top: var(--layout-control-gap); border-top: 1px solid var(--color-border-subtle); }
  .card-actions .btn { min-width: 0; flex: 1 1 8rem; font-size: .76rem; white-space: normal; }
}
@media (max-width: 640px) {
  .receivables-view { gap: var(--layout-card-gap); }
  .receivables-panel { padding: var(--layout-control-gap); }
  .filter-controls { grid-template-columns: minmax(0, 1fr); }
  .filter-tabs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: var(--layout-control-gap) 0; overflow: visible; }
  .filter-tabs button { padding-inline: var(--space-2); white-space: normal; }
  .account-card { padding: var(--layout-control-gap); }
  .account-card__header { flex-direction: column; }
  .account-card__facts { grid-template-columns: minmax(0, 1fr); }
  .card-actions { flex-direction: column; }
  .card-actions .btn { width: 100%; flex-basis: auto; }
  .receivables-toast { right: var(--layout-gutter-mobile); bottom: calc(var(--layout-bottom-nav-height) + var(--layout-control-gap)); left: var(--layout-gutter-mobile); max-width: none; }
}
@media (max-width: 520px) {
  .summary-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
