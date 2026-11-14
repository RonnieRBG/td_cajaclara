# Caja Clara — Etapa 6: Alertas y Visualización (Tareas 29, 30 y 31)

Este directorio reúne los artefactos finales de la **Etapa 6** del proyecto, conectando la base relacional en Neon PostgreSQL con el backend Python/Django y el reporte ejecutivo en Power BI (`datos/CajaClara.pbip`).

---

## 1. Tarea 29 — Consulta y Vista SQL de Alertas de Cobro (`vw_alertas_cobro`)

- **Scripts:**
  - PostgreSQL / Neon: [alertas_cobro_postgresql.sql](file:///c:/Users/Asus/Documents/GitHub/td_cajaclara/datos/Etapas_4-5-6/Etapa_6_Alertas_y_Visualizacion/alertas_cobro_postgresql.sql)
  - SQLite 3 (local): [alertas_cobro_sqlite.sql](file:///c:/Users/Asus/Documents/GitHub/td_cajaclara/datos/Etapas_4-5-6/Etapa_6_Alertas_y_Visualizacion/alertas_cobro_sqlite.sql)
  - Validador y función Python reutilizable: [validar_alertas_etapa6.py](file:///c:/Users/Asus/Documents/GitHub/td_cajaclara/datos/Etapas_4-5-6/Etapa_6_Alertas_y_Visualizacion/validar_alertas_etapa6.py)

### Lógica implementada
Sobre las cuentas abiertas (`estado IN ('PENDIENTE', 'VENCIDA')` y `fecha_pago IS NULL`) al corte operativo del dataset (`2022-09-01`):
- `1_CRITICA_VENCIDA`: facturas con vencimiento anterior a la fecha de corte (`6` cuentas, `$7.570`).
- `2_ALTA_PROXIMA_7D`: facturas pendientes que vencen dentro de los próximos `7` días (`1` cuenta, `$3.083`).
- `3_MEDIA_PROXIMA_15D`: facturas pendientes que vencen entre `8` y `15` días (`1` cuenta, `$72`).
- Cada registro expone `dias_para_vencer`, `dias_atraso`, `requiere_notificacion` y `mensaje_sugerido` listo para recordatorios desde Python/Django.
- Para operación en vivo en producción, la **Sección B** de `alertas_cobro_postgresql.sql` y `obtener_alertas_cobro()` en `validar_alertas_etapa6.py` parametrizan la fecha de corte (`CURRENT_DATE`) y la ventana de anticipación (`dias_aviso`).

---

## 2. Tarea 30 — Vistas SQL Analíticas y Permisos en Neon

Las 7 vistas analíticas de Etapa 5 (`vw_margen_producto_categoria`, `vw_ventas_categoria_mes`, `vw_flujo_caja_mensual`, `vw_cuentas_por_cobrar_cliente`, `vw_indicador_morosidad`, `vw_ranking_productos`, `vw_sustentabilidad_negocio`) ya están creadas en Neon e importadas en `CajaClara.pbip`.

Si deseas habilitar también `vw_alertas_cobro` en Neon:
1. Abre **Neon SQL Editor** (conectado como `neondb_owner`).
2. Ejecuta el contenido de `alertas_cobro_postgresql.sql` (incluye `GRANT SELECT ON vw_alertas_cobro TO cajaclara_lectura_bi, cajaclara_app_rw;`).
3. En Power BI Desktop, haz clic en **Inicio -> Actualizar**.

---

## 3. Tarea 31 — Tablero Ejecutivo en Power BI (`datos/CajaClara.pbip`)

El proyecto [CajaClara.pbip](file:///c:/Users/Asus/Documents/GitHub/td_cajaclara/datos/CajaClara.pbip) quedó armado con:
- **Modelo semántico (`CajaClara.SemanticModel`):**
  - Relaciones de fecha configuradas entre `Calendario[Date]` y `venta[fecha]` (activa), `cuenta_por_cobrar[fecha_pago]` (inactiva) y `gastos_insumo[fecha]` (inactiva).
  - Ordenamiento de `Calendario[Mes]` por `Calendario[Mes Num]` y formatos monetarios (`$#,##0`) y porcentuales aplicados en columnas y medidas (sin sufijos `CLP`).
  - **23 medidas DAX en `_Medidas`** (sin sufijo `CLP` en los nombres, siguiendo tu estándar).
- **Reporte de 4 páginas (`CajaClara.Report`, lienzo `1920x1080`):**
  1. **1. Resumen y Sustentabilidad**: 6 tarjetas KPI ejecutivas, barras horizontales de Ventas y Margen por categoría (`producto`), gráfico combinado anual de Margen + Total Fiado vs Gastos Insumo (`Período de datos = "2010–2020 (Datos completos)"`).
  2. **2. Flujo de Caja Mensual**: segmentadores de `Año`, `Período de datos` y `Mes`, 5 tarjetas KPI de caja (`Ingresos Efectivamente Cobrados`, `Ingresos Contado`, `Cobros Fiado Recibidos`, `Gastos Insumo`, `Flujo de Caja Neto`), serie mensual Facturado vs Cobrado y columna mensual de Flujo Neto.
  3. **3. Ranking de Productos**: segmentadores de `categoria`, `clasificacion_desempeno` y `alerta_escala_etapa2`, gráfico de dispersión `ventas` vs `margen` (tamaño por `unidades_vendidas`, filtrando anomalías de escala `alerta_escala_etapa2 = FALSE`), resumen de cuadrantes y tabla de ranking ordenado por `rank_ventas`.
  4. **4. Cobranza, Morosidad y Alertas**: 6 tarjetas KPI de cartera (`Morosidad Activa %`, `Cartera Abierta Actual`, `Cartera Vencida Actual`, `Cartera Por Vencer`, `Cuentas Abiertas`, `Cuentas Vencidas`), tabla de 3 escenarios (`vw_indicador_morosidad`), top clientes deudores (`cuentas_abiertas > 0`) y tabla operativa de alertas/cobranza ordenada por mayor atraso actual.

### Pasos finales de verificación en Power BI Desktop
1. Abre `datos/CajaClara.pbip` (al abrirlo por primera vez después de editar JSON/TMDL, Power BI cargará el modelo actualizado).
2. Haz clic en **Actualizar** si pide credenciales/caché de Neon y revisa que todas las visuales de las 4 páginas muestren datos sin errores.
3. Si deseas actualizar tu respaldo binario `.pbix`, usa **Archivo -> Guardar como -> Caja Clara (.pbix)** (y recuerda mantener los `.pbix` fuera de repositorios públicos si contienen datos del negocio).
