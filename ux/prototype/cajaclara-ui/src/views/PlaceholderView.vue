<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const viewInfo = computed(() => {
  if (route.path.includes('operaciones')) {
    return {
      title: 'Compras y ventas (Movimientos)',
      description: 'Listado completo, filtros por tipo, fecha y exportación de movimientos de caja.',
      icon: 'cash'
    }
  }
  if (route.path.includes('cobros')) {
    return {
      title: 'Cuentas por cobrar',
      description: 'Gestión detallada de clientes, ventas al fiado, estados de cobranza y registro de pagos.',
      icon: 'receipt'
    }
  }
  return {
    title: 'Resumen mensual',
    description: 'Reporte consolidado de flujo de caja, balance del periodo y métricas de desempeño del micronegocio.',
    icon: 'chart'
  }
})

const goBack = () => {
  router.push('/')
}
</script>

<template>
  <div class="card placeholder-card">
    <div class="placeholder-icon-wrap" aria-hidden="true">
      <svg v-if="viewInfo.icon === 'cash'" viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="1" x2="12" y2="23" />
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
      </svg>
      <svg v-else-if="viewInfo.icon === 'receipt'" viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z" />
        <line x1="8" y1="8" x2="16" y2="8" />
        <line x1="8" y1="12" x2="14" y2="12" />
      </svg>
      <svg v-else viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    </div>

    <h2 class="placeholder-title">{{ viewInfo.title }}</h2>
    <p class="placeholder-desc">{{ viewInfo.description }}</p>

    <div class="placeholder-badge">
      <span>Sprint actual: Pantalla de alta fidelidad focalizada en Dashboard principal</span>
    </div>

    <button type="button" class="btn btn-primary" @click="goBack">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="19" y1="12" x2="5" y2="12" />
        <polyline points="12 19 5 12 12 5" />
      </svg>
      <span>Volver al Dashboard</span>
    </button>
  </div>
</template>

<style scoped>
.placeholder-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-12) var(--space-6);
  min-height: 420px;
  gap: var(--space-4);
}

.placeholder-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-full);
  background-color: var(--color-primary-50);
  color: var(--color-primary-600);
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-text);
  margin: 0;
}

.placeholder-desc {
  font-size: 0.95rem;
  color: var(--color-text-secondary);
  max-width: 480px;
  margin: 0;
  line-height: 1.5;
}

.placeholder-badge {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-primary-800);
  background-color: var(--color-primary-100);
  border: 1px solid var(--color-primary-200);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
}
</style>
