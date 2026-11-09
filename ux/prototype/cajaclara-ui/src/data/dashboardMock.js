// Datos simulados exclusivamente para el prototipo de alta fidelidad. No representan resultados reales del dataset ni respuestas actuales de la API.

export const businessInfo = {
  name: 'Almacén La Esquina',
  owner: 'Max Ceballos',
  type: 'Abarrotes y Almacén de Barrio',
  rut: '76.432.198-K',
  address: 'Av. Providencia 1240, Santiago',
  phone: '+56 9 8765 4321'
}

export const currentPeriod = {
  id: '2026-10',
  label: 'Octubre de 2026',
  shortLabel: 'Oct 2026',
  startDate: '2026-10-01',
  endDate: '2026-10-31',
  isCurrent: true
}

export const kpiMetrics = {
  salesTotal: 1248500,
  salesSubtext: 'Dinero recibido por ventas en el mes',
  salesTrend: '+12.4% vs mes anterior',
  
  expensesTotal: 764300,
  expensesSubtext: 'Dinero destinado a productos y otros gastos',
  expensesTrend: '-3.1% vs mes anterior',
  
  balanceTotal: 484200,
  balanceSubtext: 'Diferencia entre entradas y salidas en caja',
  balanceTrend: 'Flujo neto positivo',
  
  receivablesTotal: 96500,
  receivablesSubtext: 'Dinero que todavía deben tus clientes',
  receivablesCount: 7
}

export const operationsSummary = {
  salesCount: 126,
  expensesCount: 41,
  unitsSold: 382,
  pendingAccountsCount: 7,
  pendingAccountsAmount: 96500
}

export const weeklyCashFlow = [
  {
    week: 'Sem 1',
    label: '01 - 07 Oct',
    sales: 310000,
    expenses: 195000,
    balance: 115000
  },
  {
    week: 'Sem 2',
    label: '08 - 14 Oct',
    sales: 285500,
    expenses: 182300,
    balance: 103200
  },
  {
    week: 'Sem 3',
    label: '15 - 21 Oct',
    sales: 368000,
    expenses: 224000,
    balance: 144000
  },
  {
    week: 'Sem 4',
    label: '22 - 31 Oct',
    sales: 285000,
    expenses: 163000,
    balance: 122000
  }
]

export const priorityCollections = [
  {
    id: 'col-001',
    customer: 'Claudia Rojas',
    invoice: 'INV-0024',
    amount: 12000,
    dueDate: '2026-11-10',
    issueDate: '2026-10-27',
    dueAlert: 'Vence en 3 días',
    status: 'Pendiente',
    productDetail: '4 botellas de aceite vegetal de 1 litro',
    phone: '+56 9 8765 4321'
  },
  {
    id: 'col-002',
    customer: 'Almacén San Pedro',
    invoice: 'INV-0019',
    amount: 18000,
    dueDate: '2026-10-25',
    issueDate: '2026-10-15',
    dueAlert: 'Vencimiento superado (hace 13 días)',
    status: 'Vencida',
    productDetail: 'Venta de productos surtidos',
    phone: '+56 9 7654 3210'
  },
  {
    id: 'col-003',
    customer: 'Minimarket Central',
    invoice: 'INV-0026',
    amount: 8500,
    dueDate: '2026-11-14',
    issueDate: '2026-10-30',
    dueAlert: 'Vence en 7 días',
    status: 'Pendiente',
    productDetail: 'Venta de aceite vegetal y abarrotes',
    phone: '+56 9 6543 2109'
  }
]

