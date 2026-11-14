# Auditoría de Integridad — Diagrama MER (Etapa 1), Etapa 2 y Etapa 3

> **Propósito:** Verificar la consistencia técnica, referencial y matemática de los entregables previos (`Etapa_1 Diagrama_MER.svg`, Etapa 2 y Etapa 3) antes de ejecutar la carga en la nube (Etapa 4) y el cálculo de métricas (Etapa 5).

---

## 1. Resumen Ejecutivo

| Componente | Estado | Veredicto |
| :--- | :---: | :--- |
| **Etapa 2: Limpieza y estandarización** | 🟡 Aprobado con observación | Totales, deduplicación, nulos, fechas y valores positivos son íntegros. Se detectó 1 artefacto puntual de escala (`< 15.0`) en 13 productos (`0.87%` del ingreso) que debe documentarse al interpretar precios unitarios extremos. |
| **Etapa 3: Integridad de los 6 CSV** | 🟢 Íntegro | Claves primarias únicas, 0 nulos, 100% de integridad referencial entre las 6 tablas y cuadratura exacta al peso chileno (`$403.521.023` CLP) frente a `ventas_originales_fuente.csv`. |
| **Etapa 1 vs Etapa 3: `Etapa_1 Diagrama_MER.svg`** | 🔴 Requiere corrección de esquema | El diagrama SVG en Lucidchart tiene **6 discrepancias de tipos/tamaños y cardinalidad** respecto a los CSV reales que harían fallar un `CREATE TABLE` o carga en PostgreSQL si se replican literalmente. |
| **Cobertura funcional frente a `Tareas.csv`** | 🟡 Brechas previstas para Etapa 4 | `cuenta_por_cobrar.csv` quedó en versión MVP (sin `estado` ni `fecha_pago`), lo cual se completa en la **Tarea 19** de Etapa 4 para habilitar flujo de caja, días de atraso y morosidad en Etapa 5. |

---

## 2. Verificación de Integridad — Etapa 2 (Limpieza de Datos)

Se auditó el flujo completo `ventas_db.ventas.zip` → `ventas_limpias.zip` → `ventas_originales_fuente.csv` y el cuaderno [limpieza_datos_etapa2.ipynb](./Etapa_2%20Limpieza%20de%20datos/limpieza_datos_etapa2.ipynb).

### 2.1 Controles aprobados (100% verificados)
1. **Deduplicación exacta (`RL-01`):**
   - Origen (`ventas_db.ventas.csv`): **1.002.986** filas y 12 columnas.
   - Duplicados exactos en las 11 columnas de negocio (excluyendo `_id`): **2.986** filas.
   - Dataset limpio (`ventas_limpias.csv`): **1.000.000** filas, **0** duplicados remanentes, **0** `_id` repetidos.
2. **Extracción de transacciones maestras (`ventas_originales_fuente.csv`):**
   - **103.489** filas correspondientes a los **103.489** `source_row_id` únicos del millón de filas (conservando la réplica con menor `replica_id`).
   - El 100% de sus `_id` coincide fila a fila con `ventas_limpias.csv`.
3. **Nulos, formatos y positividad:**
   - **0** valores nulos en todas las columnas de ambos archivos.
   - **0** registros con `cantidad <= 0`, `precio_venta <= 0` o `costo_venta <= 0`.
   - Fechas limpias en formato ISO 8601 UTC (`2010-01-05` a `2022-11-18` en `ventas_originales_fuente.csv`).
   - En `ventas_originales_fuente.csv`: **0** transacciones con margen negativo (`357.708` unidades, `$403.521.023` CLP de ingreso total, `$312.160.447` CLP de costo total y `$91.360.576` CLP de margen bruto). En `ventas_limpias.csv` existen 6 filas con leve margen negativo (réplicas promocionales documentadas en `RL-06`).

### 2.2 Hallazgos y observaciones detectadas en Etapa 2
1. **Artefacto de umbral en escala COP (`factor_escala_cop < 15.0`):**
   - En la celda 15 de [limpieza_datos_etapa2.ipynb](./Etapa_2%20Limpieza%20de%20datos/limpieza_datos_etapa2.ipynb), la escala se definió fila por fila con `np.where(df_limpio['precio_venta'] < 15.0, 1000.0, 10.0)`.
   - En el archivo crudo, **38 códigos `no_parte`** tienen precios alrededor de `14.1` a `15.8`, cruzando el corte de `15.0`. En `ventas_originales_fuente.csv`, **13 productos** (**969 filas = 0,94%**, **`$3.498.017` CLP = 0,87% del ingreso**) muestran saltos de ~100x para el mismo producto según la fila (por ejemplo, `P169578 - Gelatina Royal Frambuesa-Cereza-Fresa`: 524 filas con mediana `$46` CLP y 7 filas con mediana `$4.506` CLP; `P371029 - Esmalte Jolie`: 2 filas a `$43,5` CLP y 165 filas a `$4.404` CLP).
   - **Decisión de integridad:** No se alteran retroactivamente los archivos de Etapa 2/3 para preservar la trazabilidad y cuadratura exacta contra `ventas_originales_fuente.csv`; el artefacto queda documentado para no sesgar análisis de variación de precios por SKU en la Etapa 5.
