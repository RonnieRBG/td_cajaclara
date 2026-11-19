<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import {
  createClient,
  createExpense,
  createSale,
  getClientOptions,
  getProductOptions
} from '@/services/operationsService'
import { formatCLP, getLocalDateString } from '@/utils/formatters'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  initialMode: { type: String, default: 'venta' }
})

const emit = defineEmits(['close', 'saved'])

const dialog = ref(null)
const activeMode = ref('venta')
const clients = ref([])
const products = ref([])
const selectedClient = ref('')
const clientSearch = ref('')
const productSearch = ref('')
const channel = ref('Física')
const isCredit = ref(false)
const paymentDueDate = ref('')
const operationDate = ref('')
const productLines = ref([])
const expenseProductId = ref('')
const expenseAmount = ref(null)
const isDirty = ref(false)
const lineSequence = ref(0)
const isOptionsLoading = ref(false)
const optionsError = ref('')
const isSubmitting = ref(false)
const submitError = ref('')
const isClientFormOpen = ref(false)
const clientName = ref('')
const clientContact = ref('')
const isClientSaving = ref(false)
const clientFormError = ref('')
const clientSavedMessage = ref('')
const clientFieldErrors = ref({ name: '', contact: '' })
let previouslyFocusedElement = null
let clientSearchTimeout
let productSearchTimeout
let clientRequestSequence = 0
let productRequestSequence = 0
let pendingOptionRequests = 0

const saleTotal = computed(() => productLines.value.reduce(
  (sum, line) => sum + Math.max(0, Number(line.quantity) || 0) * Math.max(0, Number(line.unitPrice) || 0),
  0
))
const isSale = computed(() => activeMode.value === 'venta')
const formTitle = computed(() => isSale.value ? 'Nueva venta' : 'Registrar gasto en insumos')
const visibleClients = computed(() => {
  const query = clientSearch.value.trim().toLocaleLowerCase('es-CL')
  return clients.value.filter((client) => (
    String(client.id) === String(selectedClient.value) ||
    !query ||
    `${client.name} ${client.contact || client.phone || ''}`.toLocaleLowerCase('es-CL').includes(query)
  ))
})
const visibleProducts = computed(() => {
  const query = productSearch.value.trim().toLocaleLowerCase('es-CL')
  return products.value.filter((product) => (
    productLines.value.some((line) => String(line.productId) === String(product.id)) ||
    String(expenseProductId.value) === String(product.id) ||
    !query ||
    `${product.name} ${product.category}`.toLocaleLowerCase('es-CL').includes(query)
  ))
})
const selectedExpenseProduct = computed(() => (
  products.value.find((product) => String(product.id) === String(expenseProductId.value))
))
const canSubmit = computed(() => {
  if (isSale.value) {
    return selectedClient.value &&
      productLines.value.length > 0 &&
      productLines.value.every(line => (
        line.productId &&
        Number.isInteger(Number(line.quantity)) &&
        Number(line.quantity) > 0 &&
        Number(line.quantity) <= 100000 &&
        Number.isInteger(Number(line.unitPrice)) &&
        Number(line.unitPrice) > 0 &&
        Number.isInteger(Number(line.unitCost)) &&
        Number(line.unitCost) > 0
      )) &&
      productLines.value.length <= 200 &&
      Boolean(operationDate.value) &&
      saleTotal.value > 0 &&
      (!isCredit.value || (
        paymentDueDate.value &&
        paymentDueDate.value >= operationDate.value
      ))
  }
  return Boolean(expenseProductId.value) &&
    Number.isInteger(Number(expenseAmount.value)) &&
    Number(expenseAmount.value) > 0
})

function mergeOptions(current, incoming) {
  const optionsById = new Map(current.map((option) => [String(option.id), option]))
  incoming.forEach((option) => optionsById.set(String(option.id), option))
  return [...optionsById.values()]
}

