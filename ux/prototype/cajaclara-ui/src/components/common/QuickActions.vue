<template>
  <section class="quick-actions-bar ui-card" aria-label="Acciones Rápidas de Caja">
    <div class="quick-actions-bar__header">
      <span class="ui-section-kicker">Caja Registradora</span>
      <h2 class="quick-actions-bar__title">Operaciones Frecuentes</h2>
    </div>

    <div class="quick-actions-bar__grid">
      <!-- 1. Registrar Venta -->
      <button 
        type="button" 
        class="quick-action-btn quick-action-btn--primary" 
        @click="$emit('open-modal', 'venta')"
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
      </button>

      <!-- 2. Registrar Compra -->
      <button 
        type="button" 
        class="quick-action-btn quick-action-btn--secondary" 
        @click="$emit('open-modal', 'compra')"
        title="Registrar compra de productos al por mayor"
      >
        <span class="quick-action-btn__icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <path d="M16 10a4 4 0 0 1-8 0" />
          </svg>
        </span>
        <div class="quick-action-btn__content">
          <strong class="quick-action-btn__label">Registrar compra</strong>
          <span class="quick-action-btn__sub">Cajas / Fardos</span>
        </div>
      </button>

      <!-- 3. Registrar Otro Gasto -->
      <button 
        type="button" 
        class="quick-action-btn quick-action-btn--secondary" 
        @click="$emit('open-modal', 'gasto')"
        title="Registrar otro gasto operativo como fletes o servicios"
      >
        <span class="quick-action-btn__icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
            <line x1="1" y1="10" x2="23" y2="10" />
          </svg>
        </span>
        <div class="quick-action-btn__content">
          <strong class="quick-action-btn__label">Registrar otro gasto</strong>
          <span class="quick-action-btn__sub">Flete, servicios, etc.</span>
        </div>
      </button>

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
defineEmits(['open-modal'])
</script>

<style scoped>
.quick-actions-bar {
  padding: var(--space-5) var(--space-6);
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
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

.quick-action-btn {
  display: flex;
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
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .quick-actions-bar__grid {
    grid-template-columns: 1fr;
  }
}
</style>
