# Integración UX y Backend

## Estado tras integrar las ramas

- El proyecto Django está en la raíz (`manage.py`, `cajaclara/`, `finanzas/`, `usuarios/`); la aplicación Vue 3/Vite permanece en `ux/prototype/cajaclara-ui/`.
- Backend de referencia: `upstream/backend`, incorporado desde el commit `5815003`. Contratos y procedimientos: [`API_DOCUMENTACION.md`](../API_DOCUMENTACION.md) y [`ACOPLAMIENTO.md`](../ACOPLAMIENTO.md).
- El login JWT, refresh, perfil, logout y protección de rutas ya están conectados en Vue. No existe registro público.
- Dashboard, Resumen mensual, Compras y ventas y Cuentas por cobrar consumen los endpoints financieros documentados cuando `VITE_USE_MOCKS=false`; cada vista conserva mocks seleccionados explícitamente con `VITE_USE_MOCKS=true`.
- Este cambio no escribe ni modifica contratos, modelos, endpoints o pruebas de Django.
- El esquema real contiene `cliente`, `producto`, `venta`, `detalle_venta`, `cuenta_por_cobrar` y `gastos_insumo`. No usar los modelos de un contrato anterior (`Categoria`, `Movimiento`) como fuente.

## Endpoints disponibles

Todos los endpoints financieros se sirven bajo `/api/finanzas/` y requieren autenticación JWT salvo que la documentación indique lo contrario.

| Capacidad | Métodos/rutas documentados |
| --- | --- |
| Opciones de filtros | `GET /opciones-filtros/` |
| Resúmenes | `GET /resumen-mensual/`, `GET /resumen-agrupado/` |
| Exportación | `GET /exportar-excel/` |
| Clientes | `GET/POST /clientes/`, `GET /opciones/clientes/` |
| Productos | `GET /productos/`, `GET /opciones/productos/` |
| Ventas | `GET/POST /facturas/`, `GET /facturas/{id_factura}/`, `GET /ventas/` |
| Cuentas por cobrar | `GET /cuentas-por-cobrar/`, `POST /cuentas-por-cobrar/{id_cuenta}/pagar/`, `POST /cuentas-por-cobrar/{id_cuenta}/revertir-pago/` |
| Gastos en insumos | `GET/POST /gastos/` |
| Operaciones combinadas | `GET /operaciones/` |
| Alertas y métricas | `GET /alertas-cobro/`, `GET /metricas/`, `GET /metricas/{nombre}/` |

El contrato completo —parámetros, esquemas, códigos de error y respuestas— está en `API_DOCUMENTACION.md`; no deducir campos de los mocks.

## Conexión de Dashboard y Resumen mensual

Las peticiones pasan por `src/services/apiClient.js` con Bearer JWT y refresh automático. Componentes no llaman `fetch`:

| Endpoint | Uso en pantalla |
| --- | --- |
| `GET /api/finanzas/opciones-filtros/` | Rango disponible y canales; fija el periodo inicial desde `rango_fechas_disponible.max`. |
| `GET /api/finanzas/resumen-mensual/` | KPIs, flujo de caja, ventas por estado y canal; acepta fechas y `tipo_compra`. |
| `GET /api/finanzas/resumen-agrupado/?agrupacion=semanas_mes` | Flujo semanal; conserva las etiquetas de `periodo` de Backend. |
| `GET /api/finanzas/exportar-excel/` | Archivo `.xlsx` del detalle de ventas, con los filtros de `resumen-mensual`. |
| `GET /api/finanzas/operaciones/` | Operaciones recientes, sus fechas/montos y conteos agregados; el resumen mensual muestra las primeras cinco. |
| `GET /api/finanzas/alertas-cobro/` | Cobros prioritarios operativos a la fecha actual (primeros tres); no dependen del periodo/canal del resumen. |
| `GET /api/finanzas/productos/` | Productos con ventas del periodo (`fecha_inicio`, `fecha_fin`, `tipo_compra`, `ordering=-total_vendido`, `con_ventas=true`, `page_size=4`). |

`src/services/apiAdapters.js` valida la forma documentada, convierte montos a `Number` y adapta las respuestas a las propiedades de los componentes. Los montos permanecen enteros en CLP y las fechas ISO se conservan. `optionsService.js` controla la fuente y las opciones; `dashboardService.js` y `summaryService.js` realizan las consultas con `apiRequest`.

El botón Exportar Excel de Resumen mensual usa `exportService.js` y envía `fecha_inicio`, `fecha_fin` y, si está seleccionado, `tipo_compra`, iguales a los filtros activos del periodo. `apiClient.js` admite `responseType: 'blob'` para este endpoint y conserva el refresh JWT con un único reintento; las peticiones JSON existentes no cambian. El archivo se descarga usando `Content-Disposition` o `reporte_ventas.xlsx` como nombre alternativo, y se revoca la URL temporal. En modo mock, la exportación se deshabilita y se indica que está disponible con datos reales.

No existe en el contrato un desglose de gastos por categoría: Resumen mensual muestra el total de `gastos_insumo`, sin crear categorías. Alertas son operativas y de hoy, no históricas del periodo seleccionado. Los productos se consultan mediante `GET /productos/`, que sí admite periodo y canal; la métrica histórica `ranking-productos` no se usa en estas vistas. Las operaciones y los resúmenes filtrados respetan el canal; Backend documenta que los gastos no tienen canal.

### Integración de Compras y ventas

`operationsService.js` selecciona una sola fuente según `VITE_USE_MOCKS`. En modo API reutiliza `apiRequest` (JWT y refresh) y `apiAdapters.js` para:

