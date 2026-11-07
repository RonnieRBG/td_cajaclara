# CajaClara UI — Prototipo de Alta Fidelidad (Vue 3 + Vite)

Prototipo de alta fidelidad para el **Dashboard Principal de CajaClara**, concebido como una caja registradora digital sencilla, moderna y cercana para pequeños micronegocios (almacenes de barrio, abarrotes).

## Stack Frontend

- **Vue 3** (Composition API, `<script setup>`, Single File Components)
- **Vite 5**
- **Vue Router 4**
- **CSS Nativo y Scoped** con variables de diseño (Design Tokens)
- Formato de moneda localizado en **Pesos Chilenos (CLP)** con `Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 })`

## Estructura del Proyecto

```
ux/prototype/cajaclara-ui/
├── public/
├── src/
│   ├── assets/
│   │   └── styles/
│   │       └── main.css            # Tokens de diseño, tipografía, variables y utilidades base
│   ├── components/
│   │   ├── common/
│   │   │   ├── AppHeader.vue       # Barra superior con nombre de negocio, periodo y perfil
│   │   │   ├── AppSidebar.vue      # Menú lateral para escritorio y drawer para tablet/móvil
│   │   │   ├── AppBottomNav.vue    # Barra de navegación inferior con acceso rápido móvil
│   │   │   ├── BadgeStatus.vue     # Badges semánticos accesibles (Pagada, Pendiente, Vencida)
│   │   │   ├── QuickActions.vue    # 4 botones de acción rápida de caja
│   │   │   └── StatCard.vue        # Tarjetas de indicadores financieros (KPIs)
│   │   └── dashboard/
│   │       ├── CashChart.vue           # Gráfico interactivo de barras (Ventas vs Compras/Gastos)
│   │       ├── OperationsSummary.vue   # Métricas operativas de volumen
│   │       ├── PriorityCollections.vue # Cobros que requieren atención
│   │       ├── RecentOperations.vue    # Últimos movimientos de caja registrados
│   │       ├── TopProducts.vue         # Productos de mayor rotación / demanda
│   │       └── NewOperationModal.vue   # Modal interactivo para registrar movimientos
│   ├── data/
│   │   └── dashboardMock.js        # Dataset demostrativo con escenario de Almacén La Esquina
│   ├── router/
│   │   └── index.js                # Configuración de rutas (Dashboard y vistas preparadas)
│   ├── utils/
│   │   └── formatters.js           # Formateadores de moneda chilena (CLP) y fechas
│   ├── App.vue                     # Layout principal responsivo
│   └── main.js                     # Punto de entrada de la aplicación Vue
├── index.html
├── package.json
└── vite.config.js
```

## Ejecución del Prototipo

### 1. Iniciar servidor de desarrollo
```bash
npm run dev
# o desde la raíz del repositorio:
npm --prefix ux/prototype/cajaclara-ui run dev
```

### 2. Generar build de producción
```bash
npm --prefix ux/prototype/cajaclara-ui run build
```
