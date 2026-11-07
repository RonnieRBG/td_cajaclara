/**
 * Formateador de moneda oficial para pesos chilenos (CLP) sin decimales.
 */
const clpFormatter = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  maximumFractionDigits: 0
})

export function formatCLP(amount) {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '$ 0'
  }
  return clpFormatter.format(amount)
}

/**
 * Formateador de fechas para Chile (DD/MM/AAAA)
 */
export function formatDate(dateString) {
  if (!dateString) return ''
  const [year, month, day] = dateString.split('-')
  if (!year || !month || !day) return dateString
  return `${day}/${month}/${year}`
}

/**
 * Formateador de fecha amigable (ej: 31 de Octubre)
 */
export function formatFriendlyDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString + 'T00:00:00')
  return date.toLocaleDateString('es-CL', {
    day: 'numeric',
    month: 'short'
  })
}

/**
 * Formateador de fecha y hora
 */
export function formatDateTime(dateTimeString) {
  if (!dateTimeString) return ''
  return dateTimeString
}