2. **Aclaración de conteo en bitácora:** `resumen_limpieza_datos.md` menciona `4.916` fechas con barras (`DD/MM/YYYY`), cifra previa a eliminar duplicados; sobre el millón único final fueron `4.908` registros.

---

## 3. Verificación de Integridad — Etapa 3 (Tablas Relacionales CSV)

Se auditaron los 6 archivos generados por [Etapa_3_Elaboración_de_Tablas.ipynb](./Etapa_3%20Elaboracion%20de%20tablas/Etapa_3_Elaboración_de_Tablas.ipynb):

| Tabla CSV | Filas | Columnas | PK única | Nulos | Integridad Referencial (FK) |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `producto.csv` | 7.488 | 4 | ✅ `id_producto` | 0 | Catálogo completo (`7.488` `no_parte` únicos) |
| `cliente.csv` | 2.000 | 3 | ✅ `id_cliente` (`1..2000`) | 0 | Datos sintéticos únicos (nombre y teléfono) |
| `venta.csv` | 100.067 | 5 | ✅ `id_factura` | 0 | ✅ 100% `id_cliente` existe en `cliente` |
| `detalle_venta.csv` | 103.489 | 6 | ✅ `id_detalle` (`1..103489`) | 0 | ✅ 100% `id_factura` en `venta` y `id_producto` en `producto` |
| `cuenta_por_cobrar.csv` | 14.928 | 5 | ✅ `id_cuenta` (`1..14928`) | 0 | ✅ 100% `id_factura` en `venta` (`por_cobrar=True`), 100% `id_cliente` coincide con `venta.id_cliente` |
| `gastos_insumo.csv` | 20.000 | 4 | ✅ `id_gasto` (`1..20000`) | 0 | ✅ 100% `id_producto` existe en `producto` |

### 3.1 Validaciones de negocio confirmadas
- **Reconciliación exacta contra origen (`ventas_originales_fuente.csv`):**
  - Filas en `detalle_venta.csv` = **103.489** (= filas origen).
  - Suma de `cantidad` = **357.708** unidades (= origen).
  - Suma de `cantidad * precio_venta` = **`$403.521.023` CLP** (= origen).
  - Suma de `cantidad * costo_venta` = **`$312.160.447` CLP** (= origen).
  - Todas las `100.067` facturas de `venta.csv` tienen al menos 1 línea en `detalle_venta.csv` (`3.099` facturas tienen 2 o más líneas).
- **Consistencia de `cuenta_por_cobrar.csv`:**
  - `14.928` filas = exactamente el total de facturas con `por_cobrar = True` (`14,92%`).
  - `id_factura` es único en `cuenta_por_cobrar.csv` (relación `1 : 0..1` con `venta`).
  - En el 100% de las filas, `cuenta_por_cobrar.monto` coincide al peso con `SUM(cantidad * precio_venta)` en `detalle_venta.csv` (rango `$34` a `$880.999` CLP; suma total **`$57.339.252` CLP**).
  - En el 100% de las filas, `fecha_vencimiento > venta.fecha` (entre 15 y 60 días después; rango `2010-02-11` a `2022-09-09`).
- **Observación clave de cobertura temporal y gastos:**
  - Tal como se documentó en la Etapa 3, el rango `2010-01-05` a `2020-12-31` tiene **cobertura completa** (`101.052` líneas = `97,6%`), mientras que `2021-01-01` a `2022-11-18` tiene **cobertura parcial** por corte muestral de la fuente (`2.437` líneas = `2,4%`; solo 241 registros en todo 2022).
  - Sin embargo, `gastos_insumo.csv` fue generado con fechas **uniformes** entre `2010-01-05` y `2022-11-18` (~1.530 gastos/año y ~`$1,88M` CLP/año), lo que provoca que en 2022 el gasto sintético (`$1.747.895` CLP) supere artificialmente el margen de las ventas parciales (`$136.923` CLP). En la **Etapa 5**, todas las tendencias, flujo de caja y sustentabilidad deben analizarse filtrando o separando explícitamente la **cobertura completa (2010–2020)** de la **cobertura parcial (2021–2022)**.

---

## 4. Discrepancias Detectadas en el Diagrama MER (`Etapa_1 Diagrama_MER.svg`)

Al inspeccionar [Etapa_1 Diagrama_MER.svg](./Etapa_1%20Diagrama_MER.svg) contra los archivos CSV generados en Etapa 3, se detectaron **6 inconsistencias críticas** que impiden usar el diagrama tal como está para crear la base de datos en la nube (Etapa 4):

