<script setup>
import { ref, computed } from 'vue'
import { formatCLP } from '@/utils/formatters'

const props = defineProps({
  weeklyData: {
    type: Array,
    required: true
  },
  subtitle: {
    type: String,
    default: 'Comparativa semanal del mes en curso'
  }
})

const hoveredBar = ref(null)
const focusedBar = ref(null)
const selectedBar = ref(null)
const activeBar = computed(() => hoveredBar.value ?? focusedBar.value ?? selectedBar.value)

// Calculate max value to scale chart proportionally
const maxValue = computed(() => {
  let max = 0
  props.weeklyData.forEach(item => {
    const ventas = Number.isFinite(item.ventas) ? Math.max(item.ventas, 0) : 0
    const gastos = Number.isFinite(item.gastos) ? Math.max(item.gastos, 0) : 0
    max = Math.max(max, ventas, gastos)
  })
  return Math.max(Math.min(max * 1.15, Number.MAX_SAFE_INTEGER), 100000)
})

const getBarHeight = (value) => {
  const safeValue = Number.isFinite(value) ? Math.max(value, 0) : 0
  const height = Math.min(safeValue, maxValue.value) / maxValue.value * 100
  return `${Math.round(height)}%`
}

const showTooltip = (week, type, value) => {
  hoveredBar.value = { ...week, type, value }
}

const totalVentas = computed(() => {
  return props.weeklyData.reduce((acc, curr) => acc + curr.ventas, 0)
})

const totalGastos = computed(() => {
  return props.weeklyData.reduce((acc, curr) => acc + curr.gastos, 0)
})
</script>

<template>
  <div class="card cash-chart-card">
    <div class="chart-header">
      <div>
        <h3 class="chart-title">Entradas y salidas de dinero</h3>
        <p class="chart-subtitle">{{ subtitle }}</p>
      </div>

      <div class="chart-legend">
        <div class="legend-item">
          <span class="legend-dot dot-ventas"></span>
          <span class="legend-label">Ventas (Entradas): <strong>{{ formatCLP(totalVentas) }}</strong></span>
        </div>
        <div class="legend-item">
          <span class="legend-dot dot-gastos"></span>
          <span class="legend-label">Compras y gastos (Salidas): <strong>{{ formatCLP(totalGastos) }}</strong></span>
        </div>
      </div>
    </div>

    <!-- Chart visualization -->
    <div class="chart-container" role="region" aria-label="Gráfico de barras de flujo semanal">
      <div class="chart-plot">
        <div class="chart-grid-lines" aria-hidden="true">
          <div class="grid-line"><span>{{ formatCLP(maxValue) }}</span></div>
          <div class="grid-line"><span>{{ formatCLP(maxValue * 0.66) }}</span></div>
          <div class="grid-line"><span>{{ formatCLP(maxValue * 0.33) }}</span></div>
          <div class="grid-line baseline"><span>$0</span></div>
        </div>

        <div class="chart-columns">
          <div
            v-for="(week, index) in weeklyData"
            :key="week.semana"
            class="chart-week-group"
          >
            <!-- Bars Container -->
            <div class="bars-pair">
              <!-- Ventas Bar -->
              <div
                class="bar-wrapper"
                @mouseenter="showTooltip(week, 'venta', week.ventas)"
                @mouseleave="hoveredBar = null"
                @focus="focusedBar = { ...week, type: 'venta', value: week.ventas }"
                @blur="focusedBar = null"
                @click="selectedBar = { ...week, type: 'venta', value: week.ventas }"
                tabindex="0"
                :aria-label="`${week.semana}: Ventas de ${formatCLP(week.ventas)}`"
              >
                <div
                  class="chart-bar chart-bar--income"
                  :style="{ height: getBarHeight(week.ventas) }"
                >
                  <span class="bar-value-top">{{ formatCLP(week.ventas) }}</span>
                </div>
              </div>

              <!-- Gastos Bar -->
              <div
                class="bar-wrapper"
                @mouseenter="showTooltip(week, 'gasto', week.gastos)"
                @mouseleave="hoveredBar = null"
                @focus="focusedBar = { ...week, type: 'gasto', value: week.gastos }"
                @blur="focusedBar = null"
                @click="selectedBar = { ...week, type: 'gasto', value: week.gastos }"
                tabindex="0"
                :aria-label="`${week.semana}: Compras y gastos de ${formatCLP(week.gastos)}`"
              >
                <div
                  class="chart-bar chart-bar--expense"
                  :style="{ height: getBarHeight(week.gastos) }"
                >
                  <span class="bar-value-top">{{ formatCLP(week.gastos) }}</span>
                </div>
              </div>
            </div>

            <!-- Column Label -->
            <div class="week-label">{{ week.semana }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dynamic hover hint/tooltip for micro-businesses -->
    <div class="chart-footer-note">
      <div v-if="activeBar" class="active-tooltip">
        <span class="tooltip-badge" :class="activeBar.type === 'venta' ? 'badge-ingreso' : 'badge-salida'">
          {{ activeBar.type === 'venta' ? 'Entrada / Venta' : 'Salida / Gasto' }}
        </span>
        <span class="tooltip-text">
          <strong>{{ activeBar.semana }}</strong>: {{ formatCLP(activeBar.value) }}
        </span>
      </div>
      <div v-else class="default-hint">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
        <span>Enfoca, pasa el cursor o pulsa en una barra para ver el detalle de cada semana.</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cash-chart-card {
  display: flex;
  min-width: var(--content-min-width);
  flex-direction: column;
  gap: var(--space-5);
  height: 100%;
}

.chart-header {
  display: flex;
  min-width: var(--content-min-width);
  height: auto;
  flex: 0 0 auto;
  flex-direction: column;
  gap: var(--space-3);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

@media (min-width: 640px) {
  .chart-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
  }
}

.chart-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.chart-subtitle {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: var(--space-1) 0 0 0;
  line-height: 1.4;
}

.chart-legend {
  display: flex;
  min-width: var(--content-min-width);
  flex-wrap: wrap;
  gap: var(--space-5);
  font-size: 0.825rem;
}

.legend-item {
  display: flex;
  min-width: var(--content-min-width);
  align-items: center;
  gap: var(--space-2);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-sm);
}

