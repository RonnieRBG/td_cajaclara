import { operations, clients, productCatalog } from '@/data/operationsMock'
import { ApiError, apiRequest } from './apiClient'
import {
  adaptClientOptions,
  adaptCreatedClient,
  adaptCreatedExpense,
  adaptInvoiceDetail,
  adaptOperations,
  adaptProductOptions
} from './apiAdapters'
import { USE_MOCKS } from './optionsService'
import { getLocalDateString } from '@/utils/formatters'

const mockOperations = operations.map((operation) => ({
  ...operation,
  products: operation.products.map((product) => ({ ...product }))
}))
const mockClients = clients.map((client) => ({ ...client }))
const mockProducts = productCatalog.map((product) => ({ ...product }))

function queryString(params) {
  return new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
  ).toString()
}

function isPending(operation) {
  return operation.type === 'Venta' && ['Pendiente', 'Vencida'].includes(operation.paymentStatus)
}

function mockStatus(operation) {
  if (operation.paymentStatus === 'Vencida') return 'Vencida'
  if (
    isPending(operation) &&
    operation.paymentDueDate &&
    operation.paymentDueDate < getLocalDateString()
  ) return 'Vencida'
  return operation.paymentStatus
}

function mockOperationView(operation) {
  const isSale = operation.type === 'Venta'
  return {
    ...operation,
    type: isSale ? 'Venta' : 'Gasto',
    customerOrSupplier: operation.customerOrSupplier || '',
    channel: isSale ? operation.channel : '—',
    paymentStatus: isSale ? operation.paymentStatus : 'Registrada',
    displayStatus: isSale ? mockStatus(operation) : 'Registrada',
    products: operation.products.map((product) => ({ ...product }))
  }
}

function mockSummary(filtered) {
  const sales = filtered.filter((operation) => operation.type === 'Venta')
  const expenses = filtered.filter((operation) => operation.type !== 'Venta')
  const pendingSales = sales.filter((operation) => ['Pendiente', 'Vencida'].includes(mockStatus(operation)))

  return {
    salesAmount: sales.reduce((total, operation) => total + Number(operation.amount), 0),
    expensesAmount: expenses.reduce((total, operation) => total + Number(operation.amount), 0),
    totalCount: filtered.length,
    pendingSalesAmount: pendingSales.reduce((total, operation) => total + Number(operation.amount), 0)
  }
}

function mockMatches(operation, filters) {
  const isSale = operation.type === 'Venta'
  if (filters.type === 'venta' && !isSale) return false
  if (filters.type === 'gasto' && isSale) return false
  if (filters.status === 'pendiente' && !isPending(operation)) return false
  if (filters.status === 'pagado' && (isPending(operation) || !isSale)) return false
  if (filters.channel && (!isSale || operation.channel !== filters.channel)) return false
  if (filters.month && !operation.date.startsWith(filters.month)) return false
  const query = filters.search?.trim().toLocaleLowerCase('es-CL')
  if (!query) return true

  const searchableText = [
    operation.invoiceId,
    operation.description,
    operation.customerOrSupplier,
    operation.type,
    ...operation.products.map((product) => product.name)
  ].join(' ').toLocaleLowerCase('es-CL')
  return searchableText.includes(query)
}

function sortMockOperations(items, ordering) {
  return [...items].sort((a, b) => {
    if (ordering === 'monto') return a.amount - b.amount
    if (ordering === '-monto') return b.amount - a.amount
    const dateComparison = `${a.date} ${a.time || ''}`.localeCompare(`${b.date} ${b.time || ''}`)
    return ordering === 'fecha' ? dateComparison : -dateComparison
  })
}

function getMockOperations(filters) {
  const filtered = sortMockOperations(
    mockOperations.filter((operation) => mockMatches(operation, filters)),
    filters.ordering
  )
  const pageSize = Number(filters.pageSize) || 10
  const page = Math.max(1, Number(filters.page) || 1)
  const start = (page - 1) * pageSize

  return {
    count: filtered.length,
    page,
    pageSize,
    hasNext: start + pageSize < filtered.length,
    hasPrevious: page > 1,
    summary: mockSummary(filtered),
    results: filtered.slice(start, start + pageSize).map(mockOperationView)
  }
}

function toOperationView(operation) {
  return {
    id: operation.id,
    invoiceId: operation.id,
    date: operation.date,
    time: '',
    type: operation.type === 'VENTA' ? 'Venta' : 'Gasto',
    customerOrSupplier: operation.detail,
    description: operation.detail,
    products: [],
    channel: operation.channel || '—',
    amount: operation.amount,
    paymentStatus: operation.type === 'GASTO'
      ? 'Registrada'
      : operation.status === 'PENDIENTE' ? 'Pendiente' : 'Pagada',
    paymentDueDate: operation.paymentDueDate,
    isCredit: operation.isCredit,
    clientId: operation.clientId,
    productId: operation.productId,
    itemsCount: operation.itemsCount
  }
}

export function getDefaultOperationMonth() {
  if (!USE_MOCKS) return getLocalDateString().slice(0, 7)
  return mockOperations
    .map((operation) => operation.date.slice(0, 7))
    .sort()
    .at(-1) || getLocalDateString().slice(0, 7)
}

