<script setup>
import { useRouter } from 'vue-router'
import { formatCLP, formatDateTime } from '@/utils/formatters'
import BadgeStatus from '@/components/common/BadgeStatus.vue'

const props = defineProps({
  operations: {
    type: Array,
    required: true
  }
})

const router = useRouter()

const goToOperations = () => {
  router.push('/operaciones')
}

const getOperationIcon = (tipo) => {
  if (tipo === 'VENTA') return 'arrow-up-right'
  if (tipo === 'COMPRA') return 'shopping-bag'
  return 'arrow-down-left'
}
</script>

<template>
  <div class="card recent-operations-card">
    <div class="card-header">
      <div class="header-left">
        <div class="icon-wrap" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
        </div>
        <div>
          <h3 class="card-title">Últimos movimientos de caja</h3>
          <p class="card-subtitle">Registros recientes de ventas, compras y gastos</p>
        </div>
      </div>

      <button type="button" class="btn btn-secondary btn-sm" @click="goToOperations">
        <span>Ver todos (167)</span>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>
    </div>

    <!-- Operations Table / List -->
    <div class="operations-table-wrap">
      <table class="operations-table" role="table">
        <thead>
          <tr>
            <th scope="col">Movimiento / Detalle</th>
            <th scope="col">Contraparte</th>
            <th scope="col">Canal / Pago</th>
            <th scope="col">Estado</th>
            <th scope="col" class="text-right">Monto</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="op in operations" :key="op.id" class="operation-row">
            <!-- Movimiento / Detalle -->
            <td>
              <div class="op-cell-main">
                <div
                  :class="[
                    'op-icon-badge',
                    op.tipo === 'VENTA' ? 'badge-in' : op.tipo === 'COMPRA' ? 'badge-buy' : 'badge-out'
                  ]"
                  aria-hidden="true"
                >
                  <svg v-if="op.tipo === 'VENTA'" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="7" y1="17" x2="17" y2="7" />
                    <polyline points="7 7 17 7 17 17" />
                  </svg>
                  <svg v-else-if="op.tipo === 'COMPRA'" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
                    <line x1="3" y1="6" x2="21" y2="6" />
                    <path d="M16 10a4 4 0 0 1-8 0" />
                  </svg>
                  <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="17" y1="7" x2="7" y2="17" />
                    <polyline points="17 17 7 17 7 7" />
                  </svg>
                </div>
                <div class="op-title-block">
                  <span class="op-concept">{{ op.concepto }}</span>
                  <span class="op-detail">{{ op.detalle }} • {{ formatDateTime(op.fecha) }}</span>
                </div>
              </div>
            </td>

            <!-- Contraparte -->
            <td>
              <span class="op-party">{{ op.clienteProveedor }}</span>
            </td>

            <!-- Canal / Pago -->
            <td>
              <span class="op-channel-tag">{{ op.canal }}</span>
            </td>

            <!-- Estado -->
            <td>
              <BadgeStatus :status="op.estado" />
            </td>

            <!-- Monto -->
            <td class="text-right">
              <span
                :class="[
                  'op-amount',
                  op.tipo === 'VENTA' && op.estado === 'PAGADA' ? 'amount-positive' : '',
                  op.tipo === 'VENTA' && op.estado === 'PENDIENTE' ? 'amount-pending' : '',
                  op.tipo === 'COMPRA' || op.tipo === 'GASTO' ? 'amount-negative' : ''
                ]"
              >
                {{ (op.tipo === 'VENTA' && op.estado === 'PAGADA') ? '+' : '' }}{{ (op.tipo === 'COMPRA' || op.tipo === 'GASTO') ? '-' : '' }}{{ formatCLP(op.monto) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.recent-operations-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding-bottom: var(--space-3);
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
  align-items: center;
  gap: var(--space-3);
}

.icon-wrap {
  width: 36px;
  height: 36px;
  background-color: var(--color-primary-100);
  color: var(--color-primary-700);
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
}

.card-subtitle {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin: 2px 0 0 0;
}

.operations-table-wrap {
  overflow-x: auto;
  margin: 0 calc(var(--space-4) * -1);
  padding: 0 var(--space-4);
}

.operations-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 680px;
}

.operations-table th {
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  text-transform: uppercase;
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.operations-table td {
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border);
  vertical-align: middle;
}

.operation-row:hover td {
  background-color: var(--color-surface-subtle);
}

.operation-row:last-child td {
  border-bottom: none;
}

.op-cell-main {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.op-icon-badge {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.badge-in {
  background-color: var(--color-emerald-100);
  color: var(--color-emerald-700);
}

.badge-buy {
  background-color: var(--color-primary-100);
  color: var(--color-primary-700);
}

.badge-out {
  background-color: #fee2e2;
  color: #b91c1c;
}

.op-title-block {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.op-concept {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
}

.op-detail {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.op-party {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.op-channel-tag {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  background-color: var(--color-surface-subtle);
  border: 1px solid var(--color-border);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  display: inline-block;
}

.op-amount {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  white-space: nowrap;
}

.amount-positive {
  color: var(--color-emerald-700);
}

.amount-negative {
  color: #b91c1c;
}

.amount-pending {
  color: var(--color-amber-700);
}

.text-right {
  text-align: right;
}
</style>