| Acción | Endpoint |
| --- | --- |
| Listar operaciones, filtros, orden y páginas; resumen independiente de la página | `GET /operaciones/` |
| Ver detalle de una venta | `GET /facturas/{id_factura}/` |
| Buscar clientes y productos | `GET /opciones/clientes/`, `GET /opciones/productos/` |
| Crear cliente, venta al contado/crédito o gasto en insumos | `POST /clientes/`, `POST /facturas/`, `POST /gastos/` |

El formulario envía `fecha_vencimiento` solo para ventas a crédito y usa `ultimo_precio_venta` / `ultimo_costo_venta` como sugerencias; solicita ambos si no hay valores anteriores. Un error de API permanece visible con opción de reintento, sin alternar a mocks. No se implementan edición, eliminación, anulación ni pagos parciales.

### Integración de Cuentas por cobrar

`receivablesService.js` selecciona una sola fuente según `VITE_USE_MOCKS`. En modo API reutiliza `apiRequest` (JWT y refresh) y los adaptadores compartidos:

| Acción | Endpoint |
| --- | --- |
| Listar la página visible de cuentas | `GET /cuentas-por-cobrar/?estado=&search=&ordering=&page=&page_size=10` |
| Obtener los indicadores y contadores de estado, independientemente de los filtros activos | `GET /cuentas-por-cobrar/?page=1&page_size=1` (`resumen.por_estado`) |
| Obtener recordatorios y el texto sugerido por Backend (una página) | `GET /alertas-cobro/?page_size=10` |
| Obtener/actualizar el indicador lateral de cobros | `GET /alertas-cobro/?page_size=1` (`resumen.total_alertas`) |
| Consultar productos y líneas de factura al abrir el detalle | `GET /facturas/{id_factura}/` |
| Registrar un pago completo | `POST /cuentas-por-cobrar/{id_cuenta}/pagar/` |
| Revertir un pago | `POST /cuentas-por-cobrar/{id_cuenta}/revertir-pago/` |

En modo API, el listado pide solamente la página visible; búsqueda por cliente/factura, estado y orden por vencimiento se envían al servidor. La escritura espera 300 ms antes de buscar. Los indicadores y contadores de las pestañas se cargan con una consulta independiente sin estado y se derivan de `resumen.por_estado`, no de los registros visibles. Las alertas de recordatorio se limitan a una página. El indicador lateral usa `resumen.total_alertas`, se carga al iniciar sesión y se actualiza después de pagar o revertir. El detalle consulta la factura únicamente al abrirse, ya que el listado no incluye productos.

El pago es completo y acepta `fecha_pago` opcional; al omitirla no se envía body. La reversión es un POST sin body. No se registran método ni referencia de pago, no se permiten abonos ni crear cuentas manualmente. El recordatorio solo muestra/copia `mensaje_sugerido` devuelto por la API; no hay envío de mensajes documentado. Después de pagar o revertir se recargan la página actual, los indicadores de `resumen.por_estado`, las alertas y el indicador lateral. Dashboard y Resumen vuelven a obtener sus totales en su próxima carga.

Dashboard y Resumen solicitan productos con `con_ventas=true` para omitir productos sin ventas en el periodo y canal elegidos. El encabezado muestra el periodo seleccionado en esas dos vistas y lo oculta en las demás cuando se usa la API; el modo mock conserva el periodo y los valores simulados actuales.

### Fuente explícita

Crear `ux/prototype/cajaclara-ui/.env.local` desde `.env.example`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_USE_MOCKS=true
```

- `VITE_USE_MOCKS=true`: solo mocks para cada una de las vistas conectadas (Cuentas por cobrar usa exclusivamente `receivablesMock.js`).
- `VITE_USE_MOCKS=false`: solo API para cada vista; requiere login y Backend accesible.
- Un error de API se muestra con opción de reintentar; no cambia automáticamente a mocks.
- Al cambiar variables `VITE_*`, reiniciar Vite. `.env.local` no se versiona.

## Límites importantes del contrato

- Venta: requiere `id_cliente` y al menos un item con `id_producto` y `cantidad`; admite `precio_venta` y `costo_venta`. `tipo_compra` acepta `Física` o `En Línea`. Crédito usa `por_cobrar: true` y `fecha_vencimiento`; al contado no envía vencimiento.
- Gasto: es un gasto de insumo asociado a `id_producto`, con `monto` entero positivo. No hay proveedor, categoría de gasto ni gastos operativos genéricos.
- Pago: solo pago completo; `fecha_pago` es opcional. Reversión sin body. No existen pagos parciales ni anulación de ventas.
- Cuentas por cobrar: el listado incluye `estado_actual` y `resumen`; las alertas operativas incluyen `mensaje_sugerido` cuando Backend lo entrega. No hay un endpoint documentado para crear cuentas ni enviar recordatorios.
- No existe precio de catálogo; el selector puede sugerir `ultimo_precio_venta` y `ultimo_costo_venta` de la última venta.
- Todos los usuarios autenticados acceden actualmente al mismo negocio.
- Las alertas operativas se calculan a la fecha actual por defecto; no confundirlas con métricas SQL históricas de corte fijo.

## Entorno y estructura

El frontend lee `VITE_API_BASE_URL` desde Vite; su ejemplo local es `http://127.0.0.1:8000/api`. No guardar URLs de producción, secretos, tokens ni archivos `.env` en componentes o Git. Django permite por defecto los orígenes locales de Vite en los puertos `localhost:5173` y `127.0.0.1:5173`; producción se configura mediante `CORS_ALLOWED_ORIGINS`.

Las vistas financieras conectadas seleccionan una sola fuente (mock o API), muestran carga/error/vacío y permiten reintentar sin fallback silencioso.

Para validar la estructura fusionada:

```powershell
python manage.py check
python manage.py test
cd ux/prototype/cajaclara-ui
npm run build
npm run dev
```
