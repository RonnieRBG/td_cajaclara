# CajaClara UI — Prototipo Vue

Documentación técnica del prototipo frontend de alta fidelidad. Para la investigación UX, el alcance del MVP y el proceso de diseño, consulta el [README de Diseño UX](../../README.md).

## Estado técnico

### Implementado

- Vistas navegables de Dashboard, Compras y ventas, Cuentas por cobrar y Resumen mensual.
- Formularios, filtros, búsqueda, detalle y confirmaciones simuladas según el módulo.
- Layout responsive y design tokens compartidos.
- Datos mock y estado local para interacciones del prototipo.

### En desarrollo

El trabajo continúa en la iteración del prototipo y en la definición de la integración futura. La guía de integración recoge acuerdos pendientes; el cliente Vue sigue aislado de la API.

### Pendiente

- Conectar las vistas con contratos de Backend acordados.
- Persistir y sincronizar operaciones entre módulos.
- Incorporar estados de carga y error para solicitudes reales.
- Añadir pruebas automatizadas y completar la validación de accesibilidad.

### Fuera del alcance actual

Pagos parciales, autenticación productiva, facturación electrónica, inventario automático y notificaciones reales por WhatsApp o correo.

> Los datos no persisten ni se envían al Backend. Los cambios locales se pierden al recargar y no se sincronizan entre módulos. El deploy también utiliza datos simulados.

## Stack y versiones

Aplicación JavaScript con Vue Single File Components (`<script setup>`), Composition API, Vue Router y CSS nativo. No utiliza librería externa de gráficos ni store global.

| Dependencia | Rango en `package.json` | Versión instalada actualmente |
| --- | --- | --- |
| `vue` | `^3.5.12` | `3.5.45` |
| `vue-router` | `^4.4.5` | `4.6.4` |
| `vite` | `^5.4.10` | `5.4.21` |
| `@vitejs/plugin-vue` | `^5.1.4` | `5.2.4` |

Las versiones instaladas corresponden al entorno verificado con `npm ls --depth=0`; `package-lock.json` registra la resolución del proyecto.

## Requisitos previos

- Node.js 18 o superior, compatible con Vite 5. `package.json` no declara un campo `engines`.
- npm.
- Navegador moderno.

## Instalación y ejecución

Desde la raíz del repositorio:

```bash
cd ux/prototype/cajaclara-ui
npm install
npm run dev
```

Vite sirve la aplicación en `http://localhost:5173`.

## Scripts disponibles

Son los scripts presentes en `package.json`:

| Comando | Uso |
| --- | --- |
| `npm run dev` | Inicia el servidor de desarrollo. |
| `npm run build` | Genera el build de producción en `dist/`. |
| `npm run preview` | Sirve localmente el build generado. |

No hay scripts configurados para tests, lint o formateo.

## Estructura del proyecto

```text
cajaclara-ui/
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
├── dist/                         # Generado por npm run build
└── src/
    ├── App.vue
    ├── main.js
    ├── assets/styles/main.css
    ├── components/
    │   ├── common/
    │   ├── dashboard/
    │   ├── operations/
    │   └── receivables/
    ├── data/
    ├── router/index.js
    ├── utils/formatters.js
    └── views/
```

`vite.config.js` configura el plugin de Vue, el alias `@` hacia `src/` y el puerto 5173. `dist/` es un directorio generado por el build.

## Vistas y componentes existentes

### Vistas (`src/views/`)

| Archivo | Responsabilidad |
| --- | --- |
| `DashboardView.vue` | Indicadores, acciones rápidas, flujo semanal, cobros prioritarios, movimientos recientes y productos destacados. |
| `OperationsView.vue` | Compras y ventas, filtros, búsqueda, detalle y formularios simulados. |
| `ReceivablesView.vue` | Cuentas por cobrar, estados, filtros, búsqueda, detalle y registro de pago completo simulado. |
| `MonthlySummaryView.vue` | Indicadores del periodo, gráfico semanal, desglose de gastos, ventas y operaciones principales. |
| `PlaceholderView.vue` | Componente de placeholder existente; no corresponde a una ruta activa del router. |

### Componentes

- `common/`: `AppHeader`, `AppSidebar`, `AppBottomNav`, `BadgeStatus`, `QuickActions` y `StatCard`.
- `dashboard/`: `CashChart`, `NewOperationModal`, `OperationsSummary`, `PriorityCollections`, `RecentOperations` y `TopProducts`.
- `operations/`: `OperationFormModal` y `OperationDetailModal`.
- `receivables/`: `PaymentModal` y `ReceivableDetailModal`.

## Rutas

Definidas en `src/router/index.js` con `createWebHistory`:

| Ruta | Vista | Estado |
| --- | --- | --- |
| `/` | Dashboard | Implementada |
| `/operaciones` | Compras y ventas | Implementada |
| `/cobros` | Cuentas por cobrar | Implementada |
| `/resumen` | Resumen mensual | Implementada |
| `/dashboard` | Redirección a `/` | Activa |
| Ruta desconocida | Redirección a `/` | Activa |

