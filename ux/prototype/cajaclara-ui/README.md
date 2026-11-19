# CajaClara UI — Prototipo Vue

Documentación técnica del prototipo frontend de alta fidelidad. Para la investigación UX, el alcance del MVP y el proceso de diseño, consulta el [README de Diseño UX](../../README.md).

## Estado técnico

### Implementado

- Vistas navegables de Dashboard, Compras y ventas, Cuentas por cobrar y Resumen mensual.
- Formularios, filtros, búsqueda y detalle; la fuente es mock o API según el módulo y el entorno.
- Layout responsive y design tokens compartidos.
- Login JWT, restauración de sesión, refresh automático, perfil y logout.
- Dashboard, Resumen mensual, Compras y ventas y Cuentas por cobrar conectados a los endpoints financieros con JWT, estados de carga/error/vacío y reintento.
- Cobros solicita solo la página visible y envía al servidor el estado, la búsqueda y el orden; sus indicadores se consultan por separado desde `resumen.por_estado`.
- Tras pagar o revertir un cobro se recargan la página actual, sus indicadores y el contador lateral desde `resumen.total_alertas`.
- Dashboard y Resumen filtran productos con `con_ventas=true`; el encabezado usa el periodo seleccionado en estas vistas cuando está activo el modo API.
- Favicon SVG enlazado desde el documento HTML.
- Resumen mensual permite exportar ventas a Excel con sus filtros activos, exclusivamente en modo API.
- Modo mock explícito e independiente para Dashboard, Resumen mensual, Compras y ventas y Cuentas por cobrar.
- Cuentas por cobrar permite consultar facturas, registrar pagos completos y revertirlos; sus indicadores usan el resumen global de la API.

### En desarrollo

Sincronización automática entre pantallas sin una nueva carga.

### Pendiente

- Sincronizar automáticamente otras vistas tras una operación (Dashboard y Resumen recuperan los totales actualizados en su próxima carga).
- Añadir pruebas automatizadas y completar la validación de accesibilidad.

### Fuera del alcance actual

Pagos parciales, gestión de usuarios, facturación electrónica, inventario automático y notificaciones reales por WhatsApp o correo.

> La autenticación y, en modo API, Dashboard, Resumen mensual, Compras y ventas y Cuentas por cobrar se comunican con Backend. Cada módulo usa una sola fuente por ejecución.

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
├── public/favicon.svg
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
    ├── composables/useAuth.js
    ├── router/index.js
    ├── services/
    │   ├── apiClient.js
    │   ├── apiAdapters.js
    │   ├── dashboardService.js
    │   ├── operationsService.js
    │   ├── receivablesService.js
    │   ├── authService.js
    │   ├── optionsService.js
    │   └── summaryService.js
    ├── utils/formatters.js
    └── views/
        └── LoginView.vue
```

`vite.config.js` configura el plugin de Vue, el alias `@` hacia `src/` y el puerto 5173. `dist/` es un directorio generado por el build.

## Vistas y componentes existentes

### Vistas (`src/views/`)

| Archivo | Responsabilidad |
| --- | --- |
| `DashboardView.vue` | Indicadores, acciones rápidas, flujo semanal, cobros prioritarios, movimientos recientes y productos destacados. |
| `OperationsView.vue` | Compras y ventas, filtros, búsqueda, paginación, detalle y registro mediante API o mock. |
| `ReceivablesView.vue` | Cuentas por cobrar, estados, filtros, búsqueda, paginación, detalle y pago completo/reversión mediante API o mock. |
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
| `/login` | Inicio de sesión | Pública |
| `/` | Dashboard | Protegida por JWT; mock o API según entorno |
| `/operaciones` | Compras y ventas | Protegida por JWT; mock o API según entorno |
| `/cobros` | Cuentas por cobrar | Protegida por JWT; mock o API según entorno |
| `/resumen` | Resumen mensual | Protegida por JWT; mock o API según entorno |
| `/dashboard` | Redirección a `/` | Activa |
| Ruta desconocida | Redirección a `/` | Activa |

Una visita no autenticada a una ruta protegida se envía a `/login`; después del login se recupera la ruta solicitada. Una sesión válida que abre `/login` va al Dashboard. El layout de login no muestra header, sidebar ni navegación inferior.

## Datos mock y comportamiento local

| Archivo | Contenido usado por el prototipo |
| --- | --- |
| `src/data/dashboardMock.js` | Negocio y periodo de ejemplo, KPI, flujo semanal, cobros prioritarios, operaciones recientes y productos destacados. |
| `src/data/operationsMock.js` | Fuente mock exclusiva de Compras y ventas: operaciones, clientes y catálogo de productos. |
| `src/data/receivablesMock.js` | Cuentas por cobrar y datos de detalle asociados. |
| `src/data/monthlySummaryMock.js` | Datos del resumen por periodo, incluidos indicadores, desglose y actividad. |

En modo mock, Compras y ventas y Cuentas por cobrar mantienen estado local y no persisten entre recargas ni actualizan otros módulos. En modo API, ambas vistas consultan y guardan exclusivamente mediante servicios y `apiClient`. No hay pagos parciales.

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

La URL del Backend se configura con Vite. Crea un `.env.local` a partir de `.env.example`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_USE_MOCKS=true
```

