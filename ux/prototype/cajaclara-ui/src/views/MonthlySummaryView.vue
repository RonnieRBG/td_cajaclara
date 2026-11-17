<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import BadgeStatus from '@/components/common/BadgeStatus.vue'
import CashChart from '@/components/dashboard/CashChart.vue'
import StatCard from '@/components/common/StatCard.vue'
import { ApiError } from '@/services/apiClient'
import { getFilterOptions, getPeriodRange, USE_MOCKS } from '@/services/optionsService'
import { getMonthlySummaryData } from '@/services/summaryService'
import { formatCLP, formatDate } from '@/utils/formatters'

const filterOptions = ref(null)
const selectedMonth = ref('')
const selectedYear = ref(null)
const selectedChannel = ref('')
const periodData = ref(null)
const loading = ref(false)
const error = ref(null)
const periodAnnouncement = ref('')
const numberFormatter = new Intl.NumberFormat('es-CL', { maximumFractionDigits: 0 })
let requestSequence = 0

const availableYears = computed(() => [
  ...new Set((filterOptions.value?.periods ?? []).map(period => period.year))
])
const monthOptions = computed(() => (
  filterOptions.value?.periods.filter(period => period.year === selectedYear.value) ?? []
))
const periodKey = computed(() => (
  selectedYear.value && selectedMonth.value
    ? `${selectedYear.value}-${selectedMonth.value}`
    : ''
))
const selectedRange = computed(() => {
  const period = filterOptions.value?.periods.find(item => item.value === periodKey.value)
  return period ? getPeriodRange(filterOptions.value, period.year, period.month) : null
})
const periodLabel = computed(() => {
  const month = monthOptions.value.find(option => option.month === selectedMonth.value)?.label ?? ''
  return month
    ? `${month.charAt(0).toLocaleUpperCase('es-CL')}${month.slice(1)} de ${selectedYear.value}`
    : ''
})
const dateRangeLabel = computed(() => selectedRange.value
  ? `${formatDate(selectedRange.value.startDate)} – ${formatDate(selectedRange.value.endDate)}`
  : '')
const errorMessage = computed(() => {
  if (error.value instanceof ApiError && error.value.code === 'SESSION_EXPIRED') {
    return 'Tu sesión expiró. Inicia sesión nuevamente para volver a consultar el resumen.'
  }
  if (error.value instanceof ApiError && error.value.code === 'NETWORK_ERROR') {
    return 'No se pudo conectar con el Backend. Verifica que esté disponible e inténtalo de nuevo.'
  }
  return error.value?.message || 'No se pudo cargar el resumen mensual.'
})

