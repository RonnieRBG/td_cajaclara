# Guía de Visualizaciones del Dashboard — Caja Clara (`Power BI`)

Esta guía describe todas las páginas, filtros, tarjetas KPI, gráficos y tablas del reporte [CajaClara.pbip](CajaClara.pbip), pensado para que cualquier integrante del equipo o usuario de negocio pueda interpretarlo rápidamente.

> **Cómo usar este dashboard:**  
> - **Abrir:** abre [CajaClara.pbip](CajaClara.pbip) en Power BI Desktop *(al compartir esta carpeta por Google Drive, asegúrate de mantener juntas las subcarpetas `CajaClara.Report/` y `CajaClara.SemanticModel/`)*.  
> - **Actualizar datos:** haz clic en **Inicio → Actualizar** (requiere acceso de solo lectura `cajaclara_lectura_bi` a la base Neon PostgreSQL).  
> - **Moneda y período:** todos los montos están expresados en **pesos chilenos (`$`)**. El histórico completo de ventas y gastos cubre **`2010–2020`**; los años **`2021–2022`** contienen únicamente una muestra parcial de ventas frente a gastos completos (por eso existe el filtro **`Período de datos`**).

---

## Resumen de Páginas

| Página | Propósito principal | Fuente principal | Visuales |
| :--- | :--- | :--- | :---: |
| **1. Resumen y Sustentabilidad** | Rentabilidad global, margen por categoría y cobertura de gastos | Modelo tabular (`_Medidas`, `Calendario`, `producto`, `venta`) + `vw_sustentabilidad_negocio` | 12 |
| **2. Flujo de Caja** | Vista unificada anual, mensual y estacional del flujo de caja real vs. facturación | Modelo tabular (`Calendario`, `_Medidas`, `Selector Grafico`) | 14 |
| **3. Ranking de Productos** | Identificar productos *Estrella*, *Nicho rentable*, *Baja venta* y candidatos a reajuste | Vista SQL `vw_ranking_productos` | 7 |
| **4. Cobranza y Alertas** | Controlar morosidad, deuda por cliente y facturas vencidas / próximas a vencer | `_Medidas`, `cuenta_por_cobrar`, `cliente`, `vw_indicador_morosidad`, `vw_cuentas_por_cobrar_cliente` | 13 |

---

## Página 1 — `1. Resumen y Sustentabilidad`

Responde: **¿Es rentable el negocio, qué categorías aportan más margen y cuánto capital queda inmovilizado en fiados?**

### Encabezado y Segmentadores
1. **Título (`Caja Clara — Resumen Ejecutivo y Sustentabilidad`)**: contextualiza las métricas (`ventas facturadas, margen bruto, gastos de insumo y exposición al fiado`).
2. **Segmentador `Período de datos`** (`Calendario[Cobertura]`):
   - **Preseleccionado por defecto en `2010–2020 (Datos completos)`** para evitar que la muestra parcial de `2021–2022` distorsione el margen o la utilidad neta.
   - Permite cambiar a `2021–2022 (Muestra parcial)` o seleccionar ambos para inspeccionar el total histórico.
3. **Segmentador `Tipo de compra`** (`venta[tipo_compra]`): filtra entre ventas al contado (`Contado`) o fiadas/crédito (`Fiado` / según valor en BD).

### Tarjetas KPI (Fila superior)
4. **`Ventas Facturadas`**: suma total vendida (`cantidad × precio_venta`) bajo los filtros seleccionados.
5. **`Margen Bruto`**: ganancia directa sobre ventas (`Ventas Facturadas − Costo Ventas`).
6. **`Margen %`**: porcentaje de rentabilidad bruta sobre las ventas (`Margen Bruto / Ventas Facturadas`).
7. **`Gastos Insumo`**: egresos operativos de reposición e insumos (`SUM(gastos_insumo[monto])` filtrados por fecha mediante relación activa temporal `USERELATIONSHIP`).
8. **`Utilidad Neta Operativa`**: resultado operativo real después de gastos (`Margen Bruto − Gastos Insumo`).
9. **`Ratio Cobertura Gastos`**: cuántas veces el margen bruto cubre los gastos de insumos (`Margen Bruto / Gastos Insumo`). Valores mayores a `1,00` indican operación superavitaria.