export const recentOperations = [
  {
    id: 'op-001',
    type: 'Venta',
    category: 'Venta pagada',
    description: '3 botellas de aceite vegetal de 1 litro',
    customer: 'Almacén San Pedro',
    channel: 'Canal físico',
    amount: 9000,
    date: '2026-10-31',
    time: '18:45',
    status: 'Pagada',
    docNumber: 'VTA-0126'
  },
  {
    id: 'op-002',
    type: 'Venta',
    category: 'Venta pendiente',
    description: '4 botellas de aceite vegetal de 1 litro',
    customer: 'Claudia Rojas',
    channel: 'Canal físico',
    amount: 12000,
    date: '2026-10-31',
    time: '16:20',
    status: 'Pendiente',
    docNumber: 'INV-0024'
  },
  {
    id: 'op-003',
    type: 'Compra',
    category: 'Gasto de insumo',
    description: 'Aceite vegetal (12 botellas / 1 caja)',
    supplier: 'Distribuidora Mayorista Central',
    channel: 'Canal físico',
    amount: 24000,
    date: '2026-10-30',
    time: '11:15',
    status: 'Pagada',
    docNumber: 'CMP-0041'
  },
  {
    id: 'op-004',
    type: 'Gasto',
    category: 'Otro gasto',
    description: 'Transporte para retirar mercadería',
    channel: 'Operativo',
    amount: 3500,
    date: '2026-10-29',
    time: '09:30',
    status: 'Pagada',
    docNumber: 'GST-0018'
  }
]

export const topDemandProducts = [
  {
    code: 'PROD-001',
    name: 'Aceite vegetal de 1 litro',
    category: 'Abarrotes',
    unitsSold: 94,
    revenue: 282000,
    sharePercent: 32
  },
  {
    code: 'PROD-002',
    name: 'Arroz grado 1 de 1 kilo',
    category: 'Abarrotes',
    unitsSold: 76,
    revenue: 114000,
    sharePercent: 26
  },
  {
    code: 'PROD-003',
    name: 'Azúcar blanca de 1 kilo',
    category: 'Abarrotes',
    unitsSold: 58,
    revenue: 69600,
    sharePercent: 20
  },
  {
    code: 'PROD-004',
    name: 'Fideos tallarines 400 gramos',
    category: 'Pastas',
    unitsSold: 42,
    revenue: 37800,
    sharePercent: 14
  }
]

export const mockData = {
  business: {
    name: businessInfo.name,
    owner: businessInfo.owner,
    initials: 'MC',
    period: currentPeriod.label
  },
  kpis: {
    saldoPeriodo: kpiMetrics.balanceTotal,
    ventasMes: kpiMetrics.salesTotal,
    comprasGastos: kpiMetrics.expensesTotal,
    pendienteCobrar: kpiMetrics.receivablesTotal
  },
  operationsSummary: {
    totalVentas: operationsSummary.salesCount,
    totalGastos: operationsSummary.expensesCount,
    unidadesVendidas: operationsSummary.unitsSold,
    cuentasPendientes: operationsSummary.pendingAccountsCount
  },
  weeklyFlow: weeklyCashFlow.map(w => ({
    semana: w.week,
    ventas: w.sales,
    gastos: w.expenses
  })),
  priorityCollections: priorityCollections.map(p => ({
    id: p.id,
    cliente: p.customer,
    detalle: p.productDetail,
    documento: p.invoice,
    monto: p.amount,
    vencimientoTexto: p.dueAlert,
    estado: p.status.toUpperCase() === 'VENCIDA' ? 'VENCIDA' : 'PENDIENTE'
  })),
  recentOperations: recentOperations.map(o => ({
    id: o.id,
    tipo: o.type.toUpperCase(),
    concepto: o.category,
    detalle: o.description,
    clienteProveedor: o.customer || o.supplier || 'Gasto operacional',
    canal: o.channel,
    fecha: `${o.date} ${o.time}`,
    estado: o.status.toUpperCase(),
    monto: o.amount
  })),
  topProducts: topDemandProducts.map(p => ({
    id: p.code,
    nombre: p.name,
    unidadesVendidas: p.unitsSold,
    totalVentas: p.revenue,
    stockComprado: p.code === 'PROD-001' ? 12 : null
  }))
}