| # | Tabla / Relación | Qué dice el MER SVG actual | Realidad en los CSV de Etapa 3 | Corrección obligatoria para DDL / Lucidchart |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `Producto`, `Detalle_Venta`, `Gastos_insumo` (`id_producto`) | `int(4)` | Código alfanumérico de 7 caracteres (`P100055`) | Cambiar tipo a `VARCHAR(10)` en las 3 tablas. |
| **2** | `Producto.producto` (y otros textos) | `chart(100)` (typo `chart` y largo 100) | Largo máximo real en `producto.csv` es **108 caracteres** (`P951323`, `P329485`, `P493735` superan 100) | Corregir `chart` → `VARCHAR` y ampliar `producto` a **`VARCHAR(150)`** (o `TEXT`) para evitar error de truncamiento al cargar. |
| **3** | `Cuenta_por_cobrar.id_cliente` | `char(20)` | Entero `1..2000` (FK a `Cliente.id_cliente`) | Cambiar a `INTEGER` (`int(4)`). Un FK `char` no puede referenciar una PK `int` en PostgreSQL. |
| **4** | PKs `id_detalle`, `Id_cuenta`, `id_gasto` | `int(5)`, `int(4)` (con `I` mayúscula) y `int(4)` | `103.489` (6 dígitos), `14.928` (5 dígitos), `20.000` (5 dígitos) y `id_cuenta` en minúscula | Usar `INTEGER` (`INT4` en PostgreSQL, soporta hasta 2.147M) y unificar nombre a `id_cuenta`. |
| **5** | Relación `Venta` → `Cuenta_por_cobrar` | Símbolo de rombo (agregación) en el extremo hijo | Relación `1` a `0..1` (`id_factura` es `UNIQUE` en `cuenta_por_cobrar`) | Cambiar conector en Lucidchart a cardinalidad `1` (Venta) hacia `0..1` opcional (Cuenta_por_cobrar). |
| **6** | `Gastos_insumo` (`Fecha`, `Monto`) | `Fecha`, `Monto` con mayúscula inicial | CSV exportado como `Fecha,Monto` | Estandarizar columnas SQL a minúsculas (`fecha`, `monto`) en PostgreSQL/SQLite. |

### 4.1 Brechas funcionales respecto a `Tareas.csv` y el Backend Django
1. **Tabla `categoria` (Tarea 12):** En Etapa 3 se optó por mantener `categoria` como columna dentro de `producto` (13 categorías; `518` productos en `"Otros / sin clasificar"` = `0,6%` del ingreso), sin tabla `categoria` aparte. Dado que `gastos_insumo` se vincula a `producto` por `id_producto`, en Etapa 5 las categorías de gasto se pueden analizar tanto a nivel global (*Insumos / Reposición*) como por la categoría del producto asociado.
2. **Campos faltantes en `cuenta_por_cobrar` (Tareas 16, 19, 24, 25, 26):** Etapa 3 dejó fuera `estado` y `fecha_pago` como MVP. **Esto se resuelve en la Etapa 4 (Tarea 19)** antes de subir la BD a la nube, agregando `estado` (`PAGADA | PENDIENTE | VENCIDA`) y `fecha_pago` (`DATE NULL`) para calcular flujo de caja real, días de atraso y morosidad en Etapa 5.
3. **Alineación con Django (`finanzas/models.py`):** El backend actual del repositorio usa un esquema simplificado multi-usuario (`Categoria`, `Movimiento`, `CuentaPorCobrar`), distinto al modelo analítico de 6 tablas de `datos/`. Esta integración pertenece a la **Etapa 7 (Coordinación con Python y UX)**.

---

## 5. Modelo Entidad-Relación Definitivo (Corregido para Etapa 4 y 5)

```mermaid
erDiagram
    CLIENTE {
        INTEGER id_cliente PK
        VARCHAR(100) nombre
        VARCHAR(100) contacto
    }
    PRODUCTO {
        VARCHAR(10) id_producto PK
        VARCHAR(100) categoria
        VARCHAR(150) producto
        VARCHAR(100) unidad_negocio
    }
    VENTA {
        VARCHAR(30) id_factura PK
        INTEGER id_cliente FK
        DATE fecha
        VARCHAR(20) tipo_compra
        BOOLEAN por_cobrar
    }
    DETALLE_VENTA {
        INTEGER id_detalle PK
        VARCHAR(30) id_factura FK
        VARCHAR(10) id_producto FK
        INTEGER cantidad
        INTEGER precio_venta
        INTEGER costo_venta
    }
    CUENTA_POR_COBRAR {
        INTEGER id_cuenta PK
        VARCHAR(30) id_factura FK_UNIQUE
        INTEGER id_cliente FK
        INTEGER monto
        DATE fecha_vencimiento
        VARCHAR(15) estado
        DATE fecha_pago
    }
    GASTOS_INSUMO {
        INTEGER id_gasto PK
        VARCHAR(10) id_producto FK
        DATE fecha
        INTEGER monto
    }

    CLIENTE ||--o{ VENTA : "realiza"
    CLIENTE ||--o{ CUENTA_POR_COBRAR : "adeuda"
    VENTA ||--|{ DETALLE_VENTA : "contiene"
    VENTA ||--o| CUENTA_POR_COBRAR : "genera (si por_cobrar)"
    PRODUCTO ||--o{ DETALLE_VENTA : "se vende en"
    PRODUCTO ||--o{ GASTOS_INSUMO : "origina gasto"
```