### Gráficos y Tablas
10. **Barras horizontales — `Ventas Facturadas y Margen Bruto por Categoría`**:
    - Eje Y: `producto[categoria]` | Barras: `Ventas Facturadas` y `Margen Bruto`, ordenadas de mayor a menor venta.
    - *Cómo leerlo:* permite detectar categorías de alto volumen vs. categorías de mayor utilidad real (por ejemplo, comparar `Abarrotes` en facturación frente a `Belleza y maquillaje` en margen). Al hacer clic en una barra, filtra las tarjetas KPI.
11. **Gráfico combinado — `Sustentabilidad Anual (2010–2020): Margen y Fiado vs. Gastos Insumo`**:
    - Eje X: `Calendario[Año]` | Columnas (eje izquierdo): `Margen Bruto` y `Total Fiado Emitido` | Línea (eje secundario): `Gastos Insumo`.
    - **Filtro propio del visual:** siempre muestra `2010–2020 (Datos completos)` para mantener la comparabilidad anual limpia.
    - *Cómo leerlo:* muestra si el margen supera cómodamente los gastos fijos cada año y qué proporción de ese margen quedó otorgada como venta fiada.
12. **Tabla — `Indicadores Anuales de Sustentabilidad (vw_sustentabilidad_negocio)`**:
    - Columnas: `año`, `Datos del año` (etiqueta `completa` o `parcial` de la vista SQL), `ventas`, `margen_bruto`, `gastos_insumo`, `utilidad_neta_operativa`, `ratio_margen_sobre_gastos` y `fiado_sobre_margen_pct`, ordenada del año más reciente al más antiguo (`2022` → `2010`).
    - *Nota:* al provenir de una vista agregada anual independiente de `Calendario`, muestra de forma transparente todos los años (`2010–2022`) para comparar los completos frente al recorte de `2021–2022`.

---

## Página 2 — `2. Flujo de Caja`

Responde: **¿Cuánto dinero entró realmente a caja por año y por mes (contado + cobros de fiados según su `fecha_pago`) vs. lo que salió en insumos, y cuál es el patrón estacional?**

### Encabezado y Segmentadores (Listas Desplegables)
1. **Título (`Caja Clara — Flujo de Caja`)**: resume la vista anual, mensual y estacional (`Ene–Dic`) de los ingresos efectivamente cobrados frente a los gastos de insumos.
2. **Segmentador `Mostrar gráfico`** (`'Selector Grafico'[Vista]`): lista desplegable con selección múltiple directa (sin necesidad de `Ctrl`) y opción nativa `Seleccionar todo` que redimensiona automáticamente los paneles en pantalla (`1 gráfico = 100% pantalla completa`, `2 gráficos = 50% mitad izquierda y 50% mitad derecha`, `3 gráficos o sin selección = 2 arriba y 1 abajo a ancho completo`).
3. **Segmentador `Año`** (`Calendario[Año]`): filtra uno o varios años específicos. Al seleccionar un único año, los gráficos anuales hacen *auto-drilldown* automático a los 12 meses (`Ene–Dic`) de ese año para nunca quedarse con una sola barra ni duplicar el promedio histórico.
4. **Segmentador `Período de datos`** (`Calendario[Cobertura]`): preseleccionado en `2010–2020 (Datos completos)` para evitar que la muestra parcial `2021–2022` distorsione los promedios.
5. **Segmentador `Mes`** (`Calendario[Mes]`): ordenado cronológicamente de enero a diciembre (`Mes Num`).

### Tarjetas KPI (Fila superior)
6. **`Ingresos Efectivamente Cobrados`**: suma real de caja percibida (`Ingresos Contado + Cobros Fiado Recibidos`).
7. **`Ingresos Contado`**: ventas emitidas sin crédito (`venta[por_cobrar] = FALSE`).
8. **`Cobros Fiado Recibidos`**: cuotas/facturas pagadas (`cuenta_por_cobrar[estado] = "PAGADA"`) asignadas al mes en que se pagaron (`USERELATIONSHIP` sobre `fecha_pago`).
9. **`Gastos Insumo`**: egresos del período seleccionado.
10. **`Flujo de Caja Neto`**: saldo líquido real del período (`Ingresos Efectivamente Cobrados − Gastos Insumo`).