async function loadOptions() {
  const clientSequence = ++clientRequestSequence
  const productSequence = ++productRequestSequence
  pendingOptionRequests += 1
  isOptionsLoading.value = true
  optionsError.value = ''

  try {
    const [clientOptions, productOptions] = await Promise.all([
      getClientOptions(),
      getProductOptions()
    ])
    if (clientSequence === clientRequestSequence) {
      clients.value = mergeOptions(clients.value, clientOptions)
    }
    if (productSequence === productRequestSequence) {
      products.value = mergeOptions(products.value, productOptions)
    }
  } catch (error) {
    optionsError.value = error instanceof Error ? error.message : 'No se pudieron cargar las opciones.'
  } finally {
    pendingOptionRequests = Math.max(0, pendingOptionRequests - 1)
    isOptionsLoading.value = pendingOptionRequests > 0
  }
}

async function searchClients() {
  const requestSequence = ++clientRequestSequence
  pendingOptionRequests += 1
  isOptionsLoading.value = true
  optionsError.value = ''
  try {
    const result = await getClientOptions(clientSearch.value)
    if (requestSequence === clientRequestSequence) clients.value = mergeOptions(clients.value, result)
  } catch (error) {
    if (requestSequence === clientRequestSequence) {
      optionsError.value = error instanceof Error ? error.message : 'No se pudieron buscar clientes.'
    }
  } finally {
    pendingOptionRequests = Math.max(0, pendingOptionRequests - 1)
    isOptionsLoading.value = pendingOptionRequests > 0
  }
}

async function searchProducts() {
  const requestSequence = ++productRequestSequence
  pendingOptionRequests += 1
  isOptionsLoading.value = true
  optionsError.value = ''
  try {
    const result = await getProductOptions(productSearch.value)
    if (requestSequence === productRequestSequence) products.value = mergeOptions(products.value, result)
  } catch (error) {
    if (requestSequence === productRequestSequence) {
      optionsError.value = error instanceof Error ? error.message : 'No se pudieron buscar productos.'
    }
  } finally {
    pendingOptionRequests = Math.max(0, pendingOptionRequests - 1)
    isOptionsLoading.value = pendingOptionRequests > 0
  }
}

watch(clientSearch, () => {
  window.clearTimeout(clientSearchTimeout)
  clientSearchTimeout = window.setTimeout(searchClients, 250)
})

watch(productSearch, () => {
  window.clearTimeout(productSearchTimeout)
  productSearchTimeout = window.setTimeout(searchProducts, 250)
})

const addProductLine = () => {
  lineSequence.value += 1
  productLines.value.push({
    key: lineSequence.value,
    productId: '',
    quantity: 1,
    unitPrice: '',
    unitCost: ''
  })
  isDirty.value = true
}

const updateLineProduct = (line) => {
  const product = products.value.find((item) => String(item.id) === String(line.productId))
  line.unitPrice = product?.suggestedPrice ?? ''
  line.unitCost = product?.suggestedCost ?? ''
  isDirty.value = true
}

const getProduct = (line) => products.value.find((item) => String(item.id) === String(line.productId))

const resetForm = () => {
  activeMode.value = ['gasto', 'compra', 'otro-gasto'].includes(props.initialMode) ? 'gasto' : 'venta'
  selectedClient.value = ''
  clientSearch.value = ''
  productSearch.value = ''
  channel.value = 'Física'
  isCredit.value = props.initialMode === 'venta-pendiente'
  paymentDueDate.value = ''
  operationDate.value = getLocalDateString()
  lineSequence.value = 0
  productLines.value = []
  expenseProductId.value = ''
  expenseAmount.value = null
  submitError.value = ''
  isClientFormOpen.value = false
  clientName.value = ''
  clientContact.value = ''
  clientFormError.value = ''
  clientSavedMessage.value = ''
  clientFieldErrors.value = { name: '', contact: '' }
  isDirty.value = false
  void loadOptions()
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
    isCredit.value = mode === 'venta-pendiente'
  }
})

watch(isCredit, (credit) => {
  if (!credit) paymentDueDate.value = ''
})

