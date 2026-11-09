<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { clients, expenseCategories, productCatalog } from '@/data/operationsMock'
import { formatCLP, getLocalDateString } from '@/utils/formatters'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  initialMode: { type: String, default: 'venta' },
  initialData: { type: Object, default: null }
})

const emit = defineEmits(['close', 'save'])

const dialog = ref(null)
const activeMode = ref('venta')
const selectedClient = ref('')
const channel = ref('Física')
const paymentStatus = ref('Pagada')
const paymentDueDate = ref('')
const operationDate = ref('')
const productLines = ref([])
const expenseKind = ref('insumo')
const expenseProductId = ref('')
const expenseCategory = ref(expenseCategories[0])
const expenseAmount = ref(null)
const expenseDescription = ref('')
const isDirty = ref(false)
const lineSequence = ref(0)
let previouslyFocusedElement = null

const saleTotal = computed(() => productLines.value.reduce(
  (sum, line) => sum + Math.max(0, Number(line.quantity) || 0) * Math.max(0, Number(line.unitPrice) || 0),
  0
))
const isSale = computed(() => activeMode.value === 'venta')
const formTitle = computed(() => {
  if (isSale.value) return 'Nueva venta'
  return expenseKind.value === 'insumo' ? 'Registrar compra o gasto de insumo' : 'Registrar otro gasto'
})
const canSubmit = computed(() => {
  if (isSale.value) {
    return selectedClient.value &&
      productLines.value.length > 0 &&
      productLines.value.every(line => line.productId && Number(line.quantity) > 0 && Number(line.unitPrice) >= 0) &&
      saleTotal.value > 0 &&
      (paymentStatus.value !== 'Pendiente' || paymentDueDate.value)
  }
  return Boolean(operationDate.value) &&
    Number(expenseAmount.value) > 0 &&
    (expenseKind.value === 'insumo' ? Boolean(expenseProductId.value) : Boolean(expenseCategory.value && expenseDescription.value.trim()))
})

const addProductLine = () => {
  lineSequence.value += 1
  const firstProduct = productCatalog[0]
  productLines.value.push({
    key: lineSequence.value,
    productId: firstProduct.id,
    quantity: 1,
    unitPrice: firstProduct.unitPrice
  })
  isDirty.value = true
}

const updateLineProduct = (line) => {
  const product = productCatalog.find(item => item.id === line.productId)
  if (product) line.unitPrice = product.unitPrice
}

const resetForm = () => {
  activeMode.value = ['gasto', 'compra', 'otro-gasto'].includes(props.initialMode) ? 'gasto' : 'venta'
  const initialClient = props.initialData?.cliente || props.initialData?.contraparte || ''
  selectedClient.value = clients.find(client => client.name === initialClient)?.id || clients[0]?.id || ''
  channel.value = 'Física'
  paymentStatus.value = props.initialMode === 'venta-pendiente' ? 'Pendiente' : 'Pagada'
  paymentDueDate.value = ''
  operationDate.value = props.initialData?.date || getLocalDateString()
  const initialProductName = props.initialData?.detalle || props.initialData?.concepto || ''
  const initialProduct = productCatalog.find(product => (
    initialProductName.toLocaleLowerCase('es-CL').includes(product.name.toLocaleLowerCase('es-CL'))
  )) || productCatalog.find(product => (
    product.name.toLocaleLowerCase('es-CL').includes(initialProductName.toLocaleLowerCase('es-CL'))
  )) || productCatalog[0]
  lineSequence.value = 0
  productLines.value = [{
    key: ++lineSequence.value,
    productId: initialProduct?.id || '',
    quantity: Number(props.initialData?.cantidad) || 1,
    unitPrice: Number(props.initialData?.monto) || initialProduct?.unitPrice || 0
  }]
  expenseKind.value = props.initialMode === 'otro-gasto' ? 'otro' : 'insumo'
  expenseProductId.value = productCatalog[0]?.id || ''
  expenseCategory.value = expenseCategories[0]
  expenseAmount.value = null
  expenseDescription.value = ''
  isDirty.value = false
}

const focusFirstControl = async () => {
  await nextTick()
  dialog.value?.querySelector('[data-autofocus]')?.focus()
}

const close = () => {
  if (isDirty.value && !window.confirm('¿Quieres cerrar sin guardar esta operación?')) return
  emit('close')
}

const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }
  if (event.key !== 'Tab' || !dialog.value) return

  const focusable = [...dialog.value.querySelectorAll(
    'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled])'
  )]
  if (!focusable.length) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(() => props.isOpen, async (open) => {
  if (open) {
    previouslyFocusedElement = document.activeElement
    resetForm()
    await focusFirstControl()
    document.addEventListener('keydown', handleKeydown)
  } else {
    document.removeEventListener('keydown', handleKeydown)
    previouslyFocusedElement?.focus?.()
  }
}, { immediate: true, flush: 'post' })

