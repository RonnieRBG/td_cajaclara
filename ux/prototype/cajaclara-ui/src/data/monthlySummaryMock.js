// Datos simulados exclusivamente para el prototipo. No representan resultados reales ni respuestas del Backend.

export const monthlySummaryData = {
  '2026-10': {
    hasMovements: true,
    sales: {
      paid: { amount: 1152000, operations: 112 },
      pending: { amount: 96500, operations: 14 },
      physical: { amount: 998500, operations: 104 },
      online: { amount: 250000, operations: 22 }
    },
    expenses: [
      { category: 'Compras de insumos', amount: 602500 },
      { category: 'Transporte', amount: 62700 },
      { category: 'Servicios', amount: 54100 },
      { category: 'Otros gastos', amount: 45000 }
    ],
    weeklyData: [
      { semana: 'Sem 1', ventas: 310000, gastos: 195000 },
      { semana: 'Sem 2', ventas: 285500, gastos: 182300 },
      { semana: 'Sem 3', ventas: 368000, gastos: 224000 },
      { semana: 'Sem 4', ventas: 285000, gastos: 163000 }
    ],
    highlights: {
      topProduct: 'Aceite vegetal de 1 litro',
      topProductUnits: 94,
      pendingCustomer: 'Almacén San Pedro',
      pendingAmount: 18000,
      largestSale: 48000,
      unitsSold: 382
    },
    operationCount: 167,
    operations: [
      {
        id: 'summary-op-001',
        date: '2026-10-31',
        type: 'Venta',
        description: '3 botellas de aceite vegetal de 1 litro',
        amount: 9000,
        status: 'Pagada'
      },
      {
        id: 'summary-op-002',
        date: '2026-10-31',
        type: 'Venta',
        description: '4 botellas de aceite vegetal de 1 litro',
        amount: 12000,
        status: 'Pendiente'
      },
      {
        id: 'summary-op-003',
        date: '2026-10-30',
        type: 'Compra',
        description: 'Aceite vegetal (12 botellas / 1 caja)',
        amount: 24000,
        status: 'Pagada'
      },
      {
        id: 'summary-op-004',
        date: '2026-10-29',
        type: 'Gasto',
        description: 'Transporte para retirar mercadería',
        amount: 3500,
        status: 'Pagada'
      },
      {
        id: 'summary-op-005',
        date: '2026-10-28',
        type: 'Venta',
        description: 'Pedido en línea de productos surtidos',
        amount: 48000,
        status: 'Pagada'
      },
      {
        id: 'summary-op-006',
        date: '2026-10-26',
        type: 'Gasto',
        description: 'Pago de servicios del local',
        amount: 15000,
        status: 'Pagada'
      }
    ]
  },
  '2026-11': {
    hasMovements: false,
    sales: {
      paid: { amount: 0, operations: 0 },
      pending: { amount: 0, operations: 0 },
      physical: { amount: 0, operations: 0 },
      online: { amount: 0, operations: 0 }
    },
    expenses: [],
    weeklyData: [],
    highlights: {
      topProduct: '',
      topProductUnits: 0,
      pendingCustomer: '',
      pendingAmount: 0,
      largestSale: 0,
      unitsSold: 0
    },
    operationCount: 0,
    operations: []
  }
}
