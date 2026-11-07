<script setup>
import { ref, watch, computed } from 'vue'
import { formatCLP } from '@/utils/formatters'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  initialType: {
    type: String,
    default: 'VENTA_PAGADA'
  },
  initialData: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['close', 'success'])

const currentType = ref(props.initialType)
const concepto = ref('')
const cantidad = ref(1)
const monto = ref(null)
const contraparte = ref('')
const medioPago = ref('Efectivo')
const submitted = ref(false)

const operationTypes = [
  { id: 'VENTA_PAGADA', label: 'Venta pagada', badge: 'Ingreso inmediato' },
  { id: 'VENTA_PENDIENTE', label: 'Venta por cobrar (fiado)', badge: 'Pendiente' },
  { id: 'COMPRA', label: 'Compra de productos', badge: 'Salida de caja' },
  { id: 'GASTO', label: 'Otro gasto', badge: 'Salida operativa' }
]

watch(() => props.initialType, (newVal) => {
  if (newVal) currentType.value = newVal
})

watch(() => props.initialData, (newVal) => {
  if (newVal) {
    concepto.value = newVal.detalle || newVal.concepto || ''
    monto.value = newVal.monto || null
    contraparte.value = newVal.cliente || newVal.clienteProveedor || ''
  }
}, { immediate: true })

watch(() => props.isOpen, (open) => {
  if (open) {
    submitted.value = false
    if (!props.initialData) {
      if (currentType.value === 'VENTA_PAGADA') {
        concepto.value = 'Aceite vegetal de 1 litro'
        cantidad.value = 3
        monto.value = 9000
        contraparte.value = 'Almacén San Pedro'
        medioPago.value = 'Efectivo'
      } else if (currentType.value === 'VENTA_PENDIENTE') {
        concepto.value = 'Aceite vegetal de 1 litro'
        cantidad.value = 4
        monto.value = 12000
        contraparte.value = 'Claudia Rojas'
        medioPago.value = 'Por cobrar'
      } else if (currentType.value === 'COMPRA') {
        concepto.value = 'Aceite vegetal de 1 litro (12 botellas)'
        cantidad.value = 12
        monto.value = 24000
        contraparte.value = 'Distribuidora Central'
        medioPago.value = 'Efectivo'
      } else {
        concepto.value = 'Transporte para retirar mercadería'
        cantidad.value = 1
        monto.value = 3500
        contraparte.value = 'Flete Don Mario'
        medioPago.value = 'Efectivo'
      }
    }
  }
})

const modalTitle = computed(() => {
  switch (currentType.value) {
    case 'VENTA_PAGADA': return 'Registrar venta cobrada'
    case 'VENTA_PENDIENTE': return 'Registrar venta por cobrar (fiada)'
    case 'COMPRA': return 'Registrar compra de productos'
    case 'GASTO': return 'Registrar otro gasto del negocio'
    default: return 'Registrar movimiento de caja'
  }
})

const handleTypeChange = (typeId) => {
  currentType.value = typeId
}

