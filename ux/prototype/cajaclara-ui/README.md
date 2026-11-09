# CajaClara UI

## Prototipo frontend de alta fidelidad

CajaClara UI es el prototipo Frontend de alta fidelidad de CajaClara, una aplicación de caja y gestión financiera sencilla para micronegocios. La interfaz permite consultar ventas, gastos, saldo y cuentas por cobrar mediante una experiencia clara, accesible y responsive.

| Atributo              | Detalle                                  |
| --------------------- | ---------------------------------------- |
| Estado                | 🚧 En construcción                       |
| Etapa                 | Semana 3                                 |
| Área                  | Frontend y Diseño UX                     |
| Rama                  | `ux`                                     |
| Tecnología principal  | Vue 3 + Vite                             |
| Prioridad visual      | Escritorio con adaptación responsive     |

> **Nota:** Este README describe exclusivamente el prototipo Vue 3. Para consultar la investigación, los user flows, los wireframes y el proceso completo de diseño, revisa el [README de Diseño UX](../../README.md).

---

## Tabla de contenidos

- [Estado actual](#estado-actual)
- [Características actuales](#características-actuales)
- [Capturas](#capturas)
- [Stack tecnológico](#stack-tecnológico)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Scripts disponibles](#scripts-disponibles)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Arquitectura de componentes](#arquitectura-de-componentes)
- [Rutas](#rutas)
- [Datos simulados](#datos-simulados)
- [Sistema visual](#sistema-visual)
- [Responsive](#responsive)
- [Accesibilidad](#accesibilidad)
- [Integración con Backend](#integración-con-backend)
- [Variables de entorno](#variables-de-entorno)
- [Pruebas y calidad](#pruebas-y-calidad)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Roadmap técnico](#roadmap-técnico)
- [Flujo de trabajo](#flujo-de-trabajo)
- [Contribución](#contribución)
- [Licencia](#licencia)

---

## Estado actual

> El proyecto se encuentra en desarrollo. El Dashboard, Compras y ventas y Cuentas por cobrar están implementados. Los módulos restantes continúan en construcción o se representan mediante componentes placeholder.

### Implementado

- Configuración base con Vue 3 y Vite.
- Dashboard de alta fidelidad con layout de dos columnas.
- Layout principal con sidebar, header y barra inferior.
- Navegación lateral permanente en escritorio y drawer en tablet/móvil.
- Barra de navegación inferior para móvil.
- Tarjetas KPI: saldo del periodo, ventas del mes, compras y gastos, dinero pendiente por cobrar.
- Acciones rápidas de caja (4 botones).
- Gráfico de barras de entradas y salidas semanales (CSS puro).
- Cobros prioritarios con estados semánticos (pendiente, vencida).
- Resumen de actividad operativa (ventas, gastos, unidades, cuentas pendientes).
- Operaciones recientes con detalle, tipo y badge de estado.
- Productos más vendidos con unidades y monto.
- Modal de nueva operación (venta pagada, venta al fiado, compra/gasto).
- Vista de Compras y ventas en `/operaciones`, con filtros, búsqueda, indicadores y detalle de operaciones.
- Vista de Cuentas por cobrar en `/cobros`, con filtros, búsqueda, orden por vencimiento, detalle y registro simulado de pago completo.
- Formularios simulados para ventas de varios productos, compras y otros gastos.
- Notificaciones toast con feedback visual.
- Datos simulados desacoplados por vista y escenario.
- Utilidades de formato de moneda (CLP) y fechas.
- Rutas preparadas para módulos futuros.
- Sistema visual compartido con design tokens en CSS custom properties.
- Adaptación responsive de escritorio a móvil.
- Skip link de accesibilidad para navegación por teclado.

### En desarrollo

- Resumen mensual.
- Login y autenticación.
- Configuración del negocio.
- Registro completo de ventas.
- Registro de gastos.
- Registro de pago parcial o total.
- Estados vacíos.
- Estados de error.
- Estados de carga.
- Confirmaciones de acciones destructivas.
- Integración con Backend.
- Pruebas automatizadas.
- Auditoría de accesibilidad.

### Fuera del alcance actual

- Inventario automático.
- Stock en tiempo real.
- Pagos parciales.
- Facturación electrónica.
- WhatsApp o correo reales.
- Reportes tributarios.
- Gestión avanzada de proveedores.
- Rentabilidad contable definitiva.

---

## Características actuales

- **Dashboard financiero** con indicadores de saldo, ventas, gastos y cuentas por cobrar.
- **Gráfico de entradas y salidas** semanal con barras comparativas.
- **Resumen de actividad** con métricas operativas agregadas.
- **Operaciones recientes** con tipo, concepto, monto y estado.
- **Cobros prioritarios** con alertas de vencimiento y acción de cobro.
- **Productos más vendidos** con unidades y total de ventas.
- **Acciones rápidas** para registrar ventas, compras y cobros.
- **Modal de nueva operación** con formulario interactivo y tipos configurables.
- **Compras y ventas** con filtro por periodo/tipo/estado, búsqueda, ordenamiento, detalle y registro local de pagos.
- **Cuentas por cobrar** con estados pendiente, vencida y pagada; indicadores, filtros, búsqueda, orden por vencimiento, detalle y pago completo simulado.
- **Registro simulado** de ventas de varios productos, compras de insumos y otros gastos.
- **Navegación responsive** con sidebar en escritorio, drawer en tablet y barra inferior en móvil.
- **Rutas preparadas** para los módulos de operaciones, cobros y resumen mensual.

> Todas las cifras visibles en el prototipo son simuladas y no representan datos reales ni respuestas actuales de la API.

---

## Capturas

> Pendiente: incorporar capturas del Dashboard en escritorio, tablet y móvil.

---

## Stack tecnológico

| Dependencia             | Versión   | Tipo          |
| ----------------------- | --------- | ------------- |
| Vue                     | ^3.5.12   | Producción    |
| Vue Router              | ^4.4.5    | Producción    |
| Vite                    | ^5.4.10   | Desarrollo    |
| @vitejs/plugin-vue      | ^5.1.4    | Desarrollo    |

- **Lenguaje:** JavaScript (ES Modules).
- **Estilo de componentes:** Single File Components (SFC) con `<script setup>` y Composition API.
- **CSS:** CSS nativo con scoped styles y custom properties (design tokens).
- **Tipografía:** [Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans) cargada desde Google Fonts.
- **Iconos:** SVG inline (sin biblioteca externa).
- **Gráficos:** CSS puro (sin biblioteca de gráficos).
- **Formato de moneda:** `Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 })`.

No se utilizan Pinia, TypeScript, Vitest, ESLint ni Prettier en esta etapa.

---

## Requisitos previos

- **Node.js** ≥ 18.x (Vite 5 requiere Node.js 18 o superior).
- **npm** (incluido con Node.js).
- **Git**.
- **Navegador moderno** (Chrome, Firefox, Safari o Edge en sus últimas versiones).

---

## Instalación

```bash
git clone https://github.com/RonnieRBG/td_cajaclara.git
cd td_cajaclara
git checkout ux
cd ux/prototype/cajaclara-ui
npm install
npm run dev
```

La aplicación se ejecuta en `http://localhost:5173` por defecto.

---

## Scripts disponibles

Los scripts están definidos en `package.json`:

| Script          | Comando             | Descripción                                              |
| --------------- | ------------------- | -------------------------------------------------------- |
| `dev`           | `npm run dev`       | Inicia el servidor de desarrollo de Vite en el puerto 5173. |
| `build`         | `npm run build`     | Genera los assets estáticos de producción en `dist/`.    |
| `preview`       | `npm run preview`   | Sirve localmente el contenido de `dist/` para revisión.  |

No existen scripts configurados para lint, formateo ni pruebas.

---

## Estructura del proyecto

```
ux/prototype/cajaclara-ui/
├── index.html                          # Punto de entrada HTML
├── package.json                        # Dependencias y scripts
├── vite.config.js                      # Configuración de Vite (alias @, puerto 5173)
├── dist/                               # Build de producción (generado)
└── src/
    ├── main.js                         # Punto de entrada de Vue (app, router, CSS global)
    ├── App.vue                         # Layout principal (sidebar, header, router-view, bottom nav)
    ├── assets/
    │   └── styles/
    │       └── main.css                # Design tokens, reset, utilidades globales y componentes base
    ├── components/
    │   ├── common/
    │   │   ├── AppHeader.vue           # Barra superior: nombre del negocio, periodo y perfil
    │   │   ├── AppSidebar.vue          # Menú lateral (permanente en desktop, drawer en móvil)
    │   │   ├── AppBottomNav.vue        # Barra de navegación inferior para móvil
    │   │   ├── BadgeStatus.vue         # Badges semánticos accesibles (Pagada, Pendiente, Vencida)
    │   │   ├── QuickActions.vue        # 4 botones de acción rápida de caja
    │   │   └── StatCard.vue            # Tarjeta de indicador financiero (KPI)
    │   ├── dashboard/
    │       ├── CashChart.vue           # Gráfico de barras semanal (ventas vs compras/gastos)
    │       ├── NewOperationModal.vue   # Modal para registrar nuevos movimientos
    │       ├── OperationsSummary.vue   # Métricas operativas de volumen
    │       ├── PriorityCollections.vue # Cobros que requieren atención
    │       ├── RecentOperations.vue    # Últimos movimientos de caja
    │       └── TopProducts.vue         # Productos de mayor rotación
    │   └── operations/
    │       ├── OperationDetailModal.vue # Detalle accesible de una operación
    │       └── OperationFormModal.vue   # Formularios de venta, compra y gasto
    ├── data/
    │   ├── dashboardMock.js             # Datos simulados del Dashboard
    │   └── operationsMock.js            # Operaciones, clientes, productos y categorías simulados
    ├── router/
    │   └── index.js                    # Configuración de Vue Router (rutas y redirects)
    ├── utils/
    │   └── formatters.js              # Formateadores de moneda CLP y fechas
    └── views/
        ├── DashboardView.vue           # Vista principal del Dashboard (implementada)
        ├── OperationsView.vue          # Vista de Compras y ventas (implementada)
        └── PlaceholderView.vue         # Vista temporal para módulos en desarrollo
```

---

## Arquitectura de componentes

```
App.vue (Layout)
├── AppSidebar          → Navegación lateral (desktop) / drawer (tablet/móvil)
├── AppHeader           → Barra superior con nombre, periodo y perfil
├── <router-view>       → Contenido dinámico por ruta
│   ├── DashboardView   → Vista implementada
│   │   ├── QuickActions
│   │   ├── StatCard × 4             (KPIs financieros)
│   │   ├── CashChart                (Gráfico semanal)
│   │   ├── RecentOperations
│   │   ├── PriorityCollections
│   │   │   └── BadgeStatus
│   │   ├── OperationsSummary
│   │   ├── TopProducts
│   │   └── NewOperationModal
│   ├── OperationsView  → Compras y ventas implementada
│   │   ├── StatCard × 4
│   │   ├── NewOperationModal → OperationFormModal compartido
│   │   └── OperationDetailModal
│   ├── ReceivablesView → Cuentas por cobrar
│   │   ├── StatCard × 4
│   │   ├── ReceivableDetailModal
│   │   └── PaymentModal
│   └── PlaceholderView → Resumen (en desarrollo)
└── AppBottomNav        → Barra inferior para móvil
```

### Componentes comunes (`components/common/`)

| Componente          | Función                                                          |
| ------------------- | ---------------------------------------------------------------- |
| `AppHeader`         | Nombre del negocio, periodo actual, iniciales del propietario, botón hamburguesa en móvil. |
| `AppSidebar`        | Menú de navegación lateral con enlaces a Dashboard, Operaciones, Cobros y Resumen. Permanente en escritorio ≥ 1024 px, drawer con overlay en tablet/móvil. |
| `AppBottomNav`      | Barra inferior fija con acceso directo a las cuatro secciones principales. Visible solo bajo 1024 px. |
| `BadgeStatus`       | Badge visual con color semántico según estado: `PAGADA`, `PENDIENTE` o `VENCIDA`. |
| `QuickActions`      | Accesos rápidos a nueva venta, venta pendiente, compra/gasto y cobros. Las operaciones navegan a sus formularios mediante `/operaciones?nueva=...`. |
| `StatCard`          | Tarjeta KPI con monto, subtítulo, tendencia, tooltip informativo y variantes de color (`balance`, `income`, `expense`, `pending`); también permite mostrar conteos sin formato monetario. |

### Componentes del Dashboard (`components/dashboard/`)

| Componente              | Función                                                      |
| ----------------------- | ------------------------------------------------------------ |
| `CashChart`             | Gráfico de barras semanal que compara ventas contra compras/gastos. Implementado con CSS puro, sin dependencias externas. |
| `NewOperationModal`     | Modal accesible para registrar movimientos. Soporta tipos: venta pagada, venta al fiado y compra/gasto. Puede recibir datos iniciales para prellenar el formulario. |
| `OperationsSummary`     | Resumen numérico del periodo: total de ventas, total de gastos, unidades vendidas y cuentas pendientes. |
| `PriorityCollections`   | Lista de cobros urgentes con alerta de vencimiento, estado y acción para registrar pago. |
| `RecentOperations`      | Tabla de los últimos movimientos de caja con tipo, concepto, cliente/proveedor, monto y estado. |
| `TopProducts`           | Ranking de productos con más unidades vendidas y su monto total de ventas. |

### Componentes de operaciones (`components/operations/`)

| Componente | Función |
| --- | --- |
| `OperationFormModal` | Formulario accesible para venta con múltiples productos, compra de insumos u otro gasto. |
| `OperationDetailModal` | Modal de solo lectura con datos, productos, monto, estado y vencimiento de la operación. |

### Componentes de cuentas por cobrar (`components/receivables/`)

| Componente | Función |
| --- | --- |
| `ReceivableDetailModal` | Detalle de cliente, contacto, factura, productos, fechas, monto y estado. |
| `PaymentModal` | Registro de pago completo con fecha, método y referencia opcional. |

---

## Rutas

Las rutas están definidas en `src/router/index.js` usando Vue Router 4 con `createWebHistory`:

| Ruta             | Nombre        | Componente         | Estado         |
| ---------------- | ------------- | ------------------ | -------------- |
| `/`              | Dashboard     | `DashboardView`    | ✅ Implementada |
| `/dashboard`     | —             | Redirect → `/`     | ✅ Redirect     |
| `/operaciones`   | Operaciones   | `OperationsView`   | ✅ Implementada |
| `/cobros`        | Cobros        | `ReceivablesView`  | ✅ Implementada |
| `/resumen`       | Resumen       | `PlaceholderView`  | 🚧 Placeholder  |
| `/:pathMatch(.*)*` | —           | Redirect → `/`     | ✅ Catch-all    |

El componente `PlaceholderView` se conserva para Resumen y los módulos que aún no están implementados.

---

## Datos simulados

Los datos simulados están separados por vista. `src/data/dashboardMock.js` alimenta el Dashboard, `src/data/operationsMock.js` contiene operaciones, clientes, productos y categorías para Compras y ventas, y `src/data/receivablesMock.js` contiene las cuentas por cobrar vinculadas a operaciones existentes cuando es posible.

| Exportación             | Descripción                                                   |
| ----------------------- | ------------------------------------------------------------- |
| `businessInfo`          | Nombre, propietario, tipo, RUT, dirección y teléfono del negocio. |
| `currentPeriod`         | Periodo activo (Octubre de 2026) con fechas de inicio y fin.  |
| `kpiMetrics`            | Totales de ventas, gastos, saldo y cuentas por cobrar con tendencias. |
| `operationsSummary`     | Conteos de ventas, gastos, unidades vendidas y cuentas pendientes. |
| `weeklyCashFlow`        | Flujo de caja semanal desglosado en ventas, gastos y balance.  |
| `priorityCollections`   | Cobros pendientes y vencidos con cliente, monto y detalle.     |
| `recentOperations`      | Últimos movimientos registrados con tipo, fecha y estado.      |
| `topDemandProducts`     | Productos más vendidos con unidades, ingresos y participación. |
| `mockData`              | Objeto consolidado que transforma las exportaciones anteriores al formato esperado por los componentes. |

`operationsMock.js` exporta `operations`, `clients`, `productCatalog`, `expenseCategories` y `suppliers`. Las altas y los pagos que se realizan desde `/operaciones` se conservan únicamente en el estado local de la vista durante la sesión; no modifican el mock ni se envían al Backend.

Los pagos realizados desde `/cobros` cancelan la cuenta completa y actualizan su estado e indicadores solo en el estado local de la vista. No hay persistencia, pagos parciales ni llamadas al Backend.

El escenario simulado representa el **Almacén La Esquina**, un almacén de barrio en Santiago, con datos del periodo Octubre de 2026.

> Los datos no provienen de una API ni de un backend. Cuando se implemente la integración, los imports de `dashboardMock.js` deben reemplazarse por llamadas al servicio real.

---

## Sistema visual

### Design tokens

El sistema visual se define en `src/assets/styles/main.css` mediante CSS custom properties (variables `:root`). Incluye:

- **Paleta de marca:** Teal oscuro (`#0f766e`) como color primario de confianza financiera.
- **Paleta semántica de finanzas:**
  - Verde esmeralda (`--color-income`) para ingresos y ventas.
  - Rosa-rojo (`--color-expense`) para gastos y salidas.
  - Ámbar (`--color-warning`) para cuentas próximas a vencer.
  - Rojo (`--color-danger`) para cuentas vencidas.
- **Superficies:** Fondo de app (`#f8fafc`), superficie blanca, sutil y hover.
- **Tipografía:** Plus Jakarta Sans con pesos 400–800.
- **Espaciado:** Sistema de 8 niveles (4 px a 48 px) con variables `--space-1` a `--space-12`.
- **Bordes:** Radios de 6 px a `9999px` (pill).
- **Sombras:** 5 niveles (`sm`, `card`, `md`, `lg`, `modal`).
- **Medidas de layout:** Sidebar 250 px, header 64 px, bottom nav 64 px, contenido máximo 1360 px.

### Estilos compartidos

El archivo global incluye:

- Reset y normalización (`box-sizing`, márgenes, tipografía).
- Clases base de cards (`.card`, `.ui-card`).
- Sistema de botones (`.btn`, `.btn-primary`, `.btn-secondary`, `.btn-success`, `.btn-sm`, `.btn-ui`).
- Encabezados de sección (`.ui-section-header`, `.ui-section-title`, `.ui-section-kicker`).
- Focus visible accesible con borde de 2 px en color primario.
- Scrollbar sutil personalizada.

Cada componente extiende los tokens globales con estilos `<style scoped>`.

---

## Responsive

El prototipo sigue una estrategia **desktop-first** con adaptación progresiva a tablet y móvil mediante media queries:

| Breakpoint        | Comportamiento                                                   |
| ----------------- | ---------------------------------------------------------------- |
| ≥ 1024 px         | Sidebar permanente, KPIs en 4 columnas, analytics en 2 columnas. |
| 640–1023 px       | Sidebar como drawer, KPIs en 2 columnas, analytics en 1 columna. Bottom nav visible. |
| < 640 px          | KPIs en 1 columna, padding reducido, toast de ancho completo. Bottom nav visible. |

Breakpoints principales del CSS:

- `1200px` — Ajuste de padding del contenido principal.
- `1023px` — Oculta sidebar permanente, muestra bottom nav, elimina margen izquierdo.
- `640px` — Layout de columna única, padding compacto.

---

## Accesibilidad

Medidas implementadas en esta etapa:

- **Skip link** en `App.vue` para saltar al contenido principal (`#main-content`).
- **`lang="es"`** en el documento HTML.
- **`aria-label`** en secciones del Dashboard (indicadores, acciones rápidas).
- **`aria-live="polite"`** y **`role="status"`** en las notificaciones toast.
- **`aria-hidden="true"`** en iconos decorativos.
- **Focus visible** con outline de 2 px y offset, aplicado globalmente a enlaces, botones e inputs.
- **Badges semánticos** con colores diferenciados para estados (pagada, pendiente, vencida).

### Pendiente

- Auditoría completa con herramientas (axe, Lighthouse).
- Pruebas con lectores de pantalla.
- Revisión de contraste en todas las variantes de color.
- Gestión de foco dentro del modal.
- Navegación completa por teclado en todos los componentes.

---

## Integración con Backend

El prototipo actualmente no se conecta a ningún servicio externo. Toda la información es estática y proviene de `dashboardMock.js`.

### Preparación para la integración

Cuando el backend esté disponible:

1. Reemplazar los imports de `dashboardMock.js` en `DashboardView.vue` y `App.vue` por llamadas a la API.
2. Introducir un cliente HTTP (por ejemplo, `fetch` nativo o Axios).
3. Considerar un store centralizado (por ejemplo, Pinia) para gestionar el estado compartido.
4. Implementar estados de carga, error y vacío en cada componente.
5. Configurar las variables de entorno para la URL base de la API.

---

## Variables de entorno

No existen archivos `.env` configurados en esta etapa.

Cuando se requiera la integración con el backend, se recomienda crear un archivo `.env` con las variables necesarias siguiendo la convención de Vite:

```
VITE_API_BASE_URL=http://localhost:8000/api
```

Las variables con prefijo `VITE_` son expuestas al código del cliente mediante `import.meta.env.VITE_API_BASE_URL`.

---

## Pruebas y calidad

No existen pruebas automatizadas, configuración de linting ni formateo en esta etapa.

### Recomendaciones para etapas futuras

- **Unit testing:** Vitest + Vue Test Utils para lógica de componentes y utilidades.
- **Linting:** ESLint con `eslint-plugin-vue` para mantener convenciones de código.
- **Formateo:** Prettier para estilo consistente.
- **Accesibilidad:** axe-core o `eslint-plugin-vuejs-accessibility`.
- **E2E:** Cypress o Playwright para flujos críticos del Dashboard.

---

## Limitaciones conocidas

- Todos los datos son simulados. No hay persistencia ni comunicación con backend.
- El gráfico de barras está construido con CSS puro; no tiene tooltips interactivos ni animaciones avanzadas.
- El modal de nueva operación no persiste datos; simula el registro y muestra un toast.
- La vista de Operaciones usa estado local temporal; al recargar, las altas y pagos vuelven a los datos mock iniciales.
- La vista de Cuentas por cobrar utiliza un mock propio; sus cambios se pierden al recargar y no se sincronizan con Compras y ventas ni con el Backend.
- Resumen mensual continúa siendo placeholder.
- La edición de operaciones es únicamente una simulación.
- No existe gestión de estado global (Pinia). Los datos fluyen vía props desde el mock.
- No hay manejo de errores HTTP, estados de carga ni estados vacíos.
- La tipografía depende de Google Fonts (conexión externa requerida).
- No se ha realizado auditoría formal de accesibilidad ni pruebas con lectores de pantalla.
- No hay mecanismo de autenticación ni protección de rutas.

---

## Roadmap técnico

1. **Fase actual** — Dashboard y Compras y ventas de alta fidelidad con datos simulados.
2. **Siguiente fase** — Implementar Cuentas por cobrar y Resumen mensual.
3. **Integración** — Conectar con la API del backend, introducir Pinia y manejo de estados.
4. **Formularios** — Persistencia y validaciones completas para ventas, gastos y cobros.
5. **Calidad** — Incorporar ESLint, Prettier, Vitest y pruebas E2E.
6. **Accesibilidad** — Auditoría completa, gestión de foco y pruebas con lectores de pantalla.
7. **Producción** — Login, protección de rutas, variables de entorno y despliegue.

---

## Flujo de trabajo

1. Crear una rama a partir de `ux`.
2. Desarrollar o corregir en `ux/prototype/cajaclara-ui/`.
3. Verificar que `npm run dev` funcione sin errores.
4. Verificar que `npm run build` genere `dist/` correctamente.
5. Hacer commit descriptivo siguiendo convenciones del equipo.
6. Abrir Pull Request hacia la rama `ux`.

---

## Contribución

1. Forkea el repositorio o trabaja en una rama desde `ux`.
2. Sigue la estructura de carpetas existente (`components/common/`, `components/dashboard/`).
3. Utiliza `<script setup>` y Composition API en todos los componentes nuevos.
4. Utiliza los design tokens definidos en `main.css` en lugar de valores hardcodeados.
5. Mantén los datos simulados en `src/data/` separados de la lógica de componentes.
6. Documenta los componentes nuevos en este README.

---

## Licencia

Consulta el archivo de licencia en la raíz del repositorio.
