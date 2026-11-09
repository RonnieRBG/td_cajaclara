<script setup>
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import BadgeStatus from '@/components/common/BadgeStatus.vue'
import CashChart from '@/components/dashboard/CashChart.vue'
import StatCard from '@/components/common/StatCard.vue'
import { monthlySummaryData } from '@/data/monthlySummaryMock'
import { formatCLP, formatDate } from '@/utils/formatters'

const monthOptions = Array.from({ length: 12 }, (_, index) => {
  const date = new Date(2026, index, 1)
  return {
    value: String(index + 1).padStart(2, '0'),
    label: date.toLocaleDateString('es-CL', { month: 'long' })
  }
})

const selectedMonth = ref('10')
const selectedYear = ref(2026)
const periodAnnouncement = ref('')
const numberFormatter = new Intl.NumberFormat('es-CL', { maximumFractionDigits: 0 })

const periodKey = computed(() => `${selectedYear.value}-${selectedMonth.value}`)
const periodData = computed(() => monthlySummaryData[periodKey.value] ?? null)
const periodLabel = computed(() => {
  const month = monthOptions.find(option => option.value === selectedMonth.value)?.label ?? ''
  return `${month.charAt(0).toLocaleUpperCase('es-CL')}${month.slice(1)} de ${selectedYear.value}`
})
const salesTotal = computed(() => (
  (periodData.value?.sales.paid.amount ?? 0) +
  (periodData.value?.sales.pending.amount ?? 0)
))
const expensesTotal = computed(() => (
  periodData.value?.expenses.reduce((total, item) => total + item.amount, 0) ?? 0
))
const periodBalance = computed(() => salesTotal.value - expensesTotal.value)

const expenseShare = (amount) => (
  expensesTotal.value ? Math.round((amount / expensesTotal.value) * 100) : 0
)

const announcePeriodChange = () => {
  if (!periodData.value) {
    periodAnnouncement.value = `No hay información disponible para ${periodLabel.value}.`
    return
  }

  if (!periodData.value.hasMovements) {
    periodAnnouncement.value = `${periodLabel.value}: periodo seleccionado sin movimientos.`
    return
  }

  periodAnnouncement.value = `Resumen actualizado para ${periodLabel.value}.`
}
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
            <select id="summary-month" v-model="selectedMonth" @change="announcePeriodChange">
              <option v-for="month in monthOptions" :key="month.value" :value="month.value">
                {{ month.label }}
              </option>
            </select>
          </div>
          <div class="period-field period-field--year">
            <label for="summary-year">Año</label>
            <select id="summary-year" v-model.number="selectedYear" @change="announcePeriodChange">
              <option v-for="year in [2025, 2026, 2027]" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
          </div>
        </div>
        <RouterLink class="btn btn-primary summary-action" to="/operaciones">
          Ver operaciones
        </RouterLink>
      </div>

      <p v-if="periodAnnouncement" class="period-announcement" role="status" aria-live="polite">
        {{ periodAnnouncement }}
      </p>
    </header>

    <p v-if="!periodData" class="summary-empty summary-empty--unavailable" role="status">
      No hay información disponible para este periodo
    </p>

    <p v-else-if="!periodData.hasMovements" class="summary-empty" role="status">
      Este periodo no registra movimientos.
    </p>

    <template v-else>
      <section class="summary-stats" aria-label="Indicadores del periodo">
        <StatCard
          label="Ventas del periodo"
          :amount="salesTotal"
          :subtext="`${numberFormatter.format(periodData.sales.paid.operations + periodData.sales.pending.operations)} operaciones`"
          type="sales"
        />
        <StatCard
          label="Compras y gastos"
          :amount="expensesTotal"
          :subtext="`${numberFormatter.format(periodData.expenses.length)} categorías de gasto`"
          type="expenses"
        />
        <StatCard
          label="Saldo del periodo"
          :amount="periodBalance"
          subtext="Ventas - Compras y gastos"
          type="balance"
          :is-emphasis="true"
        />
        <StatCard
          label="Pendiente por cobrar"
          :amount="periodData.sales.pending.amount"
          :subtext="`${numberFormatter.format(periodData.sales.pending.operations)} ventas pendientes`"
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
            En {{ periodLabel }}, las ventas sumaron {{ formatCLP(salesTotal) }} y las compras y gastos
            {{ formatCLP(expensesTotal) }}. El saldo del periodo fue de {{ formatCLP(periodBalance) }}.
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
              <h2 id="expense-breakdown-title">Desglose de gastos</h2>
            </div>
            <span class="panel-total">{{ formatCLP(expensesTotal) }}</span>
          </div>

          <ul class="expense-list">
            <li v-for="expense in periodData.expenses" :key="expense.category" class="expense-item">
              <div class="expense-item__label">
                <span>{{ expense.category }}</span>
                <span class="expense-item__percent">{{ expenseShare(expense.amount) }}% del total</span>
              </div>
              <strong>{{ formatCLP(expense.amount) }}</strong>
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
                <span>{{ numberFormatter.format(periodData.sales.paid.operations) }} operaciones</span>
              </dd>
            </div>
            <div class="sales-breakdown__row">
              <dt>Ventas pendientes</dt>
              <dd>
                <strong>{{ formatCLP(periodData.sales.pending.amount) }}</strong>
                <span>{{ numberFormatter.format(periodData.sales.pending.operations) }} operaciones</span>
              </dd>
            </div>
            <div class="sales-breakdown__row">
              <dt>Ventas físicas</dt>
              <dd>
                <strong>{{ formatCLP(periodData.sales.physical.amount) }}</strong>
                <span>{{ numberFormatter.format(periodData.sales.physical.operations) }} operaciones</span>
              </dd>
            </div>
            <div class="sales-breakdown__row">
              <dt>Ventas en línea</dt>
              <dd>
                <strong>{{ formatCLP(periodData.sales.online.amount) }}</strong>
                <span>{{ numberFormatter.format(periodData.sales.online.operations) }} operaciones</span>
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
            <article class="highlight-item">
              <span class="highlight-item__label">Producto más vendido</span>
              <h3>{{ periodData.highlights.topProduct }}</h3>
              <p>{{ numberFormatter.format(periodData.highlights.topProductUnits) }} unidades</p>
            </article>
            <article class="highlight-item">
              <span class="highlight-item__label">Cliente con mayor monto pendiente</span>
              <h3>{{ periodData.highlights.pendingCustomer }}</h3>
              <p>{{ formatCLP(periodData.highlights.pendingAmount) }} por cobrar</p>
            </article>
            <article class="highlight-item">
              <span class="highlight-item__label">Mayor venta del periodo</span>
              <h3>{{ formatCLP(periodData.highlights.largestSale) }}</h3>
              <p>Venta individual</p>
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
