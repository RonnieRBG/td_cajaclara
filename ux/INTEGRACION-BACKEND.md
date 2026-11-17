# Integración UX y Backend

## Estado tras integrar las ramas

- El proyecto Django está en la raíz (`manage.py`, `cajaclara/`, `finanzas/`, `usuarios/`); la aplicación Vue 3/Vite permanece en `ux/prototype/cajaclara-ui/`.
- Backend de referencia: `upstream/backend`, commit `ce68c3c1835fbfef96ffb6bc1deff3fd5dfaf9ef`. Contratos y procedimientos: [`API_DOCUMENTACION.md`](../API_DOCUMENTACION.md) y [`ACOPLAMIENTO.md`](../ACOPLAMIENTO.md).
- El login JWT, refresh, perfil, logout y protección de rutas ya están conectados en Vue. No existe registro público.
- Dashboard, Compras y ventas, Cuentas por cobrar y Resumen mensual todavía usan mocks; el merge por sí solo no los conecta ni cambia sus fuentes de datos.
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

## Límites importantes del contrato

- Venta: requiere `id_cliente` y al menos un item con `id_producto` y `cantidad`; admite `precio_venta` y `costo_venta`. `tipo_compra` acepta `Física` o `En Línea`. Crédito usa `por_cobrar: true` y `fecha_vencimiento`; al contado no envía vencimiento.
- Gasto: es un gasto de insumo asociado a `id_producto`, con `monto` entero positivo. No hay proveedor, categoría de gasto ni gastos operativos genéricos.
- Pago: solo pago completo; `fecha_pago` es opcional. Reversión sin body. No existen pagos parciales ni anulación de ventas.
- No existe precio de catálogo; el selector puede sugerir `ultimo_precio_venta` y `ultimo_costo_venta` de la última venta.
- Todos los usuarios autenticados acceden actualmente al mismo negocio.
- Las alertas operativas se calculan a la fecha actual por defecto; no confundirlas con métricas SQL históricas de corte fijo.

## Entorno y estructura

El frontend lee `VITE_API_BASE_URL` desde Vite; su ejemplo local es `http://127.0.0.1:8000/api`. No guardar URLs de producción, secretos, tokens ni archivos `.env` en componentes o Git. Django permite por defecto los orígenes locales de Vite en los puertos `localhost:5173` y `127.0.0.1:5173`; producción se configura mediante `CORS_ALLOWED_ORIGINS`.

La integración futura de datos debe realizarse por servicios/adaptadores dentro de `ux/prototype/cajaclara-ui/src/`, manteniendo por separado la investigación, user flows y wireframes. Cada vista debe seleccionar una sola fuente (mock o API), mostrar carga/error/vacío y reintentar sin fallback silencioso. No retirar los mocks hasta validar autenticación, parámetros y respuesta del endpoint.

Para validar la estructura fusionada:

```powershell
python manage.py check
python manage.py test
cd ux/prototype/cajaclara-ui
npm install
npm run build
```