No hay rutas de login o configuración ni protección de rutas.

## Datos mock y comportamiento local

| Archivo | Contenido usado por el prototipo |
| --- | --- |
| `src/data/dashboardMock.js` | Negocio y periodo de ejemplo, KPI, flujo semanal, cobros prioritarios, operaciones recientes y productos destacados. |
| `src/data/operationsMock.js` | Operaciones, clientes, catálogo de productos, proveedores y categorías de gastos. |
| `src/data/receivablesMock.js` | Cuentas por cobrar y datos de detalle asociados. |
| `src/data/monthlySummaryMock.js` | Datos del resumen por periodo, incluidos indicadores, desglose y actividad. |

Las vistas de operaciones y cobros copian sus mocks a estado local para simular altas y pagos. No escriben en almacenamiento del navegador, no persisten entre recargas y no actualizan de forma compartida los otros módulos. Los pagos disponibles son completos; no hay pagos parciales.

## Design tokens y responsive

`src/assets/styles/main.css` define variables CSS compartidas para colores de marca y estados, superficies, tipografía, radios, sombras, espacios (`--space-*`) y layout (`--layout-*`). El gráfico añade tokens como `--chart-min-height`, `--chart-bar-width`, `--chart-series-gap`, `--chart-group-gap` y `--chart-axis-width`. Los componentes complementan estos valores con estilos scoped.

El responsive está implementado mediante media queries distribuidas entre el layout, las vistas y los componentes:

- El Dashboard usa dos columnas a partir de 1280 px y se apila por debajo.
- El sidebar se convierte en drawer hasta 1023 px.
- La navegación inferior se muestra hasta 767 px.
- Operaciones, cobros, resumen y modales ajustan sus grillas y controles en breakpoints propios.
- En pantallas estrechas, el desplazamiento horizontal de contenido se limita a componentes que lo requieren, como el gráfico.

## Accesibilidad

Hay medidas puntuales implementadas: skip link al contenido principal, landmarks y etiquetas ARIA en áreas relevantes, estados de foco visible, anuncios `aria-live` para feedback, controles de teclado en diálogos y soporte de movimiento reducido en el gráfico.

Esto **no representa cumplimiento completo de accesibilidad**. No se ha documentado una auditoría formal, validación integral con lectores de pantalla ni verificación de todos los criterios WCAG.

## Variables de entorno

No hay archivos `.env*`, referencias a `VITE_*` ni lectura de `import.meta.env` en el prototipo actual. No se necesita una URL de API para ejecutar los mocks. Cuando se acuerde la integración, deberá configurarse la URL del Backend mediante una variable de entorno de Vite, sin fijarla en el código.

## Deploy en Vercel

[Ver prototipo desplegado en Vercel](https://tdcajaclara-cajaclara-eml0tsuhf-jltamayocabello-droids-projects.vercel.app/)

El deploy es una demostración con datos simulados; no persiste cambios ni se conecta al Backend.

## Integración futura con Backend

El proyecto Vue todavía no realiza solicitudes HTTP. El repositorio incluye un Backend Django separado; su endpoint actual `GET /api/finanzas/resumen-mensual/` entrega totales del periodo actual, pero no cubre todos los filtros, operaciones y desgloses que esperan las vistas.

Antes de conectar el prototipo se deben acordar contratos de periodo, operaciones, cobros, estados y errores. La [guía de integración UX/Frontend con Backend](../../INTEGRACION-BACKEND.md) detalla las limitaciones y dependencias conocidas.

Pasos técnicos previstos:

1. Acordar contratos y formatos con Backend y Análisis de Datos.
2. Configurar la URL de API por entorno e introducir un cliente HTTP.
3. Sustituir mocks gradualmente y adaptar respuestas a los modelos de vista.
4. Persistir y sincronizar cambios, con estados de carga, error y vacío.
5. Validar build, navegación, formularios y persistencia de los flujos conectados.

## Pruebas y calidad

No hay suite de pruebas automatizadas, comandos de lint ni formateo en `package.json`. El build disponible es:

```bash
npm run build
```

El build se ejecutó correctamente al actualizar esta documentación.

## Limitaciones

- Sin persistencia, autenticación ni conexión desde Vue al Backend.
- Los mocks de cada módulo son independientes y no se sincronizan.
- Los estados de carga y error HTTP aún no aplican porque no hay solicitudes.
- No hay pagos parciales.
- No se ha completado una auditoría de accesibilidad.
- `PlaceholderView.vue` existe, pero no está asociado a una ruta activa.

## Roadmap técnico

1. Definir y validar contratos de API.
2. Conectar primero el resumen y luego operaciones y cuentas por cobrar.
3. Añadir persistencia, sincronización y manejo de errores/carga.
4. Incorporar pruebas para rutas y flujos críticos.
5. Completar validación de accesibilidad y preparar autenticación y configuración de producción.
