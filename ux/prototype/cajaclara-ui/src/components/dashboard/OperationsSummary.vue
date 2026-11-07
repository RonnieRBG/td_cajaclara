<script setup>
import { computed } from 'vue'

const props = defineProps({
  summary: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <div class="card summary-card">
    <div class="summary-header">
      <h3 class="summary-title">Resumen de actividad</h3>
      <span class="period-pill">Octubre 2026</span>
    </div>

    <div class="metrics-grid">
      <!-- Total Ventas -->
      <div class="metric-item">
        <div class="metric-icon icon-ventas" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
        </div>
        <div class="metric-info">
          <span class="metric-value">{{ summary.totalVentas }}</span>
          <span class="metric-label">Ventas realizadas</span>
        </div>
      </div>

      <!-- Compras y gastos -->
      <div class="metric-item">
        <div class="metric-icon icon-gastos" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
            <polyline points="17 18 23 18 23 12" />
          </svg>
        </div>
        <div class="metric-info">
          <span class="metric-value">{{ summary.totalGastos }}</span>
          <span class="metric-label">Compras y gastos</span>
        </div>
      </div>

      <!-- Unidades vendidas -->
      <div class="metric-item">
        <div class="metric-icon icon-unidades" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m7.5 4.27 9 5.15" />
            <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
            <path d="m3.3 7 8.7 5 8.7-5" />
            <path d="M12 22V12" />
          </svg>
        </div>
        <div class="metric-info">
          <span class="metric-value">{{ summary.unidadesVendidas }}</span>
          <span class="metric-label">Unidades despachadas</span>
        </div>
      </div>

      <!-- Cuentas pendientes -->
      <div class="metric-item">
        <div class="metric-icon icon-pendientes" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        </div>
        <div class="metric-info">
          <span class="metric-value">{{ summary.cuentasPendientes }}</span>
          <span class="metric-label">Cobros pendientes</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.summary-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.summary-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.period-pill {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-primary-700);
  background-color: var(--color-primary-50);
  border: 1px solid var(--color-primary-200);
  padding: 3px 8px;
  border-radius: var(--radius-full);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.metric-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background-color: var(--color-surface-subtle);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.metric-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-ventas {
  background-color: var(--color-emerald-100);
  color: var(--color-emerald-700);
}

.icon-gastos {
  background-color: var(--color-amber-100);
  color: var(--color-amber-700);
}

.icon-unidades {
  background-color: var(--color-primary-100);
  color: var(--color-primary-700);
}

.icon-pendientes {
  background-color: #fee2e2;
  color: #b91c1c;
}

.metric-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.metric-value {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--color-text);
  line-height: 1.1;
  font-family: var(--font-display);
}

.metric-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-weight: 500;
  margin-top: 2px;
}

@media (max-width: 480px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
