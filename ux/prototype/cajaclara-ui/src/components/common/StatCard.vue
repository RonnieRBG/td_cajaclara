<template>
  <article :class="['stat-card', { 'stat-card--emphasis': isEmphasis }]">
    <div class="stat-card__header">
      <div class="stat-card__icon-wrapper" :class="`stat-card__icon--${type}`" aria-hidden="true">
        <!-- Icono según tipo -->
        <svg v-if="type === 'sales'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5" />
          <polyline points="5 12 12 5 19 12" />
        </svg>
        <svg v-else-if="type === 'expenses'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19" />
          <polyline points="19 12 12 19 5 12" />
        </svg>
        <svg v-else-if="type === 'balance'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="4" width="20" height="16" rx="2" />
          <line x1="2" y1="10" x2="22" y2="10" />
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      </div>

      <span v-if="badge" class="stat-card__badge" :class="`stat-card__badge--${type}`">
        {{ badge }}
      </span>
    </div>

    <div class="stat-card__body">
      <span class="stat-card__label">{{ label }}</span>
      <div class="stat-card__value">
        {{ formattedValue }}
      </div>
      <p class="stat-card__subtext">{{ subtext }}</p>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { formatCLP } from '@/utils/formatters'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: Number,
    required: true
  },
  subtext: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'neutral', // 'sales', 'expenses', 'balance', 'receivables'
    validator: v => ['sales', 'expenses', 'balance', 'receivables', 'neutral'].includes(v)
  },
  isEmphasis: {
    type: Boolean,
    default: false
  },
  badge: {
    type: String,
    default: ''
  }
})

const formattedValue = computed(() => formatCLP(props.value))
</script>

<style scoped>
.stat-card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: var(--shadow-card);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
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
  background-color: var(--color-brand-primary-light);
  color: var(--color-brand-primary);
}

.stat-card__icon--receivables {
  background-color: var(--color-warning-light);
  color: var(--color-warning);
}

.stat-card__badge {
  font-size: 11px;
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
  background: #f0fdfa;
  color: var(--color-brand-primary);
}

.stat-card__badge--receivables {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.stat-card__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-card__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.stat-card__value {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text-main);
  line-height: 1.2;
}

.stat-card__subtext {
  font-size: 12px;
  color: var(--color-text-muted);
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

.stat-card--emphasis .stat-card__icon-wrapper {
  background-color: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-card--emphasis .stat-card__badge {
  background-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}
</style>
