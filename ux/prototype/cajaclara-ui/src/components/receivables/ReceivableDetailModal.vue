<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { formatCLP, formatDate } from '@/utils/formatters'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  account: { type: Object, default: null }
})

const emit = defineEmits(['close'])
const dialog = ref(null)
const status = computed(() => props.account?.displayStatus || props.account?.status)
let previouslyFocusedElement = null

const close = () => emit('close')

const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }

  if (event.key !== 'Tab' || !dialog.value) return
  const focusable = [...dialog.value.querySelectorAll('button:not([disabled]), a[href]')]
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
  <div v-if="isOpen && account" class="receivable-backdrop" @click.self="close">
    <section
      ref="dialog"
      class="receivable-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="receivable-detail-title"
    >
      <header class="dialog-header">
        <div>
          <span class="dialog-eyebrow">Detalle de cuenta</span>
          <h2 id="receivable-detail-title">{{ account.clientName }}</h2>
        </div>
        <button type="button" class="dialog-close" aria-label="Cerrar detalle" @click="close">×</button>
      </header>

      <dl class="detail-grid">
        <div><dt>Contacto</dt><dd>{{ account.contact }}</dd></div>
        <div><dt>Factura</dt><dd>{{ account.invoiceId }}</dd></div>
        <div><dt>Fecha de emisión</dt><dd>{{ formatDate(account.issuedDate) }}</dd></div>
        <div><dt>Fecha de vencimiento</dt><dd>{{ formatDate(account.dueDate) }}</dd></div>
        <div>
          <dt>Estado</dt>
          <dd><span :class="['detail-status', `detail-status--${status.toLowerCase()}`]">{{ status }}</span></dd>
        </div>
        <div><dt>Monto pendiente</dt><dd>{{ formatCLP(status === 'PAGADA' ? 0 : account.amount) }}</dd></div>
      </dl>

      <section class="detail-products" aria-labelledby="receivable-products-title">
        <h3 id="receivable-products-title">Productos</h3>
        <ul v-if="account.products.length">
          <li v-for="(product, index) in account.products" :key="`${product.name}-${index}`">
            <div>
              <strong>{{ product.name }}</strong>
              <span>{{ product.quantity }} × {{ formatCLP(product.unitPrice) }}</span>
            </div>
            <strong>{{ formatCLP(product.subtotal) }}</strong>
          </li>
        </ul>
        <p v-else>{{ account.description }}</p>
      </section>

      <footer class="dialog-footer">
        <span>{{ status === 'PAGADA' ? 'Total pagado' : 'Monto pendiente' }}</span>
        <strong>{{ formatCLP(account.amount) }}</strong>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.receivable-backdrop { position: fixed; inset: 0; z-index: 1110; display: grid; place-items: center; padding: var(--layout-control-gap); background: rgba(15, 23, 42, .54); }
.receivable-dialog { width: min(38rem, 100%); min-width: var(--content-min-width); max-height: 90vh; overflow-y: auto; padding: var(--layout-card-gap); border: 1px solid var(--color-border); border-radius: var(--radius-xl); background: var(--color-surface); box-shadow: var(--shadow-modal); }
.dialog-header { display: flex; min-width: var(--content-min-width); justify-content: space-between; gap: var(--layout-control-gap); padding-bottom: var(--layout-control-gap); border-bottom: 1px solid var(--color-border); }
.dialog-header > div { min-width: var(--content-min-width); overflow-wrap: anywhere; }
.dialog-eyebrow { color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.dialog-header h2 { margin-top: var(--space-1); color: var(--color-text); font-size: 1.2rem; }
.dialog-close { width: var(--control-min-height); height: var(--control-min-height); flex: 0 0 var(--control-min-height); border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-secondary); font-size: 1.6rem; line-height: 1; }
.detail-grid { display: grid; min-width: var(--content-min-width); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--layout-control-gap); padding: var(--layout-card-gap) 0; }
.detail-grid > div { min-width: var(--content-min-width); }
.detail-grid dt { margin-bottom: var(--space-1); color: var(--color-text-secondary); font-size: .75rem; }
.detail-grid dd { color: var(--color-text); font-size: .88rem; font-weight: 700; overflow-wrap: anywhere; }
.detail-status { font-size: .76rem; }
.detail-status--pendiente { color: var(--color-warning); }
.detail-status--vencida { color: var(--color-danger); }
.detail-status--pagada { color: var(--color-income); }
.detail-products h3 { margin-bottom: var(--layout-control-gap); color: var(--color-text); font-size: .95rem; }
.detail-products ul { list-style: none; border-top: 1px solid var(--color-border); }
.detail-products li { display: flex; min-width: var(--content-min-width); justify-content: space-between; gap: var(--layout-control-gap); padding: var(--layout-control-gap) 0; border-bottom: 1px solid var(--color-border-subtle); }
.detail-products li div { display: flex; min-width: var(--content-min-width); flex-direction: column; gap: var(--space-1); overflow-wrap: anywhere; }
.detail-products li strong { color: var(--color-text); font-size: .84rem; }
.detail-products li span, .detail-products p { color: var(--color-text-secondary); font-size: .8rem; }
.detail-products li > strong { flex: 0 0 auto; }
.dialog-footer { display: flex; min-width: var(--content-min-width); justify-content: space-between; gap: var(--layout-control-gap); margin-top: var(--layout-control-gap); padding: var(--layout-control-gap); border-radius: var(--radius-md); background: var(--color-bg-subtle); }
.dialog-footer span { color: var(--color-text-secondary); }
.dialog-footer strong { color: var(--color-text); }
@media (max-width: 540px) {
  .receivable-dialog { padding: var(--layout-control-gap); }
  .detail-grid { grid-template-columns: 1fr; }
}
</style>
