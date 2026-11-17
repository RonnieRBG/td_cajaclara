import { currentPeriod } from '@/data/dashboardMock'
import { monthlySummaryData } from '@/data/monthlySummaryMock'
import { apiRequest } from './apiClient'
import { adaptFilterOptions } from './apiAdapters'

export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true'

function periodsBetween(min, max) {
  const [minYear, minMonth] = min.split('-').map(Number)
  const [maxYear, maxMonth] = max.split('-').map(Number)
  const periods = []

  for (let year = minYear; year <= maxYear; year += 1) {
    const firstMonth = year === minYear ? minMonth : 1
    const lastMonth = year === maxYear ? maxMonth : 12
    for (let month = firstMonth; month <= lastMonth; month += 1) {
      periods.push({
        year,
        month: String(month).padStart(2, '0'),
        value: `${year}-${String(month).padStart(2, '0')}`,
        label: new Date(year, month - 1, 1).toLocaleDateString('es-CL', { month: 'long' })
      })
    }
  }

  return periods
}

export function getPeriodRange(options, year, month) {
  const periodStart = `${year}-${month}-01`
  const lastDay = new Date(Number(year), Number(month), 0).getDate()
  const periodEnd = `${year}-${month}-${String(lastDay).padStart(2, '0')}`

  return {
    startDate: periodStart < options.dateRange.min ? options.dateRange.min : periodStart,
    endDate: periodEnd > options.dateRange.max ? options.dateRange.max : periodEnd
  }
}

export async function getFilterOptions() {
  if (USE_MOCKS) {
    const availablePeriods = Object.keys(monthlySummaryData).sort()
    const min = `${availablePeriods[0]}-01`
    const lastPeriod = availablePeriods[availablePeriods.length - 1]
    const [year, month] = lastPeriod.split('-').map(Number)
    const max = `${lastPeriod}-${String(new Date(year, month, 0).getDate()).padStart(2, '0')}`

    return {
      types: [
        { value: 'Física', label: 'Física' },
        { value: 'En Línea', label: 'En Línea' }
      ],
      dateRange: { min, max },
      periods: periodsBetween(min, max),
      initialPeriod: currentPeriod.id
    }
  }

  const response = await apiRequest('/finanzas/opciones-filtros/', {
    authenticated: true,
    retryAfterRefresh: true
  })
  const options = adaptFilterOptions(response)

  return {
    ...options,
    periods: periodsBetween(options.dateRange.min, options.dateRange.max),
    initialPeriod: options.dateRange.max.slice(0, 7)
  }
}
