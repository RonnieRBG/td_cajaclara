import { monthlySummaryData } from '@/data/monthlySummaryMock'
import {
  adaptGroupedSummary,
  adaptMonthlySummary,
  adaptMonthlySummaryData,
  adaptOperations,
  adaptTopProducts
} from './apiAdapters'
import { apiRequest } from './apiClient'
import { USE_MOCKS } from './optionsService'

function queryString(params) {
  return new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
  ).toString()
}

function adaptMonthlyMock(data) {
  if (!data) return null

  const sales = data.sales
  const expenses = data.expenses
  const weeklyData = data.weeklyData.map((item) => ({
    semana: item.semana,
    ventas: Number(item.ventas),
    gastos: Number(item.gastos)
  }))

  return {
    ...data,
    totals: {
      sales: Number(sales.paid.amount) + Number(sales.pending.amount),
      expenses: expenses.reduce((total, item) => total + Number(item.amount), 0),
      balance: Number(sales.paid.amount) + Number(sales.pending.amount) -
        expenses.reduce((total, item) => total + Number(item.amount), 0),
      transactions: Number(sales.paid.operations) + Number(sales.pending.operations),
      expensesCount: expenses.length,
      expensesCountLabel: 'categorías simuladas'
    },
    sales: {
      paid: { amount: Number(sales.paid.amount), transactions: Number(sales.paid.operations) },
      pending: { amount: Number(sales.pending.amount), transactions: Number(sales.pending.operations) },
      physical: { amount: Number(sales.physical.amount), invoices: Number(sales.physical.operations) },
      online: { amount: Number(sales.online.amount), invoices: Number(sales.online.operations) }
    },
    weeklyData,
    highlights: {
      ...data.highlights,
      topProduct: data.highlights.topProduct || null,
      pendingCustomer: data.highlights.pendingCustomer || null
    },
    operations: data.operations.map((operation) => ({
      ...operation,
      amount: Number(operation.amount)
    }))
  }
}

export async function getMonthlySummaryData({ startDate, endDate, channel = '', period }) {
  if (USE_MOCKS) return adaptMonthlyMock(monthlySummaryData[period])

  const dateParams = { fecha_inicio: startDate, fecha_fin: endDate, tipo_compra: channel }
  const groupedParams = { ...dateParams, agrupacion: 'semanas_mes' }
  const operationsParams = { ...dateParams, page_size: 5 }
  const largestSaleParams = { ...dateParams, tipo: 'venta', ordering: '-monto', page_size: 1 }
  const productsParams = { ...dateParams, ordering: '-total_vendido', page_size: 1 }
  const [summaryResponse, groupedResponse, operationsResponse, largestSaleResponse, productsResponse] =
    await Promise.all([
      apiRequest(`/finanzas/resumen-mensual/?${queryString(dateParams)}`, {
        authenticated: true,
        retryAfterRefresh: true
      }),
      apiRequest(`/finanzas/resumen-agrupado/?${queryString(groupedParams)}`, {
        authenticated: true,
        retryAfterRefresh: true
      }),
      apiRequest(`/finanzas/operaciones/?${queryString(operationsParams)}`, {
        authenticated: true,
        retryAfterRefresh: true
      }),
      apiRequest(`/finanzas/operaciones/?${queryString(largestSaleParams)}`, {
        authenticated: true,
        retryAfterRefresh: true
      }),
      apiRequest(`/finanzas/productos/?${queryString(productsParams)}`, {
        authenticated: true,
        retryAfterRefresh: true
      })
    ])

  const largestSale = adaptOperations(largestSaleResponse).results[0] ?? null
  const topProduct = adaptTopProducts(productsResponse)[0] ?? null

  return adaptMonthlySummaryData({
    summary: adaptMonthlySummary(summaryResponse),
    grouped: adaptGroupedSummary(groupedResponse),
    operations: adaptOperations(operationsResponse),
    largestSale,
    topProduct
  })
}
