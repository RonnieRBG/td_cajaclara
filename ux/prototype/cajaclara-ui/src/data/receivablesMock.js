// Datos simulados exclusivamente para el prototipo. No representan respuestas del Backend.
import { clients, operations } from '@/data/operationsMock'

const findClient = (name) => clients.find(client => client.name === name)
const findOperation = (invoiceId) => operations.find(operation => operation.invoiceId === invoiceId) || null

const createReceivable = ({
  id,
  invoiceId,
  clientName,
  issuedDate,
  dueDate,
  amount,
  status,
  description,
  products
}) => {
  const operation = findOperation(invoiceId)
  const client = findClient(clientName)

  return {
    id,
    invoiceId,
    clientName,
    contact: client?.phone || 'No informado',
    issuedDate,
    dueDate,
    amount,
    status,
    description: operation?.description || description,
    products: operation?.products.map(product => ({ ...product })) || products,
    operationId: operation?.id || null
  }
}

export const receivables = [
  createReceivable({
    id: 'rcv-001',
    invoiceId: 'INV-0024',
    clientName: 'Claudia Rojas',
    issuedDate: '2026-10-31',
    dueDate: '2026-11-10',
    amount: 12000,
    status: 'PENDIENTE',
    description: 'Venta de aceite vegetal',
    products: []
  }),
  createReceivable({
    id: 'rcv-002',
    invoiceId: 'INV-0019',
    clientName: 'Almacén San Pedro',
    issuedDate: '2026-10-20',
    dueDate: '2026-11-06',
    amount: 18000,
    status: 'PENDIENTE',
    description: 'Venta de aceite vegetal',
    products: [
      { name: 'Aceite vegetal de 1 litro', quantity: 6, unitPrice: 3000, subtotal: 18000 }
    ]
  }),
  createReceivable({
    id: 'rcv-003',
    invoiceId: 'INV-0026',
    clientName: 'Minimarket Central',
    issuedDate: '2026-11-02',
    dueDate: '2026-11-14',
    amount: 8500,
    status: 'PENDIENTE',
    description: 'Venta de abarrotes',
    products: [
      { name: 'Productos de abarrotes', quantity: 1, unitPrice: 8500, subtotal: 8500 }
    ]
  }),
  createReceivable({
    id: 'rcv-004',
    invoiceId: 'VTA-0125',
    clientName: 'Minimarket Central',
    issuedDate: '2026-10-29',
    dueDate: '2026-11-05',
    amount: 30000,
    status: 'PAGADA',
    description: 'Venta surtida de abarrotes',
    products: []
  })
]
