import { ApiError } from './apiClient'

function invalidResponse(field) {
  throw new ApiError(`La respuesta de la API no contiene un valor válido en "${field}".`, {
    code: 'INVALID_API_RESPONSE'
  })
}

function requiredNumber(value, field) {
  if (value === null || value === undefined || value === '') invalidResponse(field)
  const number = Number(value)
  if (!Number.isFinite(number)) invalidResponse(field)
  return number
}

function requiredRecord(value, field) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) invalidResponse(field)
  return value
}

function requiredArray(value, field) {
  if (!Array.isArray(value)) invalidResponse(field)
  return value
}

function adaptCashFlow(value, field) {
  const cashFlow = requiredRecord(value, field)
  const inflows = requiredRecord(cashFlow.entradas, `${field}.entradas`)
  const outflows = requiredRecord(cashFlow.salidas, `${field}.salidas`)

  return {
    inflows: requiredNumber(inflows.total, `${field}.entradas.total`),
    outflows: requiredNumber(outflows.total, `${field}.salidas.total`),
    balance: requiredNumber(cashFlow.saldo, `${field}.saldo`)
  }
}

export function adaptFilterOptions(payload) {
  const types = requiredArray(payload?.tipos_compra, 'tipos_compra')
    .map((item) => {
      const option = requiredRecord(item, 'tipos_compra[]')
      if (typeof option.codigo !== 'string' || typeof option.nombre !== 'string') {
        invalidResponse('tipos_compra[]')
      }
      return { value: option.codigo, label: option.nombre }
    })
  const range = requiredRecord(payload?.rango_fechas_disponible, 'rango_fechas_disponible')

  if (typeof range.min !== 'string' || typeof range.max !== 'string') {
    invalidResponse('rango_fechas_disponible')
  }

  return { types, dateRange: { min: range.min, max: range.max } }
}

export function adaptMonthlySummary(payload) {
  const byStatus = requiredRecord(payload?.por_estado_pago, 'por_estado_pago')
  const paid = requiredRecord(byStatus.PAGADO, 'por_estado_pago.PAGADO')
  const pending = requiredRecord(byStatus.PENDIENTE, 'por_estado_pago.PENDIENTE')
  const byChannel = requiredRecord(payload?.por_tipo_compra, 'por_tipo_compra')
  const physical = requiredRecord(byChannel['Física'], 'por_tipo_compra.Física')
  const online = requiredRecord(byChannel['En Línea'], 'por_tipo_compra.En Línea')
  const flow = adaptCashFlow(payload?.flujo_caja, 'flujo_caja')

  return {
    totalInvoices: requiredNumber(payload.total_facturas, 'total_facturas'),
    totalTransactions: requiredNumber(payload.total_transacciones, 'total_transacciones'),
    totalUnits: requiredNumber(payload.total_unidades, 'total_unidades'),
    totalSales: requiredNumber(payload.total_ingresos, 'total_ingresos'),
    totalCosts: requiredNumber(payload.total_costos, 'total_costos'),
    grossProfit: requiredNumber(payload.utilidad_bruta, 'utilidad_bruta'),
    marginPercent: requiredNumber(payload.margen_porcentaje, 'margen_porcentaje'),
    filterChannel: payload.filtro_tipo_compra,
    cashFlow: flow,
    salesByStatus: {
      paid: {
        amount: requiredNumber(paid.ingresos, 'por_estado_pago.PAGADO.ingresos'),
        transactions: requiredNumber(paid.transacciones, 'por_estado_pago.PAGADO.transacciones')
      },
      pending: {
        amount: requiredNumber(pending.ingresos, 'por_estado_pago.PENDIENTE.ingresos'),
        transactions: requiredNumber(pending.transacciones, 'por_estado_pago.PENDIENTE.transacciones')
      }
    },
    salesByChannel: {
      physical: {
        amount: requiredNumber(physical.ingresos, 'por_tipo_compra.Física.ingresos'),
        invoices: requiredNumber(physical.facturas, 'por_tipo_compra.Física.facturas')
      },
      online: {
        amount: requiredNumber(online.ingresos, 'por_tipo_compra.En Línea.ingresos'),
        invoices: requiredNumber(online.facturas, 'por_tipo_compra.En Línea.facturas')
      }
    }
  }
}

export function adaptGroupedSummary(payload) {
  const periods = requiredArray(payload?.periodos, 'periodos').map((item) => {
    const period = requiredRecord(item, 'periodos[]')
    const flow = adaptCashFlow(period.flujo_caja, 'periodos[].flujo_caja')
    if (typeof period.periodo !== 'string') invalidResponse('periodos[].periodo')

    return {
      week: period.periodo,
      range: period.rango,
      sales: flow.inflows,
      expenses: flow.outflows
    }
  })

  return { periods }
}

export function adaptOperations(payload) {
  const results = requiredArray(payload?.results, 'results').map((item) => {
    const operation = requiredRecord(item, 'results[]')
    if (typeof operation.fecha !== 'string') invalidResponse('results[].fecha')

    return {
      type: operation.tipo,
      id: operation.id,
      date: operation.fecha,
      detail: operation.detalle,
      amount: requiredNumber(operation.monto, 'results[].monto'),
      channel: operation.tipo_compra,
      status: operation.estado_pago
    }
  })
  const summary = requiredRecord(payload?.resumen, 'resumen')
  const sales = requiredRecord(summary.ventas, 'resumen.ventas')
  const expenses = requiredRecord(summary.gastos, 'resumen.gastos')

  return {
    count: requiredNumber(payload.count, 'count'),
    results,
    summary: {
      salesCount: requiredNumber(sales.cantidad, 'resumen.ventas.cantidad'),
      expensesCount: requiredNumber(expenses.cantidad, 'resumen.gastos.cantidad')
    }
  }
}