.dot-ventas {
  background-color: var(--color-income);
}

.dot-gastos {
  background-color: var(--color-expense);
}

.legend-label {
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}

.legend-label strong {
  color: var(--color-text);
}

/* Chart Canvas */
.chart-container {
  display: flex;
  min-height: 0;
  width: 100%;
  min-width: var(--content-min-width);
  flex: 1;
  margin-top: var(--space-2);
  align-items: center;
  justify-content: center;
}

.chart-plot {
  position: relative;
  width: 100%;
  height: 220px;
  flex: 0 1 220px;
}

.chart-grid-lines {
  position: absolute;
  inset: 0 0 28px 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
}

.grid-line {
  border-top: 1px dashed var(--color-border);
  position: relative;
}

.grid-line span {
  position: absolute;
  right: 0;
  top: -10px;
  font-size: 0.7rem;
  color: var(--color-text-muted);
  background-color: var(--color-surface);
  padding-left: var(--space-2);
}

.grid-line.baseline {
  border-top-style: solid;
  border-top-color: var(--color-border-strong);
}

.chart-columns {
  position: relative;
  height: 100%;
  display: flex;
  min-width: var(--content-min-width);
  justify-content: space-around;
  align-items: flex-end;
  padding: 0 var(--space-4) 28px var(--space-4);
  z-index: 1;
}

.chart-week-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20%;
  min-width: 0;
  height: 100%;
  justify-content: flex-end;
  position: relative;
}

.bars-pair {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 100%;
  width: 100%;
  max-width: 68px;
  justify-content: center;
}

.bar-wrapper {
  position: relative;
  width: 50%;
  height: 100%;
  display: flex;
  align-items: flex-end;
  cursor: pointer;
  outline: none;
}

.chart-bar {
  width: 100%;
  min-height: 6px;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  opacity: 1;
  visibility: visible;
  transform: scaleY(1);
  transform-origin: bottom;
  transition: filter var(--transition-normal);
  position: relative;
}

.chart-bar--income {
  background-color: var(--color-income);
}

.chart-bar--expense {
  background-color: var(--color-expense);
}

.chart-bar:hover,
.bar-wrapper:focus-visible .chart-bar {
  filter: brightness(0.94);
  outline: 2px solid var(--color-brand-primary);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .chart-bar {
    transition: none;
    transform: scaleY(1);
  }
}

.bar-value-top {
  display: none;
}

.week-label {
  position: absolute;
  bottom: -24px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.chart-footer-note {
  height: auto;
  flex: 0 0 auto;
  padding-top: var(--space-4);
  margin-top: var(--space-2);
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
}

.default-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.active-tooltip {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.85rem;
  color: var(--color-text);
  animation: fadeIn 0.15s ease-in;
}

.tooltip-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.badge-ingreso {
  background-color: var(--color-emerald-100);
  color: var(--color-emerald-800);
}

.badge-salida {
  background-color: var(--color-amber-100);
  color: var(--color-amber-800);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(2px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 480px) {
  .chart-plot {
    height: 180px;
    flex-basis: 180px;
  }
  .bars-pair {
    gap: 3px;
  }
  .week-label {
    font-size: 0.7rem;
  }
}

@media (max-width: 1279px) {
  .cash-chart-card {
    height: auto;
  }

  .chart-container {
    min-height: auto;
  }
}
</style>
