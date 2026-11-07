<script setup>
import { computed } from 'vue'
import { formatCLP } from '@/utils/formatters'

const props = defineProps({
  products: {
    type: Array,
    required: true
  }
})

const maxUnits = computed(() => {
  return Math.max(...props.products.map(p => p.unidadesVendidas), 100)
})

const getBarWidth = (units) => {
  return `${Math.round((units / maxUnits.value) * 100)}%`
}
</script>

<template>
  <div class="card top-products-card">
    <div class="card-header">
      <div>
        <h3 class="card-title">Productos más vendidos</h3>
        <p class="card-subtitle">Demanda acumulada del mes</p>
      </div>
      <span class="badge-tag">Top 4</span>
    </div>

    <div class="products-list">
      <div
        v-for="(product, index) in products"
        :key="product.id"
        class="product-item"
      >
        <div class="product-rank" aria-hidden="true">
          #{{ index + 1 }}
        </div>

        <div class="product-content">
          <div class="product-main-row">
            <span class="product-name">{{ product.nombre }}</span>
            <span class="product-total">{{ formatCLP(product.totalVentas) }}</span>
          </div>

          <!-- Progress bar -->
          <div class="progress-track" aria-hidden="true">
            <div
              class="progress-fill"
              :style="{ width: getBarWidth(product.unidadesVendidas) }"
            ></div>
          </div>

          <div class="product-meta">
            <span class="product-units"><strong>{{ product.unidadesVendidas }}</strong> unidades despachadas</span>
            <span class="product-stock" v-if="product.stockComprado">
              📦 Compra reciente: {{ product.stockComprado }} un.
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.top-products-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.card-subtitle {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin: 3px 0 0 0;
  line-height: 1.4;
}

.badge-tag {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--color-primary-700);
  background-color: var(--color-primary-50);
  border: 1px solid var(--color-primary-200);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.products-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.product-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-1) 0;
}

.product-rank {
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--color-text-muted);
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.product-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.product-main-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-2);
}

.product-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-total {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-emerald-700);
  font-family: var(--font-display);
  flex-shrink: 0;
}

.progress-track {
  height: 6px;
  width: 100%;
  background-color: var(--color-slate-100);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary-500) 0%, var(--color-emerald-500) 100%);
  border-radius: var(--radius-full);
  transition: width var(--transition-normal);
}

.product-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.product-units strong {
  color: var(--color-text);
}

.product-stock {
  color: var(--color-primary-700);
  font-weight: 500;
}
</style>