async function saveClient() {
  clientFormError.value = ''
  clientSavedMessage.value = ''
  clientFieldErrors.value = { name: '', contact: '' }
  if (!clientName.value.trim() || !clientContact.value.trim()) {
    clientFieldErrors.value = {
      name: clientName.value.trim() ? '' : 'Ingresa el nombre del cliente.',
      contact: clientContact.value.trim() ? '' : 'Ingresa un contacto.'
    }
    return
  }

  try {
    isClientSaving.value = true
    const savedClient = await createClient({
      name: clientName.value,
      contact: clientContact.value
    })
    clients.value = mergeOptions(clients.value, [savedClient])
    selectedClient.value = savedClient.id
    clientName.value = ''
    clientContact.value = ''
    isClientFormOpen.value = false
    clientSavedMessage.value = 'Cliente guardado y seleccionado.'
    isDirty.value = true
  } catch (error) {
    clientSavedMessage.value = ''
    const fieldErrors = error?.validationErrors || {}
    clientFieldErrors.value = {
      name: fieldErrors.nombre || fieldErrors.name || '',
      contact: fieldErrors.contacto || fieldErrors.contact || ''
    }
    clientFormError.value = error instanceof Error ? error.message : 'No se pudo guardar el cliente.'
  } finally {
    isClientSaving.value = false
  }
}