const loadSummary = async () => {
  const sequence = ++requestSequence
  loading.value = true
  error.value = null

  try {
    if (!filterOptions.value) filterOptions.value = await getFilterOptions()
    if (!periodKey.value) {
      const [year, month] = filterOptions.value.initialPeriod.split('-')
      selectedYear.value = Number(year)
      selectedMonth.value = month
    }

    let period = filterOptions.value.periods.find(item => item.value === periodKey.value)
    if (!period && availableYears.value.length) {
      period = filterOptions.value.periods.find(item => item.year === availableYears.value[0])
      selectedYear.value = period.year
      selectedMonth.value = period.month
    }
    if (!period) {
      periodData.value = null
      return
    }

    const range = getPeriodRange(filterOptions.value, period.year, period.month)
    const result = await getMonthlySummaryData({
      ...range,
      channel: selectedChannel.value,
      period: period.value
    })
    if (sequence === requestSequence) {
      periodData.value = result
      periodAnnouncement.value = result?.hasMovements
        ? `Resumen actualizado para ${periodLabel.value}.`
        : `${periodLabel.value}: periodo sin movimientos.`
    }
  } catch (requestError) {
    if (sequence === requestSequence) error.value = requestError
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

const handleYearChange = () => {
  const firstPeriod = filterOptions.value?.periods.find(period => period.year === selectedYear.value)
  if (firstPeriod) selectedMonth.value = firstPeriod.month
  loadSummary()
}

onMounted(loadSummary)
</script>

<template>
  <div class="monthly-summary">
    <header class="summary-header">
      <div class="summary-heading">
        <p class="summary-eyebrow">Análisis del negocio</p>
        <h1 tabindex="-1">Resumen mensual</h1>
        <p class="summary-intro">Revisa el resultado de tu negocio durante el periodo</p>
      </div>

      <div class="summary-controls">
        <div class="period-selectors" role="group" aria-label="Seleccionar periodo">
          <div class="period-field">
            <label for="summary-month">Mes</label>
            <select id="summary-month" v-model="selectedMonth" :disabled="loading" @change="loadSummary">
              <option v-for="month in monthOptions" :key="month.value" :value="month.month">
                {{ month.label }}
              </option>
            </select>
          </div>
          <div class="period-field period-field--year">
            <label for="summary-year">Año</label>
            <select id="summary-year" v-model.number="selectedYear" :disabled="loading" @change="handleYearChange">
              <option v-for="year in availableYears" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
          </div>
          <div v-if="!USE_MOCKS" class="period-field period-field--channel">
            <label for="summary-channel">Canal</label>
            <select id="summary-channel" v-model="selectedChannel" :disabled="loading" @change="loadSummary">
              <option value="">Todos los canales</option>
              <option v-for="type in filterOptions?.types ?? []" :key="type.value" :value="type.value">
                {{ type.label }}
              </option>
            </select>
          </div>
        </div>
        <RouterLink class="btn btn-primary summary-action" to="/operaciones">
          Ver operaciones
        </RouterLink>
      </div>

      <p v-if="selectedChannel" class="period-announcement">
        El canal filtra ventas; los gastos en insumos no tienen canal.
      </p>
      <p v-if="periodAnnouncement" class="period-announcement" role="status" aria-live="polite">
        {{ periodAnnouncement }}
      </p>
    </header>

    <p v-if="USE_MOCKS" class="data-source-notice" role="note">Modo de demostración: datos simulados.</p>
    <p v-if="dateRangeLabel" class="summary-date-range">
      Fechas consultadas: {{ dateRangeLabel }}
    </p>
    <p v-if="!USE_MOCKS && !selectedChannel" class="summary-date-range">
      No hay desglose de gastos por categoría en el contrato; se muestra el total de gastos en insumos.
    </p>

    <p v-if="loading" class="summary-empty" role="status" aria-live="polite">
      Cargando resumen mensual…
    </p>
    <div v-else-if="error" class="summary-empty summary-error" role="alert">
      <p>{{ errorMessage }}</p>
      <button type="button" class="btn btn-primary" @click="loadSummary">Reintentar</button>
    </div>
    <p v-else-if="!periodData" class="summary-empty summary-empty--unavailable" role="status">
      No hay información disponible para este periodo
    </p>

    <p v-else-if="!periodData.hasMovements" class="summary-empty" role="status">
      Este periodo no registra movimientos.
    </p>

    <template v-else>
      <section class="summary-stats" aria-label="Indicadores del periodo">
        <StatCard
          label="Ventas del periodo"
          :amount="periodData.totals.sales"
          :subtext="`${numberFormatter.format(periodData.totals.transactions)} transacciones`"
          type="sales"
        />
        <StatCard
          label="Gastos en insumos"
          :amount="periodData.totals.expenses"
          :subtext="periodData.totals.expensesCount === null
            ? 'Sin conteo separado para el canal seleccionado'
            : `${numberFormatter.format(periodData.totals.expensesCount)} ${periodData.totals.expensesCountLabel}`"
          type="expenses"
        />
        <StatCard
          label="Saldo del periodo"
          :amount="periodData.totals.balance"
          subtext="Flujo de caja devuelto por Backend"
          type="balance"
          :is-emphasis="true"
        />
        <StatCard
          label="Pendiente por cobrar"
          :amount="periodData.sales.pending.amount"
          :subtext="`${numberFormatter.format(periodData.sales.pending.transactions)} transacciones pendientes`"
          type="pending"
        />
      </section>

      <section class="summary-chart-section" aria-labelledby="weekly-comparison-title">
        <div class="section-heading">
          <div>
            <p class="section-kicker">{{ periodLabel }}</p>
            <h2 id="weekly-comparison-title">Comparación semanal</h2>
          </div>
          <p class="chart-description">
            En {{ periodLabel }}, las ventas sumaron {{ formatCLP(periodData.totals.sales) }} y los gastos
            en insumos {{ formatCLP(periodData.totals.expenses) }}. El saldo informado fue
            {{ formatCLP(periodData.totals.balance) }}.
          </p>
        </div>
        <CashChart
          :weekly-data="periodData.weeklyData"
          :subtitle="`Comparativa semanal de ${periodLabel}`"
        />
      </section>

      <div class="summary-content-grid">
        <section class="summary-panel" aria-labelledby="expense-breakdown-title">
          <div class="section-heading">
            <div>
              <p class="section-kicker">{{ periodLabel }}</p>
              <h2 id="expense-breakdown-title">Gastos disponibles</h2>
            </div>
            <span class="panel-total">{{ formatCLP(periodData.totals.expenses) }}</span>
          </div>

          <ul class="expense-list">
            <li v-for="expense in periodData.expenses" :key="expense.category" class="expense-item">
              <div class="expense-item__label">
                <span>{{ expense.category }}</span>
              </div>
              <strong>{{ formatCLP(expense.amount) }}</strong>
            </li>
            <li v-if="periodData.expenses.length === 0" class="expense-item">
              <span>No hay gastos desglosados disponibles.</span>
            </li>
          </ul>
        </section>

        <section class="summary-panel" aria-labelledby="sales-summary-title">
          <div class="section-heading">
            <div>
              <p class="section-kicker">{{ periodLabel }}</p>
              <h2 id="sales-summary-title">Resumen de ventas</h2>
            </div>
          </div>

          <dl class="sales-breakdown">
            <div class="sales-breakdown__row">
              <dt>Ventas pagadas</dt>
              <dd>
                <strong>{{ formatCLP(periodData.sales.paid.amount) }}</strong>
                <span>{{ numberFormatter.format(periodData.sales.paid.transactions) }} transacciones</span>
              </dd>
            </div>
            <div class="sales-breakdown__row">
              <dt>Ventas pendientes</dt>
              <dd>
                <strong>{{ formatCLP(periodData.sales.pending.amount) }}</strong>
                <span>{{ numberFormatter.format(periodData.sales.pending.transactions) }} transacciones</span>
              </dd>
            </div>
            <div class="sales-breakdown__row">
              <dt>Ventas físicas</dt>
              <dd>
                <strong>{{ formatCLP(periodData.sales.physical.amount) }}</strong>
                <span>{{ numberFormatter.format(periodData.sales.physical.invoices) }} facturas</span>
              </dd>
            </div>
            <div class="sales-breakdown__row">
              <dt>Ventas en línea</dt>
              <dd>
                <strong>{{ formatCLP(periodData.sales.online.amount) }}</strong>
                <span>{{ numberFormatter.format(periodData.sales.online.invoices) }} facturas</span>
              </dd>
            </div>
          </dl>
        </section>

        <section class="summary-panel summary-panel--highlights" aria-labelledby="highlights-title">
          <div class="section-heading">
            <div>
              <p class="section-kicker">{{ periodLabel }}</p>
              <h2 id="highlights-title">Actividad destacada</h2>
            </div>
          </div>

          <div class="highlights-grid">
            <article v-if="periodData.highlights.topProduct" class="highlight-item">
              <span class="highlight-item__label">Producto más vendido</span>
              <h3>{{ periodData.highlights.topProduct }}</h3>
              <p v-if="periodData.highlights.topProductUnits !== null">
                {{ numberFormatter.format(periodData.highlights.topProductUnits) }} unidades
              </p>
            </article>
            <article v-if="periodData.highlights.pendingCustomer" class="highlight-item">
              <span class="highlight-item__label">Cliente con mayor monto pendiente</span>
              <h3>{{ periodData.highlights.pendingCustomer }}</h3>
              <p>{{ formatCLP(periodData.highlights.pendingAmount) }} por cobrar</p>
            </article>
            <article class="highlight-item">
              <span class="highlight-item__label">Mayor venta del periodo</span>
              <h3 v-if="periodData.highlights.largestSale !== null">
                {{ formatCLP(periodData.highlights.largestSale) }}
              </h3>
              <h3 v-else>Sin datos disponibles</h3>
              <p v-if="periodData.highlights.largestSale !== null">Venta individual</p>
            </article>
            <article class="highlight-item">
              <span class="highlight-item__label">Total de unidades vendidas</span>
              <h3>{{ numberFormatter.format(periodData.highlights.unitsSold) }}</h3>
              <p>Unidades en el periodo</p>
            </article>
          </div>
        </section>

        <section class="summary-panel summary-panel--operations" aria-labelledby="main-operations-title">
          <div class="section-heading">
            <div>
              <p class="section-kicker">{{ numberFormatter.format(periodData.operationCount) }} movimientos</p>
              <h2 id="main-operations-title">Operaciones principales</h2>
            </div>
            <RouterLink class="text-link" to="/operaciones">Ver todas</RouterLink>
          </div>

          <ol class="operation-list">
            <li v-for="operation in periodData.operations.slice(0, 5)" :key="operation.id" class="operation-row">
              <time class="operation-row__date" :datetime="operation.date">{{ formatDate(operation.date) }}</time>
              <BadgeStatus :status="operation.type" :label="operation.type" />
              <p class="operation-row__description">{{ operation.description }}</p>
              <strong class="operation-row__amount">{{ formatCLP(operation.amount) }}</strong>
              <BadgeStatus :status="operation.status" :label="operation.status" />
            </li>
          </ol>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.monthly-summary {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--space-6);
}

.summary-header,
.summary-heading,
.summary-controls,
.period-selectors,
.period-field {
  min-width: 0;
}

.summary-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: var(--space-4);
}

