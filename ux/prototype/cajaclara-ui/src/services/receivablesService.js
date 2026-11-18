import { getLocalDateString } from '@/utils/formatters'
import { ApiError, apiRequest } from './apiClient'
import { adaptCollectionAlerts, adaptInvoiceDetail, adaptReceivables } from './apiAdapters'
import { USE_MOCKS } from './optionsService'

const PAGE_SIZE = 100
let mockAccounts = null

async function loadMockAccounts() {
  if (!mockAccounts) {
    const { receivables } = await import('@/data/receivablesMock')
    mockAccounts = receivables.map((account) => ({
      ...account,
      products: account.products.map((product) => ({ ...product }))
    }))
  }
}

function requestOptions(page) {
  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
  return { authenticated: true, retryAfterRefresh: true, query: query.toString() }
}

function getMockStatus(account) {
  if (account.status === 'PAGADA') return 'PAGADA'
  return account.dueDate < getLocalDateString() ? 'VENCIDA' : 'PENDIENTE'
}

function mockSummary(accounts) {
  const overdue = accounts.filter((account) => getMockStatus(account) === 'VENCIDA')
  const pending = accounts.filter((account) => getMockStatus(account) === 'PENDIENTE')
  const paid = accounts.filter((account) => getMockStatus(account) === 'PAGADA')
  return {
    pendingAmount: [...pending, ...overdue].reduce((total, account) => total + Number(account.amount), 0),
    overdueAmount: overdue.reduce((total, account) => total + Number(account.amount), 0),
    pendingCount: pending.length + overdue.length,
    paidCount: paid.length
  }
}

async function getMockAccounts() {
  await loadMockAccounts()
  const results = mockAccounts.map((account) => ({
    ...account,
    displayStatus: getMockStatus(account),
    products: account.products.map((product) => ({ ...product }))
  }))
  return { count: results.length, results, summary: mockSummary(mockAccounts) }
}

async function getAllPages(path, adaptPage) {
  let page = 1
  let expectedCount = null
  let pageData = null
  const results = []

  while (page === 1 || pageData.next) {
    const { query, ...options } = requestOptions(page)
    const payload = await apiRequest(`${path}?${query}`, options)
    pageData = adaptPage(payload)
    expectedCount ??= pageData.count
    results.push(...pageData.results)

    if (pageData.next && pageData.results.length === 0) {
      throw new ApiError('La API devolvió una página vacía antes de completar el listado.', {
        code: 'INVALID_API_RESPONSE'
      })
    }
    page += 1
  }

  if (results.length !== expectedCount) {
    throw new ApiError('La API indicó un total de registros distinto al listado paginado.', {
      code: 'INVALID_API_RESPONSE'
    })
  }

  return { ...pageData, count: expectedCount, results }
}

export async function getReceivables() {
  if (USE_MOCKS) return getMockAccounts()

  const pages = await getAllPages('/finanzas/cuentas-por-cobrar/', adaptReceivables)
  return {
    count: pages.count,
    results: pages.results.map((account) => ({
      ...account,
      displayStatus: account.status
    })),
    summary: pages.summary
  }
}

export async function getReceivableDetail(account) {
  if (USE_MOCKS) {
    await loadMockAccounts()
    const found = mockAccounts.find((item) => String(item.id) === String(account.id))
    if (!found) {
      throw new ApiError('No se encontró el detalle de esta cuenta.', { code: 'NOT_FOUND' })
    }
    return {
      ...account,
      ...found,
      displayStatus: getMockStatus(found),
      products: found.products.map((product) => ({ ...product }))
    }
  }

  const payload = await apiRequest(`/finanzas/facturas/${encodeURIComponent(account.invoiceId)}/`, {
    authenticated: true,
    retryAfterRefresh: true
  })
  const invoice = adaptInvoiceDetail(payload)
  return {
    ...account,
    description: invoice.description,
    products: invoice.products
  }
}

export async function getCollectionAlerts() {
  if (USE_MOCKS) return []

  const pages = await getAllPages('/finanzas/alertas-cobro/', adaptCollectionAlerts)
  return pages.results
}

export async function payReceivable(id, paymentDate) {
  if (USE_MOCKS) {
    await loadMockAccounts()
    const account = mockAccounts.find((item) => String(item.id) === String(id))
    if (!account) throw new ApiError('No se encontró la cuenta por cobrar.', { code: 'NOT_FOUND' })
    if (getMockStatus(account) === 'PAGADA') {
      throw new ApiError('La cuenta ya está pagada.', { status: 400 })
    }
    account.status = 'PAGADA'
    account.paymentDate = paymentDate || getLocalDateString()
    return
  }

  await apiRequest(`/finanzas/cuentas-por-cobrar/${encodeURIComponent(id)}/pagar/`, {
    method: 'POST',
    ...(paymentDate ? { body: { fecha_pago: paymentDate } } : {}),
    authenticated: true,
    retryAfterRefresh: true
  })
}

export async function revertReceivablePayment(id) {
  if (USE_MOCKS) {
    await loadMockAccounts()
    const account = mockAccounts.find((item) => String(item.id) === String(id))
    if (!account) throw new ApiError('No se encontró la cuenta por cobrar.', { code: 'NOT_FOUND' })
    if (getMockStatus(account) !== 'PAGADA') {
      throw new ApiError('Solo se puede revertir el pago de una cuenta pagada.', { status: 400 })
    }
    account.status = 'PENDIENTE'
    account.paymentDate = null
    return
  }

  await apiRequest(`/finanzas/cuentas-por-cobrar/${encodeURIComponent(id)}/revertir-pago/`, {
    method: 'POST',
    authenticated: true,
    retryAfterRefresh: true
  })
}