export function adaptCollectionAlerts(payload) {
  const summary = requiredRecord(payload?.resumen, 'resumen')
  const results = requiredArray(payload?.results, 'results').map((item) => {
    const alert = requiredRecord(item, 'results[]')
    return {
      id: alert.id_cuenta,
      client: alert.cliente_nombre,
      invoice: alert.id_factura,
      amount: requiredNumber(alert.monto, 'results[].monto'),
      dueDate: alert.fecha_vencimiento,
      issueDate: alert.fecha_emision,
      dueLabel: alert.ventana_alerta,
      status: alert.estado,
      suggestedMessage: alert.mensaje_sugerido
    }
  })

  return {
    count: requiredNumber(summary.total_alertas, 'resumen.total_alertas'),
    amount: requiredNumber(summary.monto_total, 'resumen.monto_total'),
    results
  }
}

export function adaptTopProducts(payload) {
  return requiredArray(payload?.results, 'results').map((item) => {
    const product = requiredRecord(item, 'results[]')
    return {
      id: product.id_producto,
      name: product.producto,
      units: requiredNumber(product.total_vendido, 'results[].total_vendido'),
      sales: requiredNumber(product.total_ingresos, 'results[].total_ingresos'),
      stock: null
    }
  })
}

export function adaptDashboardData({ summary, grouped, operations, alerts, products }) {
  const noMovements = summary.totalInvoices === 0 &&
    summary.totalUnits === 0 &&
    summary.cashFlow.inflows === 0 &&
    summary.cashFlow.outflows === 0

  return {
    hasMovements: !noMovements,
    kpis: {
      balance: summary.cashFlow.balance,
      sales: summary.cashFlow.inflows,
      expenses: summary.cashFlow.outflows,
      priorityCollections: alerts.amount
    },
    operationsSummary: {
      sales: operations.summary.salesCount,
      expenses: summary.filterChannel === 'TODOS' ? operations.summary.expensesCount : null,
      units: summary.totalUnits,
      priorityCollections: alerts.count
    },
    weeklyFlow: grouped.periods.map((period) => ({
      semana: period.week,
      ventas: period.sales,
      gastos: period.expenses
    })),
    collections: alerts.results.map((alert) => ({
      id: alert.id,
      cliente: alert.client,
      detalle: alert.suggestedMessage,
      documento: alert.invoice,
      monto: alert.amount,
      vencimientoTexto: alert.dueLabel,
      estado: alert.status,
      fechaVencimiento: alert.dueDate,
      fechaEmision: alert.issueDate
    })),
    recentOperations: operations.results.map((operation) => ({
      id: operation.id,
      tipo: operation.type,
      concepto: operation.type === 'VENTA'
        ? operation.status === 'PENDIENTE' ? 'Venta pendiente' : 'Venta pagada'
        : 'Gasto de insumo',
      detalle: operation.type === 'VENTA' ? null : operation.detail,
      clienteProveedor: operation.type === 'VENTA' ? operation.detail : null,
      canal: operation.channel,
      fecha: operation.date,
      estado: operation.status === 'PAGADO' ? 'PAGADA' : operation.status,
      monto: operation.amount
    })),
    topProducts: products.map((product) => ({
      id: product.id,
      nombre: product.name,
      unidadesVendidas: product.units,
      totalVentas: product.sales,
      stockComprado: product.stock
    }))
  }
}

export function adaptMonthlySummaryData({
  summary,
  grouped,
  operations,
  largestSale,
  topProduct
}) {
  const noMovements = summary.totalInvoices === 0 &&
    summary.totalUnits === 0 &&
    summary.cashFlow.inflows === 0 &&
    summary.cashFlow.outflows === 0

  return {
    hasMovements: !noMovements,
    totals: {
      sales: summary.totalSales,
      expenses: summary.cashFlow.outflows,
      balance: summary.cashFlow.balance,
      transactions: summary.totalTransactions,
      expensesCount: summary.filterChannel === 'TODOS' ? operations.summary.expensesCount : null,
      expensesCountLabel: 'movimientos'
    },
    sales: {
      paid: summary.salesByStatus.paid,
      pending: summary.salesByStatus.pending,
      physical: summary.salesByChannel.physical,
      online: summary.salesByChannel.online
    },
    expenses: [{
      category: 'Gastos en insumos',
      amount: summary.cashFlow.outflows
    }],
    weeklyData: grouped.periods.map((period) => ({
      semana: period.week,
      rango: period.range,
      ventas: period.sales,
      gastos: period.expenses
    })),
    highlights: {
      topProduct: topProduct?.name ?? null,
      topProductUnits: topProduct?.units ?? null,
      largestSale: largestSale?.amount ?? null,
      unitsSold: summary.totalUnits
    },
    operationCount: operations.count,
    operations: operations.results.map((operation) => ({
      id: String(operation.id),
      date: operation.date,
      type: operation.type === 'VENTA' ? 'Venta' : 'Gasto de insumo',
      description: operation.detail,
      amount: operation.amount,
      status: operation.status
    }))
  }
}
