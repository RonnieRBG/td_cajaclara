<script setup>
import { useRouter } from 'vue-router'
import { formatCLP } from '@/utils/formatters'
import BadgeStatus from '@/components/common/BadgeStatus.vue'

const props = defineProps({
  collections: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['pay-collection'])

const router = useRouter()

const goToCollections = () => {
  router.push('/cobros')
}

const handlePay = (item) => {
  emit('pay-collection', item)
}
</script>

<template>
  <div class="card priority-card">
    <div class="card-header">
      <div class="header-left">
        <div class="icon-wrap" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M12 2v20" />
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <div>
          <h3 class="card-title">Cobros que requieren atención</h3>
          <p class="card-subtitle">Cuentas por cobrar con vencimiento próximo o superado</p>
        </div>
      </div>

      <button type="button" class="btn btn-secondary btn-sm" @click="goToCollections">
        <span>Ver todas (7)</span>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>
    </div>

    <!-- Collection Items List -->
    <div class="collections-list">
      <div
        v-for="item in collections"
        :key="item.id"
        :class="['collection-item', { 'item-overdue': item.estado === 'VENCIDA' }]"
      >
        <div class="client-column">
          <div class="client-avatar" aria-hidden="true">
            {{ item.cliente.slice(0, 2).toUpperCase() }}
          </div>
          <div class="client-info">
            <span class="client-name">{{ item.cliente }}</span>
            <span class="client-detail">{{ item.detalle }} • Doc: {{ item.documento }}</span>
          </div>
        </div>

        <div class="due-column">
          <span :class="['due-tag', item.estado === 'VENCIDA' ? 'due-overdue' : 'due-soon']">
            {{ item.vencimientoTexto }}
          </span>
          <BadgeStatus :status="item.estado" />
        </div>

        <div class="amount-column">
          <span class="collection-amount">{{ formatCLP(item.monto) }}</span>
          <button
            type="button"
            class="btn btn-success btn-xs pay-btn"
            @click="handlePay(item)"
            :title="`Registrar pago de ${item.cliente}`"
          >
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>Registrar cobro</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.priority-card {
  display: flex;
  min-width: var(--content-min-width);
  flex-direction: column;
  gap: var(--space-4);
  border-left: 4px solid var(--color-amber-500);
}

.card-header {
  display: flex;
  min-width: var(--content-min-width);
  flex-wrap: wrap;
  flex-direction: column;
  gap: var(--space-3);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

@media (min-width: 640px) {
  .card-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.header-left {
  display: flex;
  min-width: var(--content-min-width);
  flex: 1 1 14rem;
  align-items: center;
  gap: var(--space-3);
}

.icon-wrap {
  width: 36px;
  height: 36px;
  background-color: var(--color-amber-100);
  color: var(--color-amber-700);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  overflow-wrap: anywhere;
}

.card-subtitle {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin: 3px 0 0 0;
  line-height: 1.4;
}

.collections-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.collection-item {
  display: flex;
  min-width: var(--content-min-width);
  flex-wrap: wrap;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background-color: var(--color-surface-subtle);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

@media (min-width: 640px) {
  .collection-item {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.collection-item:hover {
  background-color: var(--color-surface-hover);
  border-color: var(--color-border-strong);
}

.collection-item.item-overdue {
  background-color: #fef2f2;
  border-color: #fecaca;
}

.client-column {
  display: flex;
  min-width: var(--content-min-width);
  flex: 1 1 13rem;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
}

.client-avatar {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-full);
  background-color: var(--color-primary-100);
  color: var(--color-primary-700);
  font-weight: 700;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.item-overdue .client-avatar {
  background-color: #fee2e2;
  color: #b91c1c;
}

.client-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}

.client-name {
  font-size: 0.925rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.client-detail {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  overflow-wrap: anywhere;
}

.due-column {
  display: flex;
  min-width: var(--content-min-width);
  flex: 1 1 11rem;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.due-tag {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
}

.due-soon {
  color: var(--color-amber-800);
  background-color: var(--color-amber-100);
}

.due-overdue {
  color: #991b1b;
  background-color: #fee2e2;
  font-weight: 700;
}

.amount-column {
  display: flex;
  min-width: var(--content-min-width);
  flex: 1 1 10rem;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-shrink: 0;
}

@media (min-width: 640px) {
  .amount-column {
    justify-content: flex-end;
  }
}

.collection-amount {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text);
  font-family: var(--font-display);
}

.btn-xs {
  padding: 4px 10px;
  font-size: 0.78rem;
}

.pay-btn {
  white-space: normal;
}
</style>
