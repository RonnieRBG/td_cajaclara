# Reporte de Reconciliación y Simulación de Cobros — Etapa 4 (Tareas 18 y 19)

> **Fecha de corte de simulación (`cuenta_por_cobrar`):** `2022-09-01`
> **Base local verificada:** `cajaclara_local.db` (SQLite con `PRAGMA foreign_keys = ON` y restricciones `CHECK`).

## 1. Conteo de Registros Cargados (Tarea 18)

| Tabla | Filas cargadas | Integridad PK / FK / CHECK |
| :--- | ---: | :---: |
| `cliente` | 2.000 | ✅ 100% íntegra |
| `producto` | 7.488 | ✅ 100% íntegra |
| `venta` | 100.067 | ✅ 100% íntegra |
| `detalle_venta` | 103.489 | ✅ 100% íntegra |
| `cuenta_por_cobrar` | 14.928 | ✅ 100% íntegra |
| `gastos_insumo` | 20.000 | ✅ 100% íntegra |

## 2. Reconciliación Matemática contra el Origen (`ventas_originales_fuente.csv`)

| Métrica | Origen (Etapa 2) | Base de Datos (Etapa 4) | Diferencia |
| :--- | ---: | ---: | ---: |
| Líneas de venta | 103.489 | 103.489 | 0 |
| Unidades vendidas | 357.708 | 357.708 | 0 |
| Ingreso total (CLP) | $403.521.023 | $403.521.023 | $0 |
| Costo total (CLP) | $312.160.447 | $312.160.447 | $0 |
| Margen bruto total (CLP) | $91.360.576 | $91.360.576 | $0 |
| Productos únicos vendidos | 7.488 | 7.488 | 0 |
| Total cuentas por cobrar (CLP) | $57.339.252 | $57.339.252 | $0 |
| Total gastos insumos (CLP) | $24.484.481 | $24.484.481 | $0 |

## 3. Simulación de Cobros y Estados (`cuenta_por_cobrar` — Tarea 19)

| Estado | Cuentas | % Cuentas | Monto Total (CLP) |
| :--- | ---: | ---: | ---: |
| `PAGADA` | 14.920 | 99.95% | $57.328.527 |
| `PENDIENTE` | 2 | 0.01% | $3.155 |
| `VENCIDA` | 6 | 0.04% | $7.570 |

### Reglas validadas en la carga
- `PRAGMA foreign_key_check`: **0 errores**.
- Coherencia `venta.por_cobrar = 1` ↔ existencia 1:1 en `cuenta_por_cobrar`: **0 descuadres**.
- Coherencia `cuenta_por_cobrar.monto = SUM(cantidad * precio_venta)` por factura: **0 descuadres**.
- Coherencia `fecha_pago >= venta.fecha` para todas las cuentas `PAGADA` y `fecha_pago IS NULL` para `PENDIENTE`/`VENCIDA`: **100% aprobada**.