### Gráficos Inteligentes (Adaptativos al Filtro y Redimensionables)
11. **`Flujo de Caja Neto (Anual / Mensual)`**:
    - Con múltiples años seleccionados muestra la evolución anual (`2010–2020`); al filtrar un año específico (ej. `2018`), desglosa automáticamente los 12 meses (`ene–dic`) de ese año (`Flujo de Caja Neto Mensual — Año 2018`).
12. **`Flujo Promedio Histórico (Ene–Dic)`**:
    - Muestra siempre la curva estacional histórica de los años completos (`2010–2020`, de `ene` a `dic`), sirviendo como *benchmark* estructural frente al año o mes filtrado sin duplicar jamás al Gráfico 1.
13. **`Ventas: Contado vs. Fiado (Anual / Mensual)`**:
    - Con múltiples años seleccionados compara `Ventas Contado` vs. `Total Fiado Emitido` por año; al filtrar un año específico, desglosa automáticamente las barras apiladas en los 12 meses (`ene–dic`) de ese año.

---

## Página 3 — `3. Ranking de Productos`

Responde: **¿Qué productos impulsan la ganancia (*Estrella*), cuáles conviene revisar en precio o catálogo (*Baja venta* / *Alto volumen / Bajo margen*)?**  
*(Basada en `vw_ranking_productos` para el período completo `2010–2020`.)*

### Encabezado y Segmentadores
1. **Título (`Caja Clara — Ranking y Matriz de Productos`)**: resume la segmentación por cuadrantes sobre la mediana de ventas y mediana de margen (`Datos completos 2010–2020`).
2. **Segmentador `Categoría`** (`vw_ranking_productos[categoria]`): filtra un rubro específico (ej. `Abarrotes`, `Belleza y maquillaje`).
3. **Segmentador `Clasificación`** (`vw_ranking_productos[clasificacion_desempeno]`): selecciona uno de los 4 cuadrantes (*Estrella*, *Alto volumen / Bajo margen*, *Nicho rentable*, *Baja venta*).
4. **Segmentador `Alerta escala`** (`vw_ranking_productos[alerta_escala_etapa2]`): permite aislar los `13` SKU con artefacto de escala histórico de Etapa 2 (`TRUE`) frente al catálogo limpio (`FALSE`).

### Gráficos y Tablas
5. **Gráfico de dispersión — `Matriz Ventas vs. Margen por Producto (excluye alertas de escala)`**:
    - Eje X: `ventas` | Eje Y: `margen` | Color (`Series`): `clasificacion_desempeno` | Tamaño de burbuja: `unidades_vendidas`.
    - **Filtro propio del visual:** excluye `alerta_escala_etapa2 = TRUE` para que saltos puntuales de escala no distorsionen el gráfico.
    - *Cómo leerlo:* arriba a la derecha se concentran los productos **Estrella** (alta venta y alto margen); arriba a la izquierda los **Nicho rentable**; abajo a la derecha los **Alto volumen / Bajo margen** (candidatos a ajuste de precio/costo).
6. **Tabla resumen — `Resumen de Cuadrantes de Desempeño`**:
    - Columnas: `clasificacion_desempeno`, `unidades_vendidas`, `ventas` y `margen`, ordenada de mayor a menor margen total.
    - *Cómo leerlo:* cuantifica cuánto volumen y ganancia concentra cada cuadrante; al seleccionar una fila filtra la dispersión y la tabla de detalle.
7. **Tabla detalle — `Ranking Detallado de Productos (Estrellas y Reajuste)`**:
    - Columnas: `rank_ventas`, `producto`, `categoria`, `clasificacion_desempeno`, `unidades_vendidas`, `ventas`, `margen`, `margen_pct` y `alerta_escala_etapa2`, ordenada por `rank_ventas` ascendente (`1, 2, 3...`).
    - *Cómo leerlo:* sirve como lista operativa de consulta exacta por SKU y permite combinarla con el segmentador de `Clasificación` para revisar el Top 10 Estrella o productos a depurar.

---

## Página 4 — `4. Cobranza y Alertas`

