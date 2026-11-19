import { getLocalDateString } from '@/utils/formatters'
import { ApiError, apiRequest } from './apiClient'
import {
  adaptCollectionAlerts,
  adaptInvoiceDetail,
  adaptReceivables,
  adaptReceivablesSummary
} from './apiAdapters'
import { USE_MOCKS } from './optionsService'

const PAGE_SIZE = 10
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

function queryString(params) {
  return new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
  ).toString()
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
    pendingOnlyCount: pending.length,
    overdueCount: overdue.length,
    totalCount: accounts.length,
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

export async function getReceivables({ filter = 'all', search = '', sortOrder = 'earliest', page = 1 } = {}) {
  if (USE_MOCKS) return getMockAccounts()

  const query = queryString({
    ...(filter !== 'all' ? { estado: filter } : {}),
    search: search.trim(),
    ordering: sortOrder === 'latest' ? '-fecha_vencimiento' : 'fecha_vencimiento',
    page,
    page_size: PAGE_SIZE
  })
  const payload = await apiRequest(`/finanzas/cuentas-por-cobrar/?${query}`, {
    authenticated: true,
    retryAfterRefresh: true
  })
  const pageData = adaptReceivables(payload)
  return {
    ...pageData,
    results: pageData.results.map((account) => ({
      ...account,
      displayStatus: account.status
    }))
  }
}

export async function getReceivablesSummary() {
  if (USE_MOCKS) return (await getMockAccounts()).summary

  const payload = await apiRequest('/finanzas/cuentas-por-cobrar/?page=1&page_size=1', {
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptReceivablesSummary(payload)
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

  const payload = await apiRequest(`/finanzas/alertas-cobro/?page_size=${PAGE_SIZE}`, {
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptCollectionAlerts(payload).results
}

export async function getCollectionAlertCount() {
  const payload = await apiRequest('/finanzas/alertas-cobro/?page_size=1', {
    authenticated: true,
    retryAfterRefresh: true
  })
  return adaptCollectionAlerts(payload).count
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