const handleSubmit = () => {
  submitted.value = true
  setTimeout(() => {
    emit('success', {
      tipo: currentType.value,
      concepto: concepto.value,
      monto: monto.value,
      contraparte: contraparte.value
    })
    emit('close')
  }, 1200)
}
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-dialog" role="dialog" aria-modal="true" :aria-labelledby="'modal-title'">
      <!-- Header -->
      <div class="modal-header">
        <div>
          <h2 id="modal-title" class="modal-title">{{ modalTitle }}</h2>
          <p class="modal-subtitle">Almacén La Esquina • Caja diaria</p>
        </div>
        <button
          type="button"
          class="modal-close-btn"
          @click="$emit('close')"
          aria-label="Cerrar ventana"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- Type Switcher Tabs -->
      <div class="operation-tabs">
        <button
          v-for="op in operationTypes"
          :key="op.id"
          type="button"
          :class="['tab-btn', { active: currentType === op.id }]"
          @click="handleTypeChange(op.id)"
        >
          {{ op.label }}
        </button>
      </div>

      <!-- Body Form -->
      <form @submit.prevent="handleSubmit" class="modal-body">
        <div v-if="submitted" class="success-banner">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          <div>
            <strong>¡Movimiento registrado con éxito!</strong>
            <p>Se actualizó la caja del periodo (Simulación de prototipo UX).</p>
          </div>
        </div>

        <div v-else class="form-fields">
          <!-- Concepto -->
          <div class="form-group">
            <label for="input-concepto" class="form-label">Producto o concepto</label>
            <input
              id="input-concepto"
              v-model="concepto"
              type="text"
              class="form-input"
              placeholder="Ej: Aceite vegetal 1L o Flete mercadería"
              required
            />
          </div>

          <!-- Unidades & Monto Row -->
          <div class="form-row">
            <div class="form-group flex-1">
              <label for="input-cantidad" class="form-label">Cantidad / Unidades</label>
              <input
                id="input-cantidad"
                v-model.number="cantidad"
                type="number"
                min="1"
                class="form-input"
                required
              />
            </div>

            <div class="form-group flex-2">
              <label for="input-monto" class="form-label">Monto total ($ CLP)</label>
              <input
                id="input-monto"
                v-model.number="monto"
                type="number"
                min="0"
                step="100"
                class="form-input font-bold"
                placeholder="Ej: 9000"
                required
              />
            </div>
          </div>

          <!-- Cliente / Proveedor -->
          <div class="form-group">
            <label for="input-contraparte" class="form-label">
              {{ currentType.includes('VENTA') ? 'Cliente' : 'Proveedor o destinatario' }}
            </label>
            <input
              id="input-contraparte"
              v-model="contraparte"
              type="text"
              class="form-input"
              :placeholder="currentType.includes('VENTA') ? 'Nombre del cliente (ej: Claudia Rojas)' : 'Proveedor o repartidor'"
              required
            />
          </div>

          <!-- Medio de Pago -->
          <div class="form-group" v-if="currentType !== 'VENTA_PENDIENTE'">
            <label class="form-label">Medio de pago</label>
            <div class="payment-pills">
              <button
                type="button"
                :class="['payment-pill', { active: medioPago === 'Efectivo' }]"
                @click="medioPago = 'Efectivo'"
              >
                💵 Efectivo
              </button>
              <button
                type="button"
                :class="['payment-pill', { active: medioPago === 'Transferencia' }]"
                @click="medioPago = 'Transferencia'"
              >
                📱 Transferencia
              </button>
              <button
                type="button"
                :class="['payment-pill', { active: medioPago === 'Débito' }]"
                @click="medioPago = 'Débito'"
              >
                💳 Débito
              </button>
            </div>
          </div>

          <div v-else class="pending-notice">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <div>
              <strong>Venta anotada como cuenta por cobrar</strong>
              <p>Quedará registrada en la lista de cobros pendientes hasta que el cliente pague.</p>
            </div>
          </div>
        </div>

        <!-- Footer actions -->
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            @click="$emit('close')"
          >
            Cancelar
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="submitted || !monto || !concepto"
          >
            <span>Guardar en caja</span>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(3px);
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  animation: fadeIn 0.15s ease-out;
}

.modal-dialog {
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  width: 100%;
  max-width: 520px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.modal-subtitle {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin: 2px 0 0 0;
}

.modal-close-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: var(--space-1);
  border-radius: var(--radius-sm);
}

.modal-close-btn:hover {
  background-color: var(--color-surface-hover);
  color: var(--color-text);
}

.operation-tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  background-color: var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

@media (min-width: 480px) {
  .operation-tabs {
    grid-template-columns: repeat(4, 1fr);
  }
}

.tab-btn {
  background-color: var(--color-surface-subtle);
  border: none;
  padding: var(--space-2) var(--space-2);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  text-align: center;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  background-color: var(--color-surface);
  color: var(--color-primary-700);
}

.tab-btn.active {
  background-color: var(--color-surface);
  color: var(--color-primary-800);
  font-weight: 700;
  box-shadow: inset 0 -2px 0 var(--color-primary-600);
}

.modal-body {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.form-row {
  display: flex;
  gap: var(--space-3);
}

.flex-1 { flex: 1; }
.flex-2 { flex: 2; }

.form-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text);
}

.form-input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: 0.925rem;
  color: var(--color-text);
  background-color: var(--color-surface);
  outline: none;
  transition: border-color var(--transition-fast);
}

.form-input:focus {
  border-color: var(--color-primary-600);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.font-bold {
  font-weight: 700;
  font-family: var(--font-display);
}

.payment-pills {
  display: flex;
  gap: var(--space-2);
}

.payment-pill {
  flex: 1;
  background-color: var(--color-surface-subtle);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-2);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.payment-pill.active {
  background-color: var(--color-primary-50);
  border-color: var(--color-primary-500);
  color: var(--color-primary-800);
  font-weight: 600;
}

.pending-notice {
  display: flex;
  gap: var(--space-3);
  background-color: var(--color-amber-50);
  border: 1px solid var(--color-amber-200);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  color: var(--color-amber-900);
  font-size: 0.825rem;
  line-height: 1.35;
}

.pending-notice p {
  margin: 2px 0 0 0;
  font-size: 0.78rem;
  color: var(--color-amber-800);
}

.success-banner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  background-color: var(--color-emerald-50);
  border: 1px solid var(--color-emerald-300);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  color: var(--color-emerald-900);
}

.success-banner p {
  margin: 4px 0 0 0;
  font-size: 0.825rem;
  color: var(--color-emerald-700);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