Responde: **¿Cuánta plata está en la calle, qué porcentaje está vencido y a qué clientes hay que cobrar primero?**  
*(Evaluada al corte operativo del dataset: `2022-09-01`.)*

### Encabezado y Tarjetas KPI
1. **Título (`Caja Clara — Cobranza, Morosidad y Alertas Operativas`)**.
2. **`Morosidad Activa %`**: porcentaje de la deuda abierta que ya superó su fecha de vencimiento (`Cartera Vencida Actual / Cartera Abierta Actual`).
3. **`Cartera Abierta Actual`**: monto total pendiente de pago (`estado IN {"PENDIENTE", "VENCIDA"}`).
4. **`Cartera Vencida Actual`**: monto total ya vencido (`estado = "VENCIDA"`).
5. **`Cartera Por Vencer`**: monto aún dentro de plazo (`estado = "PENDIENTE"`).
6. **`Cuentas Abiertas`**: número total de facturas por cobrar (`PENDIENTE` + `VENCIDA`).
7. **`Cuentas Vencidas`**: número de facturas vencidas que requieren gestión urgente.

### Gráficos y Tablas Operativas
8. **Tabla — `Escenarios de Morosidad (vw_indicador_morosidad)`**:
    - Muestra los 3 escenarios históricos de evaluación (`Corte Final Dataset (2022-09-01)`, `Cierre Cobertura Completa (2020-12-31)` e `Histórico Pagos con Atraso (2010–2022)`) con `cuentas_por_cobrar_abiertas`, `cuentas_vencidas`, `monto_por_cobrar`, `monto_vencido`, `morosidad_monto_pct` y `morosidad_cuentas_pct`.
    - *Cómo leerlo:* permite contextualizar la foto actual del corte frente al comportamiento histórico normal del negocio.
9. **Barras horizontales — `Deuda Abierta vs. Vencida por Cliente`**:
    - Eje Y: `vw_cuentas_por_cobrar_cliente[nombre]` | Barras: `monto_adeudado_actual` vs. `monto_vencido_actual`, ordenada de mayor a menor deuda abierta.
    - **Filtro propio del visual:** `cuentas_abiertas > 0` (muestra solo deudores activos).
    - *Cómo leerlo:* identifica de un vistazo quién concentra mayor riesgo monetario. Al hacer clic en un cliente, filtra las tarjetas y tablas inferiores.
10. **Tabla — `Facturas en Alerta de Cobro (Vencidas y Pendientes)`**:
    - Columnas: `id_factura`, `cliente[nombre]`, `cliente[contacto]`, `fecha_vencimiento`, `estado` y `monto`, ordenada ascendente por `fecha_vencimiento` (las más antiguas primero).
    - **Filtro propio del visual:** `estado IN {'VENCIDA', 'PENDIENTE'}`.
    - *Cómo leerlo:* es la lista directa de cobranza factura por factura con el teléfono del cliente listo para llamar o escribir.
11. **Tabla — `Prioridad de Cobranza por Cliente (cuentas abiertas > 0)`**:
    - Columnas: `id_cliente`, `nombre`, `contacto`, `cuentas_abiertas`, `cuentas_vencidas`, `monto_adeudado_actual`, `monto_vencido_actual`, `proxima_fecha_cobro` y `max_dias_atraso_actual`, ordenada de mayor a menor `max_dias_atraso_actual`.
    - **Filtro propio del visual:** `cuentas_abiertas > 0`.
    - *Cómo leerlo:* ordena automáticamente a los clientes con deuda activa desde el atraso más crítico hasta los vencimientos próximos.

---

## Resumen de Medidas DAX (`_Medidas`)

Además de los KPIs visibles en las tarjetas, la tabla [_Medidas.tmdl](CajaClara.SemanticModel/definition/tables/_Medidas.tmdl) incluye 23 medidas reutilizables (todas formateadas sin sufijo `CLP`, en `$#,##0`, `#,##0`, `0.0%` o `0.00`), entre ellas `Costo Ventas`, `Unidades Vendidas`, `Facturas Emitidas`, `Cuentas Por Vencer`, `Clientes Con Deuda` y `Ratio Fiado sobre Margen %`, disponibles para futuras vistas o análisis exploratorios.