`VITE_USE_MOCKS=true` usa mocks exclusivamente en Dashboard, Resumen mensual, Compras y ventas y Cuentas por cobrar; esta última usa solo `receivablesMock.js`. Con `VITE_USE_MOCKS=false` estas vistas usan la API con JWT y no hacen fallback a mocks. La URL base se lee en `src/services/apiClient.js`; los componentes no contienen URLs de Backend. Reinicia Vite después de cambiar variables `VITE_*`. No guardes `.env.local` en Git.

### Contrato JWT integrado

Se usan únicamente estas rutas documentadas:

| Método | Ruta | Contrato |
| --- | --- | --- |
| `POST` | `/api/auth/login/` | Request `{ "username": "...", "password": "..." }`; respuesta `{ "access": "...", "refresh": "...", "usuario": { "id", "username", "nombre", "email", "es_admin" } }`. |
| `POST` | `/api/auth/refresh/` | Request `{ "refresh": "..." }`; respuesta con `access` y un `refresh` rotado. |
| `POST` | `/api/auth/logout/` | Request `{ "refresh": "..." }`; invalida el refresh. Backend confirma `200`; el cliente limpia ambos tokens incluso si la llamada falla. |
| `GET` | `/api/auth/perfil/` | Requiere `Authorization: Bearer <access>` y devuelve `id`, `username`, `nombre`, `email` y `es_admin`. |

No existe registro público; las cuentas las crea un administrador. Los errores documentados son `401` para credenciales inválidas y `429` al superar 10 intentos de login por minuto. El mensaje de credenciales inválidas es “Usuario o contraseña incorrectos.”. Los errores de refresh inválido se manejan como sesión expirada sin mostrar respuestas sensibles.

### Almacenamiento y expiración

El Backend recomienda `localStorage`: access en `cc_access` y refresh en `cc_refresh`. El access dura 30 minutos y el refresh 7 días por defecto (configurables en Backend). Al recibir `401` en una petición protegida, el cliente comparte un único refresh concurrente, guarda el par rotado y reintenta esa petición una sola vez. Si refresh falla, se eliminan ambos tokens, se redirige al login y se conserva la ruta solicitada como contexto.

El logout invalida el refresh en Backend y elimina ambos valores locales. `localStorage` persiste tras recargar, pero es accesible desde JavaScript; un XSS podría robar tokens. No son cookies `HttpOnly`, no se registran en consola y no se muestran en mensajes de error. Esta estrategia debe revisarse antes de producción.

### CORS

Backend permite por defecto `http://localhost:5173` y `http://127.0.0.1:5173`. Al publicar el frontend en otro origen, ese origen debe agregarse a `CORS_ALLOWED_ORIGINS` en Backend. La API usa JSON y no depende de cookies.

## Deploy en Vercel