.summary-eyebrow,
.section-kicker {
  color: var(--color-brand-primary);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.summary-heading h1 {
  margin: var(--space-1) 0;
  color: var(--color-text);
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 3vw, 2.25rem);
  line-height: 1.2;
  letter-spacing: -0.035em;
}

.summary-heading h1:focus {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 4px;
  border-radius: var(--radius-xs);
}

.summary-intro {
  max-width: 42rem;
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
}

.summary-controls {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
}

.period-selectors {
  display: flex;
  gap: var(--space-3);
}

.period-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.period-field label {
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  font-weight: 700;
}

.period-field select {
  min-height: var(--control-min-height);
  min-width: 9.5rem;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
}

.period-field--year select {
  min-width: 6rem;
}

.summary-action {
  min-height: var(--control-min-height);
}

.period-announcement {
  grid-column: 1 / -1;
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
}

.summary-date-range,
.data-source-notice {
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
}

.data-source-notice {
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.summary-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.summary-stats {
  display: grid;
  min-width: 0;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.summary-chart-section,
.summary-panel {
  min-width: 0;
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.summary-chart-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  border-top: 3px solid var(--color-brand-primary);
}

.section-heading {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.section-heading h2 {
  margin-top: var(--space-1);
  color: var(--color-text);
  font-size: 1.125rem;
  line-height: 1.35;
}

.chart-description {
  max-width: 37rem;
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
  line-height: 1.55;
}

.summary-content-grid {
  display: grid;
  min-width: 0;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-5);
}

.summary-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.panel-total {
  color: var(--color-text);
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.expense-list,
.operation-list {
  display: flex;
  min-width: 0;
  flex-direction: column;
  list-style: none;
}

.expense-item {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-top: 1px solid var(--color-border-subtle);
}

.expense-item__label {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
  color: var(--color-text);
  font-size: 0.875rem;
  font-weight: 600;
}

.expense-item__percent {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  font-weight: 500;
}

.expense-item strong,
.sales-breakdown strong,
.operation-row__amount {
  color: var(--color-text);
  font-size: 0.875rem;
  font-weight: 700;
  overflow-wrap: anywhere;
  text-align: right;
}

.sales-breakdown {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.sales-breakdown__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-top: 1px solid var(--color-border-subtle);
}

.sales-breakdown dt {
  color: var(--color-text);
  font-size: 0.875rem;
  font-weight: 600;
}

.sales-breakdown dd {
  display: flex;
  min-width: 0;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.sales-breakdown dd span {
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

.summary-panel--highlights,
.summary-panel--operations {
  grid-column: 1 / -1;
}

.highlights-grid {
  display: grid;
  min-width: 0;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}

.highlight-item {
  min-width: 0;
  padding: var(--space-4);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  background: var(--color-bg-app);
}

.highlight-item__label {
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  font-weight: 600;
}

.highlight-item h3 {
  margin-top: var(--space-2);
  color: var(--color-text);
  font-size: 0.9375rem;
  overflow-wrap: anywhere;
}

.highlight-item p {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: 0.8125rem;
}

.text-link {
  flex-shrink: 0;
  color: var(--color-brand-primary);
  font-size: 0.8125rem;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.operation-list {
  gap: var(--space-2);
}

.operation-row {
  display: grid;
  min-width: 0;
  grid-template-columns: minmax(5.5rem, 0.7fr) minmax(5.5rem, 0.7fr) minmax(0, 2fr) minmax(6rem, 0.8fr) minmax(6rem, 0.7fr);
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-top: 1px solid var(--color-border-subtle);
}

.operation-row__date {
  color: var(--color-text-secondary);
  font-size: 0.8125rem;
}

.operation-row__description {
  min-width: 0;
  color: var(--color-text);
  font-size: 0.8125rem;
  overflow-wrap: anywhere;
}

.summary-empty {
  padding: var(--space-8) var(--space-5);
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
  text-align: center;
}

.summary-empty--unavailable {
  border-style: solid;
}

@media (max-width: 1100px) {
  .summary-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-header {
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
  }

  .summary-controls {
    flex-wrap: wrap;
  }

  .period-announcement {
    grid-column: auto;
  }
}

@media (max-width: 767px) {
  .summary-content-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .summary-panel--highlights,
  .summary-panel--operations {
    grid-column: auto;
  }

  .operation-row {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: var(--space-2) var(--space-3);
    padding: var(--space-4) 0;
  }

  .operation-row__date {
    grid-column: 1;
  }

  .operation-row > :nth-child(2) {
    grid-column: 2;
    justify-self: end;
  }

  .operation-row__description {
    grid-column: 1 / -1;
    grid-row: 2;
  }

  .operation-row__amount {
    grid-column: 1;
    grid-row: 3;
    text-align: left;
  }

  .operation-row > :last-child {
    grid-column: 2;
    grid-row: 3;
    justify-self: end;
  }
}

@media (max-width: 639px) {
  .monthly-summary {
    gap: var(--space-4);
  }

  .summary-controls,
  .period-selectors {
    width: 100%;
  }

  .period-field {
    flex: 1 1 0;
  }

  .period-field select {
    width: 100%;
    min-width: 0;
  }

  .summary-action {
    width: 100%;
  }

  .summary-stats {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-3);
  }

  .summary-stats :deep(.stat-card) {
    padding: var(--space-3);
  }

  .summary-chart-section,
  .summary-panel {
    padding: var(--space-4);
  }

  .summary-content-grid,
  .highlights-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .section-heading {
    align-items: flex-start;
  }
}
</style>
