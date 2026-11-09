<script setup>
import { computed } from 'vue'
import OperationFormModal from '@/components/operations/OperationFormModal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  initialType: { type: String, default: 'VENTA_PAGADA' },
  initialMode: { type: String, default: '' },
  initialData: { type: Object, default: null }
})

const emit = defineEmits(['close', 'success', 'save'])

const formMode = computed(() => {
  if (props.initialMode) return props.initialMode
  const type = props.initialType.toLocaleUpperCase('es-CL')
  if (type === 'VENTA_PENDIENTE') return 'venta-pendiente'
  if (type === 'COMPRA') return 'compra'
  if (type === 'GASTO') return 'otro-gasto'
  return 'venta'
})

const handleSave = (operation) => {
  emit('save', operation)
  emit('success', {
    tipo: props.initialType,
    concepto: operation.description,
    monto: operation.amount,
    contraparte: operation.customerOrSupplier,
    operation
  })
  emit('close')
}
</script>

<template>
  <OperationFormModal
    :is-open="isOpen"
    :initial-mode="formMode"
    :initial-data="initialData"
    @close="emit('close')"
    @save="handleSave"
  />
</template>