[Ver prototipo desplegado en Vercel](https://tdcajaclara-cajaclara-ui-omega.vercel.app/)

El login requiere que `VITE_API_BASE_URL` apunte a un Backend accesible. Configura `VITE_USE_MOCKS=true` para el modo de demostración o `false` para consultar Dashboard, Resumen mensual, Compras y ventas y Cuentas por cobrar en Backend.

## Integración financiera conectada

Dashboard y Resumen mensual llaman, a través de servicios y `apiClient`, a:

| Endpoint | Datos mostrados |
| --- | --- |
| `GET /api/finanzas/opciones-filtros/` | Rango de fechas disponible y canales `Física` / `En Línea`; determina el periodo inicial. |
| `GET /api/finanzas/resumen-mensual/` | Indicadores, flujo de caja, ventas por estado y canal. |
| `GET /api/finanzas/resumen-agrupado/` con `agrupacion=semanas_mes` | Flujo semanal y etiquetas entregadas por Backend. |
| `GET /api/finanzas/exportar-excel/` | Descarga autenticada del Excel con filtros de fecha y canal activos. |
| `GET /api/finanzas/operaciones/` | Operaciones recientes y del periodo, fechas ISO y montos. |
| `GET /api/finanzas/alertas-cobro/` | Alertas prioritarias operativas vigentes a la fecha actual. |
| `GET /api/finanzas/productos/` | Productos más vendidos del periodo/canal, ordenados por unidades vendidas. |

`src/services/apiAdapters.js` valida y adapta las respuestas sin deducir el contrato de los mocks. `dashboardService.js`, `summaryService.js` y `optionsService.js` separan consultas y selección de fuente. Las peticiones protegidas reutilizan JWT y refresh automático del `apiClient`.

`exportService.js` solicita `/api/finanzas/exportar-excel/` como Blob mediante `apiClient`, enviando `fecha_inicio`, `fecha_fin` y `tipo_compra` cuando hay un canal seleccionado. Descarga el archivo con el nombre de `Content-Disposition` o `reporte_ventas.xlsx` si falta, y revoca la URL temporal. En modo mock el botón está deshabilitado y se muestra “Exportación disponible con datos reales”.

Compras y ventas usa `operationsService.js` y estos endpoints con JWT y refresh: `GET /api/finanzas/operaciones/` (paginación, filtros, orden y resumen global de resultados), `GET /api/finanzas/facturas/{id}/` (detalle), `GET /api/finanzas/opciones/clientes/`, `GET /api/finanzas/opciones/productos/`, `POST /api/finanzas/clientes/`, `POST /api/finanzas/facturas/` y `POST /api/finanzas/gastos/`. El formulario registra ventas al contado o a crédito y gastos asociados a producto; los errores `400` del alta de cliente aparecen junto a sus campos. No se implementan eliminación, anulación ni pagos parciales.

`receivablesService.js` conecta Cuentas por cobrar con JWT y refresh. En modo API, el listado pide únicamente la página actual (`page_size=10`) y envía al servidor estado, búsqueda y orden por vencimiento; la búsqueda se aplica tras una pausa de 300 ms. Los indicadores y contadores de las pestañas provienen de `resumen.por_estado` en una consulta independiente (`page_size=1`). El detalle consulta `/api/finanzas/facturas/{id_factura}/` solo al abrirse. Los recordatorios se limitan a una página de `/api/finanzas/alertas-cobro/`. El contador del layout usa `resumen.total_alertas` de esa ruta con `page_size=1`, se consulta al iniciar sesión y se actualiza tras pagar o revertir. Pagar acepta fecha opcional y siempre es por el total. La reversión no envía body. Los recordatorios muestran y copian `mensaje_sugerido`, pero no se envían. En modo mock se mantienen búsqueda, filtro, orden y paginación locales.

Limitaciones del contrato: no hay desglose de gastos por categoría; se muestra el total de gastos en insumos. Las alertas operativas no corresponden al periodo seleccionado y no tienen filtro por canal. La métrica `ranking-productos` es histórica, por lo que las vistas usan en su lugar el endpoint `/productos/`, que sí permite filtrar por periodo y canal. Los gastos carecen de canal. Cobros no permite crear cuentas ni registrar pagos parciales. Dashboard y Resumen obtienen los totales actualizados en su próxima carga; no hay sincronización automática de otras vistas. Ver [guía de integración UX/Backend](../../INTEGRACION-BACKEND.md). Backend comparte actualmente el mismo negocio entre usuarios autenticados.

Tras una operación de pago o reversión, Cobros actualiza inmediatamente su página, resumen e indicador lateral. Dashboard y Resumen reflejan cambios de otros módulos al volver a cargarse; no existe sincronización automática general entre vistas.

## Pruebas y calidad

No hay suite de pruebas automatizadas, comandos de lint ni formateo en `package.json`. El build disponible es:

```bash
npm run build
```

## Limitaciones

- Dashboard, Resumen mensual, Compras y ventas y Cuentas por cobrar usan una sola fuente por ejecución; API fallida produce estado de error y no fallback a mocks.
- Compras y ventas no implementa edición, eliminación, anulación ni pagos parciales. Cuentas por cobrar no permite crear cuentas ni registrar pagos parciales.
- El contrato no proporciona desglose de gastos por categorías ni filtro por canal para las alertas.
- Las alertas se calculan a la fecha actual, no al periodo histórico seleccionado.
- Los mocks de cada módulo son independientes y no se sincronizan.
- La autenticación JWT usa `localStorage` y no se ha hecho una auditoría de seguridad de producción.
- No hay pagos parciales.
- No se ha completado una auditoría de accesibilidad.
- `PlaceholderView.vue` existe, pero no está asociado a una ruta activa.

## Roadmap técnico

1. Sincronizar automáticamente los cambios entre vistas.
2. Incorporar pruebas automatizadas para rutas, autenticación y flujos críticos.
3. Completar validación de accesibilidad y revisar almacenamiento de tokens para producción.