watch(() => props.initialMode, (mode) => {
  if (props.isOpen) {
    activeMode.value = ['gasto', 'compra', 'otro-gasto'].includes(mode) ? 'gasto' : 'venta'
    paymentStatus.value = mode === 'venta-pendiente' ? 'Pendiente' : 'Pagada'
    expenseKind.value = mode === 'otro-gasto' ? 'otro' : 'insumo'
  }
})

watch(paymentStatus, (status) => {
  if (status !== 'Pendiente') paymentDueDate.value = ''
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})

const submit = () => {
  if (!canSubmit.value) return

  if (isSale.value) {
    const client = clients.find(item => item.id === selectedClient.value)
    const products = productLines.value.map(line => {
      const product = productCatalog.find(item => item.id === line.productId)
      const quantity = Number(line.quantity)
      const unitPrice = Number(line.unitPrice)
      return {
        name: product?.name || 'Producto',
        quantity,
        unitPrice,
        subtotal: quantity * unitPrice
      }
    })
    emit('save', {
      date: operationDate.value,
      type: 'Venta',
      customerOrSupplier: client?.name || '',
      description: products.map(product => product.name).join(', '),
      products,
      channel: channel.value,
      amount: saleTotal.value,
      paymentStatus: paymentStatus.value,
      paymentDueDate: paymentStatus.value === 'Pendiente' ? paymentDueDate.value : null
    })
    return
  }

  const purchase = expenseKind.value === 'insumo'
  const selectedProduct = productCatalog.find(item => item.id === expenseProductId.value)
  emit('save', {
    date: operationDate.value,
    type: purchase ? 'Compra' : 'Otro gasto',
    customerOrSupplier: purchase ? 'Proveedor no indicado' : expenseCategory.value,
    description: expenseDescription.value.trim() || (purchase ? 'Compra de insumo' : expenseCategory.value),
    products: purchase ? [{
      name: selectedProduct?.name || 'Insumo',
      quantity: null,
      unitPrice: null,
      subtotal: Number(expenseAmount.value)
    }] : [],
    channel: '—',
    amount: Number(expenseAmount.value),
    paymentStatus: 'Registrada',
    paymentDueDate: null
  })
}
</script>

