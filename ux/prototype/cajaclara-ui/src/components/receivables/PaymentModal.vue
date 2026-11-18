<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { formatCLP, getLocalDateString } from '@/utils/formatters'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  account: { type: Object, default: null },
  mode: { type: String, default: 'pay' },
  isSaving: { type: Boolean, default: false },
  error: { type: String, default: '' }
})

const emit = defineEmits(['close', 'confirm'])
const dialog = ref(null)
const paymentDate = ref('')
let previouslyFocusedElement = null

const close = () => {
  if (!props.isSaving) emit('close')
}

const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }

  if (event.key !== 'Tab' || !dialog.value) return
  const focusable = [...dialog.value.querySelectorAll('button:not([disabled]), input:not([disabled]), select:not([disabled])')]
  if (!focusable.length) return
  if (event.shiftKey && document.activeElement === focusable[0]) {
    event.preventDefault()
    focusable.at(-1).focus()
  } else if (!event.shiftKey && document.activeElement === focusable.at(-1)) {
    event.preventDefault()
    focusable[0].focus()
  }
}

const confirmPayment = () => {
  emit('confirm', { date: paymentDate.value })
}

watch(() => props.isOpen, async (open) => {
  if (open) {
    previouslyFocusedElement = document.activeElement
    paymentDate.value = ''
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
  <div v-if="isOpen && account" class="payment-backdrop">
    <section
      ref="dialog"
      class="payment-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="payment-title"
      aria-describedby="payment-help"
    >
      <header class="dialog-header">
        <div>
          <span class="dialog-eyebrow">{{ mode === 'pay' ? 'Confirmación de pago' : 'Reversión de pago' }}</span>
          <h2 id="payment-title">{{ mode === 'pay' ? 'Registrar pago completo' : 'Revertir pago registrado' }}</h2>
          <p id="payment-help">
            {{ mode === 'pay'
              ? 'El pago cancelará el total pendiente. La fecha es opcional; si se omite, la API usa hoy.'
              : 'La cuenta volverá a pendiente o vencida según su fecha de vencimiento.' }}
          </p>
        </div>
        <button type="button" class="dialog-close" aria-label="Cerrar registro de pago" :disabled="isSaving" @click="close">×</button>
      </header>

      <form class="payment-form" :aria-busy="isSaving" @submit.prevent="confirmPayment">
        <dl class="payment-summary">
          <div><dt>Cliente</dt><dd>{{ account.clientName }}</dd></div>
          <div><dt>Factura</dt><dd>{{ account.invoiceId }}</dd></div>
          <div><dt>{{ mode === 'pay' ? 'Monto pendiente' : 'Monto de la cuenta' }}</dt><dd>{{ formatCLP(account.amount) }}</dd></div>
        </dl>

        <label v-if="mode === 'pay'" class="form-field">
          <span>Fecha de pago <small>(opcional)</small></span>
          <input
            v-model="paymentDate"
            type="date"
            :min="account.issuedDate"
            :max="getLocalDateString()"
          />
        </label>

        <p v-if="error" class="form-error" role="alert">{{ error }}</p>

        <footer class="dialog-actions">
          <button type="button" class="btn btn-secondary" :disabled="isSaving" @click="close">Cancelar</button>
          <button type="submit" class="btn btn-primary" :disabled="isSaving">
            {{ isSaving ? 'Guardando…' : mode === 'pay' ? 'Confirmar pago completo' : 'Confirmar reversión' }}
          </button>
        </footer>
      </form>
    </section>
  </div>
</template>

<style scoped>
.payment-backdrop { position: fixed; inset: 0; z-index: 1120; display: grid; place-items: center; padding: var(--layout-control-gap); background: rgba(15, 23, 42, .56); }
.payment-dialog { width: min(34rem, 100%); min-width: var(--content-min-width); max-height: 90vh; overflow-y: auto; padding: var(--layout-card-gap); border: 1px solid var(--color-border); border-radius: var(--radius-xl); background: var(--color-surface); box-shadow: var(--shadow-modal); }
.dialog-header { display: flex; min-width: var(--content-min-width); justify-content: space-between; gap: var(--layout-control-gap); padding-bottom: var(--layout-control-gap); border-bottom: 1px solid var(--color-border); }
.dialog-header > div { min-width: var(--content-min-width); }
.dialog-eyebrow { color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.dialog-header h2 { margin-top: var(--space-1); color: var(--color-text); font-size: 1.2rem; }
.dialog-header p { margin-top: var(--space-1); color: var(--color-text-secondary); font-size: .82rem; }
.dialog-close { width: var(--control-min-height); height: var(--control-min-height); flex: 0 0 var(--control-min-height); border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-secondary); font-size: 1.6rem; line-height: 1; }
.payment-form { display: flex; min-width: var(--content-min-width); flex-direction: column; gap: var(--layout-control-gap); padding-top: var(--layout-card-gap); }
.payment-summary { display: grid; min-width: var(--content-min-width); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--layout-control-gap); padding: var(--layout-control-gap); border-radius: var(--radius-md); background: var(--color-bg-subtle); }
.payment-summary > div { min-width: var(--content-min-width); }
.payment-summary dt { color: var(--color-text-secondary); font-size: .75rem; }
.payment-summary dd { margin-top: var(--space-1); color: var(--color-text); font-size: .86rem; font-weight: 700; overflow-wrap: anywhere; }
.payment-summary > div:last-child { grid-column: 1 / -1; }
.form-field { display: flex; min-width: var(--content-min-width); flex-direction: column; gap: var(--space-1); color: var(--color-text-secondary); font-size: .8rem; font-weight: 700; }
.form-field small { font-weight: 500; }
.form-field input { width: 100%; min-width: var(--content-min-width); min-height: var(--control-min-height); padding: var(--space-2) var(--layout-control-gap); border: 1px solid var(--color-border-strong); border-radius: var(--radius-sm); background: var(--color-surface); color: var(--color-text); font: inherit; font-weight: 500; }
.form-error { padding: var(--layout-control-gap); border-radius: var(--radius-sm); background: var(--color-danger-light); color: var(--color-danger); font-size: .82rem; }
.dialog-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: var(--layout-control-gap); margin-top: var(--space-2); padding-top: var(--layout-control-gap); border-top: 1px solid var(--color-border); }
.dialog-actions .btn { min-width: 0; }
@media (max-width: 540px) {
  .payment-dialog { padding: var(--layout-control-gap); }
  .payment-summary { grid-template-columns: 1fr; }
  .payment-summary > div:last-child { grid-column: auto; }
  .dialog-actions { flex-direction: column-reverse; }
  .dialog-actions .btn { width: 100%; }
}
</style>