async function submit() {
  if (!canSubmit.value) return
  submitError.value = ''
  isSubmitting.value = true

  try {
    if (isSale.value) {
      const payload = {
        id_cliente: selectedClient.value,
        fecha: operationDate.value,
        tipo_compra: channel.value,
        items: productLines.value.map((line) => ({
          id_producto: line.productId,
          cantidad: Number(line.quantity),
          precio_venta: Number(line.unitPrice),
          costo_venta: Number(line.unitCost)
        }))
      }
      if (isCredit.value) {
        payload.por_cobrar = true
        payload.fecha_vencimiento = paymentDueDate.value
      }
      const savedOperation = await createSale(payload)
      emit('saved', { type: 'sale', operation: savedOperation })
    } else {
      const payload = {
        id_producto: expenseProductId.value,
        monto: Number(expenseAmount.value)
      }
      if (operationDate.value) payload.fecha = operationDate.value
      const savedOperation = await createExpense(payload)
      emit('saved', { type: 'expense', operation: savedOperation })
    }
    emit('close')
  } catch (error) {
    submitError.value = error instanceof Error ? error.message : 'No se pudo guardar la operación.'
  } finally {
    isSubmitting.value = false
  }
}

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
  window.clearTimeout(clientSearchTimeout)
  window.clearTimeout(productSearchTimeout)
})
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
          <p id="operation-form-help">Completa los datos requeridos para registrar la operación.</p>
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
        >Registrar venta</button>
        <button
          type="button"
          :class="{ 'is-active': !isSale }"
          :aria-pressed="!isSale"
          @click="activeMode = 'gasto'; isDirty = true"
        >Gasto en insumos</button>
      </div>

      <div v-if="optionsError" class="modal-error" role="alert">
        <span>{{ optionsError }}</span>
        <button type="button" class="text-action" @click="loadOptions">Reintentar carga de opciones</button>
      </div>
      <p v-else-if="isOptionsLoading" class="modal-status" role="status">Cargando clientes y productos…</p>

      <form class="operation-form" @submit.prevent="submit" @input="isDirty = true" @change="isDirty = true">
        <template v-if="isSale">
          <div class="form-grid">
            <label class="field field--wide">
              <span>Cliente</span>
              <input
                v-model="clientSearch"
                type="search"
                autocomplete="off"
                placeholder="Buscar cliente por nombre o contacto"
                aria-label="Buscar clientes"
                data-autofocus
              />
              <select v-model="selectedClient" required aria-label="Seleccionar cliente">
                <option value="" disabled>Selecciona un cliente</option>
                <option v-for="client in visibleClients" :key="client.id" :value="client.id">
                  {{ client.name }} · {{ client.contact || client.phone }}
                </option>
              </select>
              <small v-if="!visibleClients.length && !isOptionsLoading" class="modal-status">
                No hay clientes para esta búsqueda. Puedes crear uno.
              </small>
              <button type="button" class="text-action inline-action" @click="isClientFormOpen = !isClientFormOpen">
                {{ isClientFormOpen ? 'Cancelar nuevo cliente' : '+ Crear cliente' }}
              </button>
            </label>
            <label class="field">
              <span>Fecha de la venta</span>
              <input v-model="operationDate" type="date" required />
            </label>
          </div>
          <p v-if="clientSavedMessage" class="modal-status" role="status">{{ clientSavedMessage }}</p>

          <section
            v-if="isClientFormOpen"
            class="new-client-form"
            aria-labelledby="new-client-title"
            @keydown.enter.prevent="saveClient"
          >
            <h3 id="new-client-title">Nuevo cliente</h3>
            <div class="form-grid">
              <label class="field">
                <span>Nombre</span>
                <input
                  v-model="clientName"
                  type="text"
                  maxlength="100"
                  autocomplete="name"
                  aria-required="true"
                  :aria-invalid="Boolean(clientFieldErrors.name)"
                  :aria-describedby="clientFieldErrors.name ? 'new-client-name-error' : undefined"
                  @input="clientFieldErrors.name = ''; clientFormError = ''"
                />
                <small v-if="clientFieldErrors.name" id="new-client-name-error" class="field-error" role="alert">
                  {{ clientFieldErrors.name }}
                </small>
              </label>
              <label class="field">
                <span>Contacto</span>
                <input
                  v-model="clientContact"
                  type="text"
                  maxlength="100"
                  autocomplete="tel"
                  aria-required="true"
                  :aria-invalid="Boolean(clientFieldErrors.contact)"
                  :aria-describedby="clientFieldErrors.contact ? 'new-client-contact-error' : undefined"
                  @input="clientFieldErrors.contact = ''; clientFormError = ''"
                />
                <small v-if="clientFieldErrors.contact" id="new-client-contact-error" class="field-error" role="alert">
                  {{ clientFieldErrors.contact }}
                </small>
              </label>
            </div>
            <p v-if="clientFormError && !clientFieldErrors.name && !clientFieldErrors.contact" class="modal-error" role="alert">
              {{ clientFormError }}
            </p>
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="isClientSaving || !clientName.trim() || !clientContact.trim()"
              @click="saveClient"
            >
              {{ isClientSaving ? 'Guardando cliente…' : 'Guardar cliente' }}
            </button>
          </section>

          <div class="form-grid">
            <fieldset class="field field--wide channel-field">
              <legend>Canal de venta</legend>
              <label><input v-model="channel" type="radio" value="Física" /> Física</label>
              <label><input v-model="channel" type="radio" value="En Línea" /> En Línea</label>
            </fieldset>
          </div>

          <section class="line-items" aria-labelledby="sale-products-title">
            <div class="section-heading">
              <div>
                <h3 id="sale-products-title">Productos</h3>
                <p>Los precios anteriores aparecen como sugerencia; complétalos si aún no hay historial.</p>
              </div>
              <button
                type="button"
                class="text-action"
                :disabled="productLines.length >= 200"
                @click="addProductLine"
              >+ Añadir producto</button>
            </div>
            <label class="field product-search">
              <span>Buscar productos</span>
              <input v-model="productSearch" type="search" autocomplete="off" placeholder="Nombre o categoría" />
            </label>

            <div v-for="(line, index) in productLines" :key="line.key" class="product-line">
              <label class="field product-line__product">
                <span>Producto {{ index + 1 }}</span>
                <select v-model="line.productId" required @change="updateLineProduct(line)">
                  <option value="" disabled>Selecciona un producto</option>
                  <option v-for="product in visibleProducts" :key="product.id" :value="product.id">
                    {{ product.name }} · {{ product.category }}
                  </option>
                </select>
              </label>
              <label class="field">
                <span>Cantidad</span>
                <input v-model.number="line.quantity" type="number" min="1" max="100000" step="1" required />
              </label>
              <label class="field">
                <span>Precio unitario</span>
                <input v-model.number="line.unitPrice" type="number" min="1" step="1" required />
                <small v-if="line.productId && getProduct(line)?.suggestedPrice == null">Sin precio anterior: ingrésalo.</small>
                <small v-else-if="getProduct(line)?.suggestedPrice != null">Sugerido: {{ formatCLP(getProduct(line).suggestedPrice) }}</small>
              </label>
              <label class="field">
                <span>Costo unitario</span>
                <input v-model.number="line.unitCost" type="number" min="1" step="1" required />
                <small v-if="line.productId && getProduct(line)?.suggestedCost == null">Sin costo anterior: ingrésalo.</small>
                <small v-else-if="getProduct(line)?.suggestedCost != null">Sugerido: {{ formatCLP(getProduct(line).suggestedCost) }}</small>
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
            <button v-if="!productLines.length" type="button" class="btn btn-secondary" @click="addProductLine">
              Añadir el primer producto
            </button>
          </section>

          <div class="form-grid">
            <fieldset class="field field--wide channel-field">
              <legend>Condición de pago</legend>
              <label><input v-model="isCredit" type="radio" :value="false" /> Al contado</label>
              <label><input v-model="isCredit" type="radio" :value="true" /> A crédito</label>
            </fieldset>
            <label v-if="isCredit" class="field">
              <span>Fecha esperada de pago</span>
              <input
                v-model="paymentDueDate"
                type="date"
                :min="operationDate"
                required
                aria-describedby="payment-date-help"
              />
              <small id="payment-date-help">Debe ser igual o posterior a la fecha de venta.</small>
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
          <div class="form-grid">
            <label class="field field--wide">
              <span>Buscar producto</span>
              <input v-model="productSearch" type="search" autocomplete="off" placeholder="Nombre o categoría" data-autofocus />
            </label>
            <label class="field field--wide">
              <span>Producto o insumo</span>
              <select v-model="expenseProductId" required>
                <option value="" disabled>Selecciona un producto</option>
                <option v-for="product in visibleProducts" :key="product.id" :value="product.id">
                  {{ product.name }} · {{ product.category }}
                </option>
              </select>
              <small v-if="!visibleProducts.length && !isOptionsLoading" class="modal-status">
                No hay productos para esta búsqueda.
              </small>
            </label>
            <label class="field">
              <span>Fecha (opcional)</span>
              <input v-model="operationDate" type="date" />
            </label>
            <label class="field">
              <span>Monto (CLP)</span>
              <input v-model.number="expenseAmount" type="number" min="1" step="1" required />
            </label>
          </div>

          <section class="sale-review" aria-label="Resumen del gasto en insumos">
            <div>
              <span>Producto</span>
              <strong>{{ selectedExpenseProduct?.name || 'Sin seleccionar' }}</strong>
            </div>
            <div class="sale-review__total">
              <span>Monto a registrar</span>
              <strong>{{ formatCLP(Number(expenseAmount) || 0) }}</strong>
            </div>
          </section>
        </template>

        <div v-if="submitError" class="modal-error" role="alert">
          <span>{{ submitError }}</span>
          <button type="button" class="text-action" :disabled="isSubmitting || !canSubmit" @click="submit">
            Reintentar
          </button>
        </div>

        <footer class="operation-modal__footer">
          <button type="button" class="btn btn-secondary" @click="close">Cancelar</button>
          <button type="submit" class="btn btn-primary" :disabled="!canSubmit || isSubmitting">
            {{ isSubmitting ? 'Guardando…' : isSale ? 'Registrar venta' : 'Registrar gasto' }}
          </button>
        </footer>
      </form>
    </section>
  </div>