<template>
  <div v-if="isOpen" class="operation-modal-backdrop">
    <section
      ref="dialog"
      class="operation-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="operation-form-title"
      aria-describedby="operation-form-help"
    >
      <header class="operation-modal__header">
        <div>
          <span class="operation-modal__eyebrow">Almacén La Esquina</span>
          <h2 id="operation-form-title">{{ formTitle }}</h2>
          <p id="operation-form-help">Completa los datos para revisar la operación antes de confirmarla.</p>
        </div>
        <button type="button" class="icon-button" aria-label="Cerrar formulario" @click="close">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m18 6-12 12M6 6l12 12" /></svg>
        </button>
      </header>

      <div class="operation-mode-switch" role="group" aria-label="Tipo de operación">
        <button
          type="button"
          :class="{ 'is-active': isSale }"
          :aria-pressed="isSale"
          @click="activeMode = 'venta'; isDirty = true"
        >Venta</button>
        <button
          type="button"
          :class="{ 'is-active': !isSale }"
          :aria-pressed="!isSale"
          @click="activeMode = 'gasto'; isDirty = true"
        >Compra o gasto</button>
      </div>

      <form class="operation-form" @submit.prevent="submit" @input="isDirty = true" @change="isDirty = true">
        <template v-if="isSale">
          <div class="form-grid">
            <label class="field">
              <span>Cliente</span>
              <select v-model="selectedClient" required data-autofocus>
                <option v-for="client in clients" :key="client.id" :value="client.id">{{ client.name }}</option>
              </select>
            </label>
            <label class="field">
              <span>Fecha de la venta</span>
              <input v-model="operationDate" type="date" required />
            </label>
            <fieldset class="field field--wide channel-field">
              <legend>Canal de venta</legend>
              <label><input v-model="channel" type="radio" value="Física" /> Física</label>
              <label><input v-model="channel" type="radio" value="En línea" /> En línea</label>
            </fieldset>
          </div>

          <section class="line-items" aria-labelledby="sale-products-title">
            <div class="section-heading">
              <div>
                <h3 id="sale-products-title">Productos</h3>
                <p>Añade uno o varios productos a la venta.</p>
              </div>
              <button type="button" class="text-action" @click="addProductLine">+ Añadir producto</button>
            </div>

            <div v-for="(line, index) in productLines" :key="line.key" class="product-line">
              <label class="field product-line__product">
                <span>Producto {{ index + 1 }}</span>
                <select v-model="line.productId" required :data-autofocus="index === 0" @change="updateLineProduct(line)">
                  <option v-for="product in productCatalog" :key="product.id" :value="product.id">{{ product.name }}</option>
                </select>
              </label>
              <label class="field">
                <span>Cantidad</span>
                <input v-model.number="line.quantity" type="number" min="1" step="1" required />
              </label>
              <label class="field">
                <span>Precio unitario</span>
                <input v-model.number="line.unitPrice" type="number" min="0" step="1" required />
              </label>
              <div class="line-subtotal">
                <span>Subtotal</span>
                <strong>{{ formatCLP((Number(line.quantity) || 0) * (Number(line.unitPrice) || 0)) }}</strong>
              </div>
              <button
                type="button"
                class="icon-button remove-line"
                :aria-label="`Eliminar producto ${index + 1}`"
                :disabled="productLines.length === 1"
                @click="productLines.splice(index, 1); isDirty = true"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6m4-6v6M5 7l1 14h12l1-14M9 7V4h6v3" /></svg>
              </button>
            </div>
          </section>

          <div class="form-grid">
            <fieldset class="field field--wide channel-field">
              <legend>Estado de pago</legend>
              <label><input v-model="paymentStatus" type="radio" value="Pagada" /> Pagada</label>
              <label><input v-model="paymentStatus" type="radio" value="Pendiente" /> Pendiente</label>
            </fieldset>
            <label v-if="paymentStatus === 'Pendiente'" class="field">
              <span>Fecha esperada de pago</span>
              <input v-model="paymentDueDate" type="date" required aria-describedby="payment-date-help" />
              <small id="payment-date-help">Indica cuándo esperas recibir el pago.</small>
            </label>
          </div>

          <section class="sale-review" aria-label="Resumen de la venta">
            <div>
              <span>Resumen</span>
              <strong>{{ productLines.length }} {{ productLines.length === 1 ? 'producto' : 'productos' }}</strong>
            </div>
            <div class="sale-review__total">
              <span>Total de la venta</span>
              <strong>{{ formatCLP(saleTotal) }}</strong>
            </div>
          </section>
        </template>

        <template v-else>
          <fieldset class="field channel-field">
            <legend>¿Qué vas a registrar?</legend>
            <label><input v-model="expenseKind" type="radio" value="insumo" /> Compra o gasto de insumo</label>
            <label><input v-model="expenseKind" type="radio" value="otro" /> Otro gasto</label>
          </fieldset>

          <div class="form-grid">
            <label v-if="expenseKind === 'insumo'" class="field field--wide">
              <span>Producto o insumo</span>
              <select v-model="expenseProductId" required data-autofocus>
                <option v-for="product in productCatalog" :key="product.id" :value="product.id">{{ product.name }}</option>
              </select>
            </label>
            <label v-else class="field field--wide">
              <span>Categoría</span>
              <select v-model="expenseCategory" required data-autofocus>
                <option v-for="category in expenseCategories" :key="category" :value="category">{{ category }}</option>
              </select>
            </label>
            <label class="field">
              <span>Fecha</span>
              <input v-model="operationDate" type="date" required />
            </label>
            <label class="field">
              <span>Monto (CLP)</span>
              <input v-model.number="expenseAmount" type="number" min="1" step="1" required />
            </label>
            <label class="field field--wide">
              <span>Descripción <template v-if="expenseKind === 'otro'">(obligatoria)</template><template v-else>(opcional)</template></span>
              <textarea v-model="expenseDescription" rows="3" :required="expenseKind === 'otro'"></textarea>
            </label>
          </div>

          <section class="sale-review" aria-label="Resumen del gasto">
            <div>
              <span>Tipo</span>
              <strong>{{ expenseKind === 'insumo' ? 'Compra o gasto de insumo' : expenseCategory }}</strong>
            </div>
            <div class="sale-review__total">
              <span>Monto a registrar</span>
              <strong>{{ formatCLP(Number(expenseAmount) || 0) }}</strong>
            </div>
          </section>
        </template>

        <footer class="operation-modal__footer">
          <button type="button" class="btn btn-secondary" @click="close">Cancelar</button>
          <button type="submit" class="btn btn-primary" :disabled="!canSubmit">Revisar y confirmar</button>
        </footer>
      </form>
    </section>
  </div>
</template>

