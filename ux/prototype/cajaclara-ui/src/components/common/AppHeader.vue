<template>
  <header class="app-header">
    <div class="app-header__left">
      <!-- Botón menú móvil (visible solo < 1024px) -->
      <button 
        type="button" 
        class="app-header__mobile-toggle"
        @click="$emit('toggle-sidebar')"
        aria-label="Abrir menú de navegación"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      <!-- Logo de CajaClara -->
      <router-link to="/dashboard" class="app-header__brand" title="CajaClara — Inicio">
        <span class="app-header__logo-mark" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="3" />
            <path d="M7 15h0M12 15h0M17 15h0M7 11h10" />
          </svg>
        </span>
        <div class="app-header__brand-info">
          <span class="app-header__brand-title">CajaClara</span>
          <span class="app-header__brand-tag">Caja Digital</span>
        </div>
      </router-link>

      <span class="app-header__divider" aria-hidden="true" />

      <!-- Nombre del Negocio -->
      <div class="app-header__business">
        <span class="app-header__business-kicker">Negocio Activo</span>
        <strong class="app-header__business-name">{{ businessName }}</strong>
      </div>
    </div>

    <div class="app-header__right">
      <!-- Selector de Periodo -->
      <div class="app-header__period">
        <span class="app-header__period-icon" aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
        </span>
        <span class="app-header__period-label">{{ activePeriod }}</span>
        <span class="app-header__chevron" aria-hidden="true">▼</span>
      </div>

      <!-- Usuario y Avatar -->
      <div class="app-header__user">
        <div class="app-header__avatar" aria-hidden="true">
          {{ activeInitials }}
        </div>
        <div class="app-header__user-meta">
          <strong class="app-header__user-name">{{ activeUser }}</strong>
          <span class="app-header__user-role">Emprendedor</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  businessName: {
    type: String,
    default: 'Almacén La Esquina'
  },
  periodLabel: {
    type: String,
    default: 'Octubre de 2026'
  },
  period: {
    type: String,
    default: ''
  },
  userName: {
    type: String,
    default: 'Max Ceballos'
  },
  ownerName: {
    type: String,
    default: ''
  },
  ownerInitials: {
    type: String,
    default: 'MC'
  }
})

defineEmits(['toggle-sidebar'])

const activePeriod = computed(() => props.period || props.periodLabel || 'Octubre de 2026')
const activeUser = computed(() => props.ownerName || props.userName || 'Max Ceballos')
const activeInitials = computed(() => props.ownerInitials || 'MC')
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  background-color: var(--color-bg-surface);
  border-bottom: 1px solid var(--color-border);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  position: sticky;
  top: 0;
  z-index: 30;
}

.app-header__left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.app-header__mobile-toggle {
  display: none;
  padding: 8px;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
}

.app-header__mobile-toggle:hover {
  background: var(--color-bg-subtle);
  color: var(--color-text-main);
}

.app-header__brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-header__logo-mark {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--color-brand-primary);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(15, 118, 110, 0.2);
}

.app-header__brand-info {
  display: flex;
  flex-direction: column;
}

.app-header__brand-title {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-text-main);
  line-height: 1.1;
}

.app-header__brand-tag {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-brand-primary);
  letter-spacing: 0.05em;
}

.app-header__divider {
  width: 1px;
  height: 28px;
  background-color: var(--color-border);
  display: inline-block;
}

.app-header__business {
  display: flex;
  flex-direction: column;
}

.app-header__business-kicker {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
  color: var(--color-text-muted);
}

.app-header__business-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-main);
}

.app-header__right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.app-header__period {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-main);
  cursor: pointer;
  transition: all 0.15s ease;
}

.app-header__period:hover {
  background: #ffffff;
  border-color: #cbd5e1;
}

.app-header__period-icon {
  color: var(--color-brand-primary);
  display: flex;
  align-items: center;
}

.app-header__chevron {
  font-size: 9px;
  color: var(--color-text-muted);
}

.app-header__user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-header__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.app-header__user-meta {
  display: flex;
  flex-direction: column;
  text-align: right;
}

.app-header__user-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-main);
  line-height: 1.2;
}

.app-header__user-role {
  font-size: 11px;
  color: var(--color-text-muted);
}

/* Responsive */
@media (max-width: 1024px) {
  .app-header__mobile-toggle {
    display: inline-flex;
  }
}

@media (max-width: 768px) {
  .app-header {
    padding: 0 16px;
  }
  .app-header__divider,
  .app-header__business,
  .app-header__user-meta {
    display: none;
  }
}
</style>
