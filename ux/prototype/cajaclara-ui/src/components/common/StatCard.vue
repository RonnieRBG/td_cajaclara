<template>
  <article :class="['stat-card', { 'stat-card--emphasis': computedEmphasis }]">
    <div class="stat-card__header">
      <div class="stat-card__icon-wrapper" :class="`stat-card__icon--${resolvedType}`" aria-hidden="true">
        <!-- Sales / Income -->
        <svg v-if="resolvedType === 'sales'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5" />
          <polyline points="5 12 12 5 19 12" />
        </svg>
        <!-- Expenses / Outflow -->
        <svg v-else-if="resolvedType === 'expenses'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19" />
          <polyline points="19 12 12 19 5 12" />
        </svg>
        <!-- Balance -->
        <svg v-else-if="resolvedType === 'balance'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="4" width="20" height="16" rx="2" />
          <line x1="2" y1="10" x2="22" y2="10" />
        </svg>
        <!-- Receivables / Pending -->
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      </div>

      <div class="stat-card__tags">
        <span v-if="trend" class="stat-card__trend" :class="{ 'trend-up': trend.startsWith('+'), 'trend-down': trend.startsWith('-') }">
          {{ trend }}
        </span>
        <span v-if="badge" class="stat-card__badge" :class="`stat-card__badge--${resolvedType}`">
          {{ badge }}
        </span>
      </div>
    </div>

    <div class="stat-card__body">
      <span class="stat-card__label">{{ resolvedLabel }}</span>
      <div class="stat-card__value">
        {{ formattedValue }}
      </div>
      <p class="stat-card__subtext">{{ resolvedSubtext }}</p>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { formatCLP } from '@/utils/formatters'

const props = defineProps({
  label: { type: String, default: '' },
  title: { type: String, default: '' },
  value: { type: Number, default: 0 },
  amount: { type: Number, default: 0 },
  subtext: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  type: { type: String, default: '' },
  variant: { type: String, default: '' },
  isEmphasis: { type: Boolean, default: false },
  trend: { type: String, default: '' },
  trendLabel: { type: String, default: '' },
  badge: { type: String, default: '' },
  tooltip: { type: String, default: '' }
})

const resolvedLabel = computed(() => props.label || props.title || 'Métrica')

const resolvedValue = computed(() => {
  if (typeof props.amount === 'number' && props.amount !== 0) return props.amount
  if (typeof props.value === 'number') return props.value
  return props.amount || 0
})

const resolvedSubtext = computed(() => props.subtext || props.subtitle || '')

const resolvedType = computed(() => {
  const t = (props.variant || props.type || '').toLowerCase()
  if (t === 'income' || t === 'sales') return 'sales'
  if (t === 'expense' || t === 'expenses') return 'expenses'
  if (t === 'balance') return 'balance'
  if (t === 'pending' || t === 'receivables') return 'receivables'
  return 'sales'
})

const computedEmphasis = computed(() => {
  return props.isEmphasis || resolvedType.value === 'balance'
})

const formattedValue = computed(() => formatCLP(resolvedValue.value))
</script>

<style scoped>
.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: var(--shadow-card);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  position: relative;
  overflow: hidden;
  min-height: 154px;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.stat-card__icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card__icon--sales {
  background-color: var(--color-income-light);
  color: var(--color-income);
}

.stat-card__icon--expenses {
  background-color: var(--color-expense-light);
  color: var(--color-expense);
}

.stat-card__icon--balance {
  background-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.stat-card__icon--receivables {
  background-color: var(--color-warning-light);
  color: var(--color-warning);
}

.stat-card__tags {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.stat-card__trend {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: var(--radius-sm);
  background-color: var(--color-surface-subtle);
  color: var(--color-text-secondary);
}

.trend-up {
  color: var(--color-emerald-700);
  background-color: var(--color-emerald-50);
}

.trend-down {
  color: #b91c1c;
  background-color: #fee2e2;
}

.stat-card__badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: var(--radius-pill);
}

.stat-card__badge--sales {
  background: var(--color-income-light);
  color: var(--color-income);
}

.stat-card__badge--expenses {
  background: var(--color-expense-light);
  color: var(--color-expense);
}

.stat-card__badge--balance {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

.stat-card__badge--receivables {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.stat-card__body {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-card__label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  letter-spacing: 0.01em;
}

.stat-card__value {
  font-size: 1.625rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text);
  line-height: 1.2;
  font-family: var(--font-display);
  margin-top: 2px;
}

.stat-card__subtext {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  line-height: 1.35;
  margin-top: 2px;
}

/* Variante de Énfasis (Saldo del periodo) */
.stat-card--emphasis {
  background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
  border-color: #0d9488;
  color: #ffffff;
}

.stat-card--emphasis .stat-card__label {
  color: #ccfbf1;
}

.stat-card--emphasis .stat-card__value {
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.stat-card--emphasis .stat-card__subtext {
  color: #99f6e4;
}

.stat-card--emphasis .stat-card__trend {
  background-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}
</style>