export async function getOperations(filters) {
  if (USE_MOCKS) return getMockOperations(filters)

  const query = queryString({
    mes: filters.month,
    tipo: filters.type === 'all' ? undefined : filters.type,
    estado: filters.status || undefined,
    tipo_compra: filters.channel || undefined,
    search: filters.search?.trim() || undefined,
    ordering: filters.ordering,
    page: filters.page,
    page_size: filters.pageSize
  })
  const payload = await apiRequest(`/finanzas/operaciones/?${query}`, {
    authenticated: true,
    retryAfterRefresh: true
  })
  const adapted = adaptOperations(payload)

  return {
    count: adapted.count,
    page: Number(filters.page) || 1,
    pageSize: Number(filters.pageSize) || 10,
    hasNext: Boolean(adapted.next),
    hasPrevious: Boolean(adapted.previous),
    summary: {
      salesAmount: adapted.summary.salesAmount,
      expensesAmount: adapted.summary.expensesAmount,
      totalCount: adapted.summary.salesCount + adapted.summary.expensesCount,
      pendingSalesAmount: adapted.summary.pendingSalesAmount
    },
    results: adapted.results.map(toOperationView)
  }
}

export async function getClientOptions(search = '') {
  if (USE_MOCKS) {
    const query = search.trim().toLocaleLowerCase('es-CL')
    return mockClients
      .filter((client) => !query || `${client.name} ${client.phone} ${client.id}`
        .toLocaleLowerCase('es-CL').includes(query))
      .slice(0, 100)
  }

  const query = queryString({ search: search.trim(), limit: 100 })
  const payload = await apiRequest(`/finanzas/opciones/clientes/?${query}`, {
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptClientOptions(payload)
}

export async function getProductOptions(search = '') {
  if (USE_MOCKS) {
    const query = search.trim().toLocaleLowerCase('es-CL')
    return mockProducts
      .filter((product) => !query || `${product.name} ${product.category} ${product.id}`
        .toLocaleLowerCase('es-CL').includes(query))
      .slice(0, 100)
      .map((product) => ({
        id: product.id,
        name: product.name,
        category: product.category,
        suggestedPrice: product.unitPrice,
        suggestedCost: product.unitCost
      }))
  }

  const query = queryString({ search: search.trim(), limit: 100 })
  const payload = await apiRequest(`/finanzas/opciones/productos/?${query}`, {
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptProductOptions(payload)
}

export async function getOperationDetail(operation) {
  if (operation.type !== 'Venta') return operation
  if (USE_MOCKS) {
    const found = mockOperations.find((item) => item.id === operation.id)
    if (!found) throw new ApiError('No se encontró el detalle de esta venta.', { code: 'NOT_FOUND' })
    return mockOperationView(found)
  }

  const payload = await apiRequest(`/finanzas/facturas/${encodeURIComponent(operation.id)}/`, {
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptInvoiceDetail(payload)
}

export async function createClient({ name, contact }) {
  if (USE_MOCKS) {
    const normalizedContact = contact.trim()
    if (mockClients.some((client) => client.phone === normalizedContact)) {
      throw new ApiError('Este contacto ya está registrado.', {
        status: 400,
        validationErrors: { contacto: 'Este contacto ya está registrado.' }
      })
    }

    const client = {
      id: `cli-local-${Date.now()}`,
      name: name.trim(),
      phone: normalizedContact
    }
    mockClients.unshift(client)
    return { id: client.id, name: client.name, contact: client.phone }
  }

  const payload = await apiRequest('/finanzas/clientes/', {
    method: 'POST',
    body: { nombre: name.trim(), contacto: contact.trim() },
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptCreatedClient(payload)
}

export async function createSale(payload) {
  if (USE_MOCKS) {
    const client = mockClients.find((item) => item.id === payload.id_cliente)
    const details = payload.items.map((item) => {
      const product = mockProducts.find((entry) => entry.id === item.id_producto)
      return {
        id: item.id_producto,
        name: product?.name || 'Producto',
        quantity: item.cantidad,
        unitPrice: item.precio_venta,
        unitCost: item.costo_venta,
        subtotal: item.cantidad * item.precio_venta
      }
    })
    const id = `VTA-${String(mockOperations.length + 1).padStart(4, '0')}`
    const sale = {
      id,
      invoiceId: id,
      date: payload.fecha,
      type: 'Venta',
      customerOrSupplier: client?.name || '',
      description: details.map((product) => product.name).join(', '),
      products: details,
      channel: payload.tipo_compra,
      amount: details.reduce((total, product) => total + product.subtotal, 0),
      paymentStatus: payload.por_cobrar ? 'Pendiente' : 'Pagada',
      paymentDueDate: payload.por_cobrar ? payload.fecha_vencimiento : null
    }
    mockOperations.unshift(sale)
    return sale
  }

  const response = await apiRequest('/finanzas/facturas/', {
    method: 'POST',
    body: payload,
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptInvoiceDetail(response)
}

export async function createExpense(payload) {
  if (USE_MOCKS) {
    const product = mockProducts.find((item) => item.id === payload.id_producto)
    const expense = {
      id: `GST-${String(mockOperations.length + 1).padStart(4, '0')}`,
      invoiceId: `GST-${String(mockOperations.length + 1).padStart(4, '0')}`,
      date: payload.fecha || getLocalDateString(),
      type: 'Gasto',
      customerOrSupplier: product?.name || '',
      description: product?.name || 'Gasto en insumos',
      products: [{
        name: product?.name || 'Producto',
        quantity: null,
        unitPrice: null,
        subtotal: payload.monto
      }],
      channel: '—',
      amount: payload.monto,
      paymentStatus: 'Registrada',
      paymentDueDate: null
    }
    mockOperations.unshift(expense)
    return expense
  }

  const response = await apiRequest('/finanzas/gastos/', {
    method: 'POST',
    body: payload,
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptCreatedExpense(response)
}
