import { mockData, currentPeriod } from '@/data/dashboardMock'
import {
  adaptCollectionAlerts,
  adaptDashboardData,
  adaptGroupedSummary,
  adaptMonthlySummary,
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

function adaptDashboardMock(period) {
  if (period !== currentPeriod.id) return null

  return {
    hasMovements: true,
    kpis: {
      balance: mockData.kpis.saldoPeriodo,
      sales: mockData.kpis.ventasMes,
      expenses: mockData.kpis.comprasGastos,
      priorityCollections: mockData.kpis.pendienteCobrar
    },
    operationsSummary: {
      sales: mockData.operationsSummary.totalVentas,
      expenses: mockData.operationsSummary.totalGastos,
      units: mockData.operationsSummary.unidadesVendidas,
      priorityCollections: mockData.operationsSummary.cuentasPendientes
    },
    weeklyFlow: mockData.weeklyFlow,
    collections: mockData.priorityCollections,
    recentOperations: mockData.recentOperations,
    topProducts: mockData.topProducts
  }
}

export async function getDashboardData({ startDate, endDate, channel = '', period }) {
  if (USE_MOCKS) return adaptDashboardMock(period)

  const dateParams = { fecha_inicio: startDate, fecha_fin: endDate, tipo_compra: channel }
  const groupedParams = { ...dateParams, agrupacion: 'semanas_mes' }
  const operationsParams = { ...dateParams, page_size: 5 }
  const productsParams = queryString({
    ...dateParams,
    ordering: '-total_vendido',
    con_ventas: true,
    page_size: 4
  })
  const [summaryResponse, groupedResponse, operationsResponse, alertsResponse, productsResponse] =
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
      apiRequest('/finanzas/alertas-cobro/?page_size=3', {
        authenticated: true,
        retryAfterRefresh: true
      }),
      apiRequest(`/finanzas/productos/?${productsParams}`, {
        authenticated: true,
        retryAfterRefresh: true
      })
    ])

  return adaptDashboardData({
    summary: adaptMonthlySummary(summaryResponse),
    grouped: adaptGroupedSummary(groupedResponse),
    operations: adaptOperations(operationsResponse),
    alerts: adaptCollectionAlerts(alertsResponse),
    products: adaptTopProducts(productsResponse)
  })
}