<style scoped>
.operation-modal-backdrop { position: fixed; inset: 0; z-index: 1100; display: grid; place-items: center; padding: 20px; background: rgba(15, 23, 42, .56); }
.operation-modal { width: min(760px, 100%); max-height: min(92vh, 900px); overflow: auto; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-xl); box-shadow: var(--shadow-modal); }
.operation-modal__header { display: flex; justify-content: space-between; gap: 20px; padding: 24px 28px 20px; border-bottom: 1px solid var(--color-border); }
.operation-modal__eyebrow { color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.operation-modal__header h2 { margin: 4px 0; color: var(--color-text); font-size: 1.35rem; }
.operation-modal__header p, .section-heading p { color: var(--color-text-secondary); font-size: .84rem; }
.icon-button { display: inline-grid; place-items: center; width: 44px; height: 44px; flex: 0 0 44px; border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-secondary); }
.icon-button:hover { background: var(--color-bg-subtle); }
.icon-button svg { width: 19px; height: 19px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.operation-mode-switch { display: flex; gap: 8px; padding: 16px 28px 0; }
.operation-mode-switch button { min-height: 44px; padding: 8px 14px; border: 1px solid var(--color-border); border-radius: var(--radius-pill); color: var(--color-text-secondary); font-size: .84rem; font-weight: 700; }
.operation-mode-switch button.is-active { color: var(--color-brand-primary); background: var(--color-brand-primary-light); border-color: var(--color-brand-primary-border); }
.operation-form { display: flex; flex-direction: column; gap: 20px; padding: 20px 28px 24px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.field { display: flex; min-width: 0; flex-direction: column; gap: 7px; color: var(--color-text); font-size: .82rem; font-weight: 700; }
.field--wide { grid-column: 1 / -1; }
.field input:not([type="radio"]), .field select, .field textarea { width: 100%; min-height: 44px; padding: 10px 12px; border: 1px solid var(--color-border-strong); border-radius: var(--radius-sm); background: var(--color-surface); color: var(--color-text); font: inherit; font-weight: 500; }
.field textarea { resize: vertical; }
.field small { color: var(--color-text-secondary); font-size: .75rem; font-weight: 500; }
.channel-field { display: flex; flex-flow: row wrap; gap: 10px 22px; border: 0; }
.channel-field legend { width: 100%; margin-bottom: 8px; font-size: .82rem; font-weight: 700; }
.channel-field label { display: inline-flex; min-height: 44px; align-items: center; gap: 8px; color: var(--color-text-secondary); font-size: .84rem; font-weight: 600; }
.channel-field input { width: 17px; height: 17px; accent-color: var(--color-brand-primary); }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.section-heading h3 { margin-bottom: 2px; font-size: .98rem; }
.text-action { min-height: 44px; padding: 6px 10px; color: var(--color-brand-primary); font-size: .82rem; font-weight: 800; }
.product-line { display: grid; grid-template-columns: minmax(180px, 2fr) minmax(85px, .7fr) minmax(120px, 1fr) minmax(100px, auto) 44px; gap: 10px; align-items: end; padding: 12px 0; border-top: 1px solid var(--color-border-subtle); }
.line-subtotal { display: flex; min-height: 44px; flex-direction: column; justify-content: center; gap: 2px; color: var(--color-text-secondary); font-size: .72rem; }
.line-subtotal strong { color: var(--color-text); font-size: .85rem; }
.remove-line { color: var(--color-expense); }
.remove-line:disabled { cursor: not-allowed; opacity: .45; }
.sale-review { display: flex; justify-content: space-between; gap: 16px; padding: 16px; border: 1px solid var(--color-brand-primary-border); border-radius: var(--radius-md); background: var(--color-brand-primary-light); }
.sale-review > div { display: flex; flex-direction: column; gap: 4px; }
.sale-review span { color: var(--color-text-secondary); font-size: .76rem; }
.sale-review strong { color: var(--color-text); font-size: .9rem; }
.sale-review__total { text-align: right; }
.sale-review__total strong { color: var(--color-brand-primary); font-size: 1.15rem; }
.operation-modal__footer { display: flex; justify-content: flex-end; gap: 10px; padding-top: 16px; border-top: 1px solid var(--color-border); }
.operation-modal__footer .btn { min-height: 44px; }
.operation-modal__footer .btn:disabled { cursor: not-allowed; opacity: .55; }
@media (max-width: 640px) {
  .operation-modal-backdrop { padding: 0; align-items: end; }
  .operation-modal { max-height: 96dvh; border-radius: var(--radius-lg) var(--radius-lg) 0 0; }
  .operation-modal__header, .operation-form { padding-left: 18px; padding-right: 18px; }
  .operation-mode-switch { padding-left: 18px; padding-right: 18px; }
  .form-grid { grid-template-columns: 1fr; }
  .field--wide { grid-column: auto; }
  .product-line { grid-template-columns: minmax(0, 1fr) 44px; gap: 10px; }
  .product-line .field:first-child { grid-column: 1 / -1; }
  .line-subtotal { grid-column: 1; }
  .remove-line { grid-column: 2; grid-row: 2; }
  .sale-review { align-items: flex-start; }
  .operation-modal__footer { flex-direction: column-reverse; }
  .operation-modal__footer .btn { width: 100%; }
}
</style>