</template>

<style scoped>
.operation-modal-backdrop { position: fixed; inset: 0; z-index: 1100; display: grid; place-items: center; padding: var(--layout-control-gap); background: rgba(15, 23, 42, .56); }
.operation-modal { width: min(47.5rem, 100%); min-width: var(--content-min-width); max-height: min(92vh, 56.25rem); overflow: auto; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-xl); box-shadow: var(--shadow-modal); }
.operation-modal__header { display: flex; min-width: var(--content-min-width); justify-content: space-between; gap: var(--layout-control-gap); padding: var(--layout-card-gap) var(--layout-section-gap); border-bottom: 1px solid var(--color-border); }
.operation-modal__header > div { min-width: var(--content-min-width); }
.operation-modal__eyebrow { color: var(--color-brand-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.operation-modal__header h2 { margin: 4px 0; color: var(--color-text); font-size: 1.35rem; }
.operation-modal__header p, .section-heading p { color: var(--color-text-secondary); font-size: .84rem; }
.icon-button { display: inline-grid; place-items: center; width: var(--control-min-height); height: var(--control-min-height); flex: 0 0 var(--control-min-height); border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-secondary); }
.icon-button:hover { background: var(--color-bg-subtle); }
.icon-button svg { width: 19px; height: 19px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.operation-mode-switch { display: flex; min-width: var(--content-min-width); flex-wrap: wrap; gap: var(--space-2); padding: var(--layout-control-gap) var(--layout-section-gap) 0; }
.operation-mode-switch button { min-height: 44px; padding: 8px 14px; border: 1px solid var(--color-border); border-radius: var(--radius-pill); color: var(--color-text-secondary); font-size: .84rem; font-weight: 700; }
.operation-mode-switch button.is-active { color: var(--color-brand-primary); background: var(--color-brand-primary-light); border-color: var(--color-brand-primary-border); }
.modal-error, .modal-status { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: var(--layout-control-gap); margin: var(--layout-control-gap) var(--layout-section-gap) 0; padding: var(--layout-control-gap); border-radius: var(--radius-md); font-size: .84rem; }
.modal-error { border: 1px solid #fecaca; background: #fef2f2; color: #991b1b; }
.modal-status { background: var(--color-bg-subtle); color: var(--color-text-secondary); }
.new-client-form { display: flex; min-width: 0; flex-direction: column; gap: var(--layout-control-gap); padding: var(--layout-control-gap); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-bg-subtle); }
.new-client-form h3 { font-size: .95rem; }
.field-error { color: #b91c1c !important; }
.field input[aria-invalid="true"] { border-color: #b91c1c; }
.inline-action { align-self: flex-start; }
.operation-form { display: flex; min-width: var(--content-min-width); flex-direction: column; gap: var(--layout-card-gap); padding: var(--layout-card-gap) var(--layout-section-gap); }
.form-grid { display: grid; min-width: var(--content-min-width); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--layout-control-gap); }
.field { display: flex; min-width: 0; flex-direction: column; gap: 7px; color: var(--color-text); font-size: .82rem; font-weight: 700; }
.field--wide { grid-column: 1 / -1; }
.field input:not([type="radio"]), .field select, .field textarea { width: 100%; max-width: 100%; min-width: var(--content-min-width); min-height: var(--control-min-height); padding: var(--space-2) var(--layout-control-gap); border: 1px solid var(--color-border-strong); border-radius: var(--radius-sm); background: var(--color-surface); color: var(--color-text); font: inherit; font-weight: 500; }
.field textarea { resize: vertical; }
.field small { color: var(--color-text-secondary); font-size: .75rem; font-weight: 500; }
.channel-field { display: flex; min-width: var(--content-min-width); flex-flow: row wrap; gap: var(--space-2) var(--layout-card-gap); border: 0; }
.channel-field legend { width: 100%; margin-bottom: 8px; font-size: .82rem; font-weight: 700; }
.channel-field label { display: inline-flex; min-height: var(--control-min-height); align-items: center; gap: var(--space-2); color: var(--color-text-secondary); font-size: .84rem; font-weight: 600; }
.channel-field input { width: 17px; height: 17px; accent-color: var(--color-brand-primary); }
.section-heading { display: flex; min-width: var(--content-min-width); flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--layout-control-gap); margin-bottom: var(--layout-control-gap); }
.section-heading > div { min-width: var(--content-min-width); }
.section-heading h3 { margin-bottom: 2px; font-size: .98rem; }
.product-search { margin-bottom: var(--layout-control-gap); }
.text-action { min-height: var(--control-min-height); padding: var(--space-2) var(--layout-control-gap); color: var(--color-brand-primary); font-size: .82rem; font-weight: 800; }
.product-line { display: grid; min-width: 0; grid-template-columns: minmax(0, 2fr) minmax(4rem, .7fr) minmax(5rem, 1fr) minmax(5rem, 1fr) minmax(5rem, auto) var(--control-min-height); gap: var(--layout-control-gap); align-items: end; padding: var(--layout-control-gap) 0; border-top: 1px solid var(--color-border-subtle); }
.product-line .field input, .product-line .field select { min-width: 0; }
.line-subtotal { display: flex; min-width: 0; min-height: var(--control-min-height); flex-direction: column; justify-content: center; gap: var(--space-1); color: var(--color-text-secondary); font-size: .72rem; }
.line-subtotal strong { color: var(--color-text); font-size: .85rem; }
.remove-line { color: var(--color-expense); }
.remove-line:disabled { cursor: not-allowed; opacity: .45; }
.sale-review { display: flex; min-width: var(--content-min-width); flex-wrap: wrap; justify-content: space-between; gap: var(--layout-control-gap); padding: var(--layout-control-gap); border: 1px solid var(--color-brand-primary-border); border-radius: var(--radius-md); background: var(--color-brand-primary-light); }
.sale-review > div { display: flex; min-width: var(--content-min-width); flex: 1 1 10rem; flex-direction: column; gap: var(--space-1); }
.sale-review span { color: var(--color-text-secondary); font-size: .76rem; }
.sale-review strong { color: var(--color-text); font-size: .9rem; }
.sale-review__total { text-align: right; }
.sale-review__total strong { color: var(--color-brand-primary); font-size: 1.15rem; }
.operation-modal__footer { display: flex; min-width: var(--content-min-width); flex-wrap: wrap; justify-content: flex-end; gap: var(--layout-control-gap); padding-top: var(--layout-control-gap); border-top: 1px solid var(--color-border); }
.operation-modal__footer .btn { min-width: 0; min-height: var(--control-min-height); }
.operation-modal__footer .btn:disabled { cursor: not-allowed; opacity: .55; }
@media (max-width: 900px) {
  .product-line { grid-template-columns: minmax(0, 2fr) minmax(4rem, .7fr) minmax(5rem, 1fr) minmax(5rem, 1fr); }
  .line-subtotal { grid-column: 1 / -2; }
  .remove-line { grid-column: -2 / -1; grid-row: 2; justify-self: end; }
}
@media (max-width: 640px) {
  .operation-modal-backdrop { padding: 0; align-items: end; }
  .operation-modal { max-height: 96dvh; border-radius: var(--radius-lg) var(--radius-lg) 0 0; }
  .operation-modal__header, .operation-form { padding-left: var(--layout-control-gap); padding-right: var(--layout-control-gap); }
  .operation-mode-switch { padding-left: var(--layout-control-gap); padding-right: var(--layout-control-gap); }
  .modal-error, .modal-status { margin-right: var(--layout-control-gap); margin-left: var(--layout-control-gap); }
  .form-grid { grid-template-columns: 1fr; }
  .field--wide { grid-column: auto; }
  .product-line { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--layout-control-gap); }
  .product-line__product { grid-column: 1 / -1; }
  .line-subtotal { grid-column: 1; }
  .remove-line { grid-column: 2; grid-row: auto; justify-self: end; }
  .sale-review { align-items: flex-start; }
  .operation-modal__footer { flex-direction: column-reverse; }
  .operation-modal__footer .btn { width: 100%; }
}
</style>
