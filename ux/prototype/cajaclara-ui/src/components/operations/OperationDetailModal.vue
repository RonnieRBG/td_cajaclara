<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { formatCLP, formatDate } from '@/utils/formatters'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  operation: { type: Object, default: null }
})

const emit = defineEmits(['close'])
const dialog = ref(null)
let previouslyFocusedElement = null

const close = () => emit('close')

const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }
  if (event.key !== 'Tab' || !dialog.value) return
  const focusable = [...dialog.value.querySelectorAll('button:not([disabled])')]
  if (!focusable.length) return
  if (event.shiftKey && document.activeElement === focusable[0]) {
    event.preventDefault()
    focusable.at(-1).focus()
  } else if (!event.shiftKey && document.activeElement === focusable.at(-1)) {
    event.preventDefault()
    focusable[0].focus()
  }
}

watch(() => props.isOpen, async (open) => {
  if (open) {
    previouslyFocusedElement = document.activeElement
    await nextTick()
    dialog.value?.querySelector('button')?.focus()
    document.addEventListener('keydown', handleKeydown)
  } else {
    document.removeEventListener('keydown', handleKeydown)
    previouslyFocusedElement?.focus?.()
  }
})

onBeforeUnmount(() => document.removeEventListener('keydown', handleKeydown))
</script>

<template>
  <div v-if="isOpen && operation" class="detail-backdrop" @click.self="close">
    <section
      ref="dialog"
      class="detail-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="operation-detail-title"
    >
      <header class="detail-header">
        <div>
          <span class="detail-kicker">Detalle de operación</span>
          <h2 id="operation-detail-title">{{ operation.type }} · {{ operation.invoiceId }}</h2>
        </div>
        <button type="button" class="detail-close" aria-label="Cerrar detalle" @click="close">×</button>
      </header>

      <dl class="detail-facts">
        <div><dt>Fecha</dt><dd>{{ formatDate(operation.date) }}<template v-if="operation.time"> · {{ operation.time }}</template></dd></div>
        <div><dt>Cliente o proveedor</dt><dd>{{ operation.customerOrSupplier || 'No informado' }}</dd></div>
        <div><dt>Canal</dt><dd>{{ operation.channel || 'No aplica' }}</dd></div>
        <div><dt>Estado</dt><dd>{{ operation.displayStatus || operation.paymentStatus }}</dd></div>
        <div v-if="operation.paymentDueDate"><dt>Fecha esperada de pago</dt><dd>{{ formatDate(operation.paymentDueDate) }}</dd></div>
      </dl>

      <section v-if="operation.products?.length" class="detail-products" aria-labelledby="detail-products-title">
        <h3 id="detail-products-title">Productos</h3>
        <ul>
          <li v-for="(product, index) in operation.products" :key="`${product.name}-${index}`">
            <div>
              <strong>{{ product.name }}</strong>
              <span v-if="product.quantity != null">{{ product.quantity }} × {{ formatCLP(product.unitPrice) }}</span>
              <span v-else>Detalle de cantidad y precio unitario no informado</span>
            </div>
            <strong>{{ formatCLP(product.subtotal ?? operation.amount) }}</strong>
          </li>
        </ul>
      </section>
      <p v-else class="detail-description">{{ operation.description }}</p>

      <footer class="detail-total">
        <span>Total</span>
        <strong>{{ formatCLP(operation.amount) }}</strong>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.detail-backdrop { position: fixed; inset: 0; z-index: 1110; display: grid; place-items: center; padding: var(--layout-control-gap); background: rgba(15, 23, 42, .54); }
.detail-dialog { width: min(35rem, 100%); min-width: var(--content-min-width); max-height: 90vh; overflow-y: auto; padding: var(--layout-card-gap); border: 1px solid var(--color-border); border-radius: var(--radius-xl); background: var(--color-surface); box-shadow: var(--shadow-modal); }
.detail-header { display: flex; min-width: var(--content-min-width); justify-content: space-between; gap: var(--layout-control-gap); padding-bottom: var(--layout-control-gap); border-bottom: 1px solid var(--color-border); }
.detail-header > div { min-width: var(--content-min-width); overflow-wrap: anywhere; }
.detail-kicker { color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.detail-header h2 { margin-top: 4px; font-size: 1.15rem; }
.detail-close { width: var(--control-min-height); height: var(--control-min-height); flex: 0 0 var(--control-min-height); border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-secondary); font-size: 1.6rem; line-height: 1; }
.detail-facts { display: grid; min-width: var(--content-min-width); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--layout-control-gap); padding: var(--layout-card-gap) 0; }
.detail-facts div { min-width: 0; }
.detail-facts dt { margin-bottom: 3px; color: var(--color-text-secondary); font-size: .75rem; }
.detail-facts dd { color: var(--color-text); font-size: .88rem; font-weight: 700; overflow-wrap: anywhere; }
.detail-products h3 { margin-bottom: 10px; font-size: .95rem; }
.detail-products ul { list-style: none; border-top: 1px solid var(--color-border); }
.detail-products li { display: flex; min-width: var(--content-min-width); justify-content: space-between; gap: var(--layout-control-gap); padding: var(--layout-control-gap) 0; border-bottom: 1px solid var(--color-border-subtle); }
.detail-products li div { display: flex; min-width: var(--content-min-width); flex-direction: column; gap: var(--space-1); overflow-wrap: anywhere; }
.detail-products li > strong { flex: 0 0 auto; }
.detail-products li strong { font-size: .84rem; }
.detail-products li span { color: var(--color-text-secondary); font-size: .77rem; }
.detail-description { padding: var(--layout-control-gap) 0; color: var(--color-text-secondary); font-size: .88rem; overflow-wrap: anywhere; }
.detail-total { display: flex; min-width: var(--content-min-width); justify-content: space-between; gap: var(--layout-control-gap); margin-top: var(--layout-control-gap); padding: var(--layout-control-gap); border-radius: var(--radius-md); background: var(--color-bg-subtle); }
.detail-total span { color: var(--color-text-secondary); }
.detail-total strong { color: var(--color-text); font-size: 1.1rem; }
@media (max-width: 540px) { .detail-dialog { padding: var(--layout-control-gap); } .detail-facts { grid-template-columns: 1fr; gap: var(--layout-control-gap); } }
</style>
