import { ApiError, apiRequest } from './apiClient'
import { USE_MOCKS } from './optionsService'

const FALLBACK_FILENAME = 'reporte_ventas.xlsx'

function queryString(params) {
  return new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
  ).toString()
}

function getFilename(contentDisposition) {
  const encodedFilename = contentDisposition?.match(/filename\*\s*=\s*(?:UTF-8'')?([^;]+)/i)?.[1]
  if (encodedFilename) {
    const value = encodedFilename.trim().replace(/^"|"$/g, '')
    try {
      return decodeURIComponent(value) || FALLBACK_FILENAME
    } catch {
      return value || FALLBACK_FILENAME
    }
  }

  const filename = contentDisposition?.match(/filename\s*=\s*(?:"([^"]*)"|([^;]*))/i)
  return (filename?.[1] ?? filename?.[2])?.trim() || FALLBACK_FILENAME
}

export async function exportMonthlySummary({ startDate, endDate, channel = '' }) {
  if (USE_MOCKS) {
    throw new ApiError('Exportación disponible con datos reales.', { code: 'MOCK_EXPORT_UNAVAILABLE' })
  }

  const query = queryString({
    fecha_inicio: startDate,
    fecha_fin: endDate,
    tipo_compra: channel
  })
  const response = await apiRequest(`/finanzas/exportar-excel/?${query}`, {
    authenticated: true,
    retryAfterRefresh: true,
    responseType: 'blob'
  })
  const url = URL.createObjectURL(response.blob)
  let link
  try {
    link = document.createElement('a')
    link.href = url
    link.download = getFilename(response.headers.get('Content-Disposition'))
    link.hidden = true
    document.body.append(link)
    link.click()
  } finally {
    link?.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
  }
}
