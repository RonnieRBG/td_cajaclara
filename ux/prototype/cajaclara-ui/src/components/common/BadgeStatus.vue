<template>
  <span :class="['badge-status', `badge-status--${variantClass}`]">
    <span class="badge-status__dot" aria-hidden="true" />
    <span class="badge-status__text">
      <slot>{{ label }}</slot>
    </span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'pendiente'
  },
  label: {
    type: String,
    default: ''
  }
})

const variantClass = computed(() => {
  const s = (props.status || '').toLowerCase().trim()
  if (s.includes('vencid')) return 'danger'
  if (s.includes('pendient')) return 'warning'
  if (s.includes('pagad') || s.includes('cobrad')) return 'success'
  if (s.includes('venta')) return 'income'
  if (s.includes('compra') || s.includes('gasto')) return 'expense'
  return 'neutral'
})
</script>

<style scoped>
.badge-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  white-space: nowrap;
}

.badge-status__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Variantes Semánticas */
.badge-status--success {
  background-color: var(--color-income-light);
  color: var(--color-income);
  border: 1px solid #a7f3d0;
}
.badge-status--success .badge-status__dot {
  background-color: var(--color-income);
}

.badge-status--warning {
  background-color: var(--color-warning-light);
  color: var(--color-warning);
  border: 1px solid #fde68a;
}
.badge-status--warning .badge-status__dot {
  background-color: var(--color-warning);
}

.badge-status--danger {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
  border: 1px solid #fecaca;
}
.badge-status--danger .badge-status__dot {
  background-color: var(--color-danger);
}

.badge-status--income {
  background-color: var(--color-brand-primary-light);
  color: var(--color-brand-primary);
  border: 1px solid var(--color-brand-primary-border);
}
.badge-status--income .badge-status__dot {
  background-color: var(--color-brand-primary);
}

.badge-status--expense {
  background-color: var(--color-expense-light);
  color: var(--color-expense);
  border: 1px solid #fecdd3;
}
.badge-status--expense .badge-status__dot {
  background-color: var(--color-expense);
}

.badge-status--neutral {
  background-color: var(--color-bg-subtle);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}
.badge-status--neutral .badge-status__dot {
  background-color: var(--color-text-muted);
}
</style>
