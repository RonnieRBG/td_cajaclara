# Integración UX y Backend

## Estado tras integrar las ramas

- El proyecto Django está en la raíz (`manage.py`, `cajaclara/`, `finanzas/`, `usuarios/`); la aplicación Vue 3/Vite permanece en `ux/prototype/cajaclara-ui/`.
- Backend de referencia: `upstream/backend`, commit `ce68c3c1835fbfef96ffb6bc1deff3fd5dfaf9ef`. Contratos y procedimientos: [`API_DOCUMENTACION.md`](../API_DOCUMENTACION.md) y [`ACOPLAMIENTO.md`](../ACOPLAMIENTO.md).
- El login JWT, refresh, perfil, logout y protección de rutas ya están conectados en Vue. No existe registro público.
- Dashboard y Resumen mensual consumen los endpoints financieros documentados cuando `VITE_USE_MOCKS=false`; ambos conservan los mocks, seleccionados explícitamente con `VITE_USE_MOCKS=true`.
- Compras y ventas y Cuentas por cobrar siguen usando mocks. Este cambio no escribe ni modifica contratos, modelos, endpoints o pruebas de Django.
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
| `GET /api/finanzas/operaciones/` | Operaciones recientes, sus fechas/montos y conteos agregados; el resumen mensual muestra las primeras cinco. |
| `GET /api/finanzas/alertas-cobro/` | Cobros prioritarios operativos a la fecha actual (primeros tres); no dependen del periodo/canal del resumen. |
| `GET /api/finanzas/productos/` | Productos más vendidos del periodo (`fecha_inicio`, `fecha_fin`, `tipo_compra`, `ordering=-total_vendido`, `page_size=4`). |

`src/services/apiAdapters.js` valida la forma documentada, convierte montos a `Number` y adapta las respuestas a las propiedades de los componentes. Los montos permanecen enteros en CLP y las fechas ISO se conservan. `optionsService.js` controla la fuente y las opciones; `dashboardService.js` y `summaryService.js` realizan las consultas con `apiRequest`.

No existe en el contrato un desglose de gastos por categoría: Resumen mensual muestra el total de `gastos_insumo`, sin crear categorías. Alertas son operativas y de hoy, no históricas del periodo seleccionado. Los productos se consultan mediante `GET /productos/`, que sí admite periodo y canal; la métrica histórica `ranking-productos` no se usa en estas vistas. Las operaciones y los resúmenes filtrados respetan el canal; Backend documenta que los gastos no tienen canal.

### Fuente explícita

Crear `ux/prototype/cajaclara-ui/.env.local` desde `.env.example`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_USE_MOCKS=true
```

- `VITE_USE_MOCKS=true`: solo mocks para cada una de las vistas conectadas.
- `VITE_USE_MOCKS=false`: solo API para cada vista; requiere login y Backend accesible.
- Un error de API se muestra con opción de reintentar; no cambia automáticamente a mocks.
- Al cambiar variables `VITE_*`, reiniciar Vite. `.env.local` no se versiona.

## Límites importantes del contrato

- Venta: requiere `id_cliente` y al menos un item con `id_producto` y `cantidad`; admite `precio_venta` y `costo_venta`. `tipo_compra` acepta `Física` o `En Línea`. Crédito usa `por_cobrar: true` y `fecha_vencimiento`; al contado no envía vencimiento.
- Gasto: es un gasto de insumo asociado a `id_producto`, con `monto` entero positivo. No hay proveedor, categoría de gasto ni gastos operativos genéricos.
- Pago: solo pago completo; `fecha_pago` es opcional. Reversión sin body. No existen pagos parciales ni anulación de ventas.
- No existe precio de catálogo; el selector puede sugerir `ultimo_precio_venta` y `ultimo_costo_venta` de la última venta.
- Todos los usuarios autenticados acceden actualmente al mismo negocio.
- Las alertas operativas se calculan a la fecha actual por defecto; no confundirlas con métricas SQL históricas de corte fijo.

## Entorno y estructura

El frontend lee `VITE_API_BASE_URL` desde Vite; su ejemplo local es `http://127.0.0.1:8000/api`. No guardar URLs de producción, secretos, tokens ni archivos `.env` en componentes o Git. Django permite por defecto los orígenes locales de Vite en los puertos `localhost:5173` y `127.0.0.1:5173`; producción se configura mediante `CORS_ALLOWED_ORIGINS`.

La integración restante debe realizarse por servicios/adaptadores dentro de `ux/prototype/cajaclara-ui/src/`, manteniendo por separado la investigación, user flows y wireframes. Cada vista selecciona una sola fuente (mock o API), muestra carga/error/vacío y permite reintentar sin fallback silencioso.

Para validar la estructura fusionada:

```powershell
python manage.py check
python manage.py test
cd ux/prototype/cajaclara-ui
npm run build
npm run dev
```
