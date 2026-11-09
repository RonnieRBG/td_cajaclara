<template>
  <section class="quick-actions-bar ui-card" aria-label="Acciones Rápidas de Caja">
    <div class="quick-actions-bar__header">
      <span class="ui-section-kicker">Caja Registradora</span>
      <h2 class="quick-actions-bar__title">Operaciones Frecuentes</h2>
    </div>

    <div class="quick-actions-bar__grid">
      <!-- 1. Registrar Venta -->
      <router-link
        to="/operaciones?nueva=venta"
        class="quick-action-btn quick-action-btn--primary"
        title="Registrar una nueva venta por unidad"
      >
        <span class="quick-action-btn__icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </span>
        <div class="quick-action-btn__content">
          <strong class="quick-action-btn__label">Registrar venta</strong>
          <span class="quick-action-btn__sub">Entrada de dinero</span>
        </div>
      </router-link>

      <!-- 2. Venta al fiado -->
      <router-link
        to="/operaciones?nueva=venta-pendiente"
        class="quick-action-btn quick-action-btn--secondary"
        title="Registrar venta al fiado (pendiente de pago)"
      >
        <span class="quick-action-btn__icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <line x1="19" y1="11" x2="19" y2="17" />
            <line x1="16" y1="14" x2="22" y2="14" />
          </svg>
        </span>
        <div class="quick-action-btn__content">
          <strong class="quick-action-btn__label">Venta al fiado</strong>
          <span class="quick-action-btn__sub">Pendiente de pago</span>
        </div>
      </router-link>

      <!-- 3. Registrar Compra / Gasto -->
      <router-link
        to="/operaciones?nueva=gasto"
        class="quick-action-btn quick-action-btn--secondary"
        title="Registrar compra de productos o gasto operativo"
      >
        <span class="quick-action-btn__icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
            <line x1="1" y1="10" x2="23" y2="10" />
          </svg>
        </span>
        <div class="quick-action-btn__content">
          <strong class="quick-action-btn__label">Registrar gasto</strong>
          <span class="quick-action-btn__sub">Compra o gasto operativo</span>
        </div>
      </router-link>

      <!-- 4. Revisar Cobros -->
      <router-link
        to="/cobros"
        class="quick-action-btn quick-action-btn--secondary"
        title="Ir a gestionar cobros pendientes a clientes"
      >
        <span class="quick-action-btn__icon quick-action-btn__icon--warning" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
        </span>
        <div class="quick-action-btn__content">
          <strong class="quick-action-btn__label">Revisar cobros</strong>
          <span class="quick-action-btn__sub">Dinero que te deben</span>
        </div>
      </router-link>
    </div>
  </section>
</template>

<script setup>
</script>

<style scoped>
.quick-actions-bar {
  min-width: var(--content-min-width);
  padding: var(--space-5) var(--layout-card-gap);
}

.quick-actions-bar__header {
  margin-bottom: var(--space-4);
}

.quick-actions-bar__title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text-main);
  letter-spacing: -0.01em;
}

.quick-actions-bar__grid {
  display: grid;
  min-width: var(--content-min-width);
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--layout-control-gap);
}

.quick-action-btn {
  display: flex;
  min-width: var(--content-min-width);
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg-subtle);
  text-align: left;
  transition: all 0.15s ease;
  cursor: pointer;
}

.quick-action-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
  border-color: #cbd5e1;
  background: #ffffff;
}

.quick-action-btn--primary {
  background: var(--color-brand-primary);
  border-color: var(--color-brand-primary);
  color: #ffffff;
}

.quick-action-btn--primary:hover {
  background: var(--color-brand-primary-hover);
  border-color: var(--color-brand-primary-hover);
}

.quick-action-btn--primary .quick-action-btn__sub {
  color: #ccfbf1;
}

.quick-action-btn__icon {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.05);
  color: var(--color-text-main);
  flex-shrink: 0;
}

.quick-action-btn--primary .quick-action-btn__icon {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.quick-action-btn__icon--warning {
  color: var(--color-warning);
  background: var(--color-warning-light);
}

.quick-action-btn__content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.quick-action-btn__label {
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-action-btn__sub {
  font-size: 11px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Responsive */
@media (max-width: 1024px) {
  .quick-actions-bar__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .quick-actions-bar__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
