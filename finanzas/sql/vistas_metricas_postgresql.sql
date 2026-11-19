-- ============================================================================
-- Caja Clara — Vistas Analíticas Reutilizables (PostgreSQL)
-- Etapa 5: Análisis y Métricas (Tareas 22 a 28) — Base directa para Etapa 6
-- Fecha de corte del dataset de cobros: 2022-09-01
-- Corte de cobertura completa histórica: 2020-12-31
-- ============================================================================

-- Se eliminan antes de recrear porque PostgreSQL no permite cambiar nombres
-- de columnas existentes mediante CREATE OR REPLACE VIEW.
DROP VIEW IF EXISTS vw_sustentabilidad_negocio CASCADE;
DROP VIEW IF EXISTS vw_ranking_productos CASCADE;
DROP VIEW IF EXISTS vw_indicador_morosidad CASCADE;
DROP VIEW IF EXISTS vw_cuentas_por_cobrar_cliente CASCADE;
DROP VIEW IF EXISTS vw_flujo_caja_mensual CASCADE;
DROP VIEW IF EXISTS vw_ventas_categoria_mes CASCADE;
DROP VIEW IF EXISTS vw_margen_producto_categoria CASCADE;

-- Tarea 22: Margen por producto, categoría y período (año-mes)
CREATE OR REPLACE VIEW vw_margen_producto_categoria AS
SELECT
    EXTRACT(YEAR FROM v.fecha)::INT AS anio,
    EXTRACT(MONTH FROM v.fecha)::INT AS mes,
    TO_CHAR(v.fecha, 'YYYY-MM') AS periodo,
    CASE WHEN v.fecha <= DATE '2020-12-31' THEN 'completa' ELSE 'parcial' END AS cobertura,
    p.id_producto,
    p.producto,
    p.categoria,
    COUNT(DISTINCT dv.id_factura) AS num_facturas,
    SUM(dv.cantidad) AS unidades,
    SUM(dv.cantidad::BIGINT * dv.precio_venta) AS ventas,
    SUM(dv.cantidad::BIGINT * dv.costo_venta) AS costo,
    SUM((dv.precio_venta - dv.costo_venta)::BIGINT * dv.cantidad) AS margen,
    ROUND(
        SUM((dv.precio_venta - dv.costo_venta)::BIGINT * dv.cantidad)::NUMERIC
        / NULLIF(SUM(dv.cantidad::BIGINT * dv.precio_venta), 0) * 100,
        2
    ) AS margen_pct
FROM detalle_venta dv
JOIN venta v ON v.id_factura = dv.id_factura
JOIN producto p ON p.id_producto = dv.id_producto
GROUP BY 1, 2, 3, 4, p.id_producto, p.producto, p.categoria;


-- Tarea 23: Ventas por categoría y mes
CREATE OR REPLACE VIEW vw_ventas_categoria_mes AS
SELECT
    EXTRACT(YEAR FROM v.fecha)::INT AS anio,
    EXTRACT(MONTH FROM v.fecha)::INT AS mes,
    TO_CHAR(v.fecha, 'YYYY-MM') AS periodo,
    CASE WHEN v.fecha <= DATE '2020-12-31' THEN 'completa' ELSE 'parcial' END AS cobertura,
    p.categoria,
    COUNT(DISTINCT v.id_factura) AS facturas,
    SUM(dv.cantidad) AS unidades,
    SUM(dv.cantidad::BIGINT * dv.precio_venta) AS ventas,
    SUM((dv.precio_venta - dv.costo_venta)::BIGINT * dv.cantidad) AS margen
FROM detalle_venta dv
JOIN venta v ON v.id_factura = dv.id_factura
JOIN producto p ON p.id_producto = dv.id_producto
GROUP BY 1, 2, 3, 4, p.categoria;


-- Tarea 24: Flujo de caja mensual (distingue lo vendido/facturado de lo efectivamente cobrado menos gastos)
CREATE OR REPLACE VIEW vw_flujo_caja_mensual AS
WITH facturado_mes AS (
    SELECT
        TO_CHAR(v.fecha, 'YYYY-MM') AS periodo,
        CASE WHEN MAX(v.fecha) <= DATE '2020-12-31' THEN 'completa' ELSE 'parcial' END AS cobertura,
        SUM(dv.cantidad::BIGINT * dv.precio_venta) AS ventas_facturadas,
        SUM(CASE WHEN v.por_cobrar = FALSE THEN dv.cantidad::BIGINT * dv.precio_venta ELSE 0 END) AS ingresos_contado,
        SUM(CASE WHEN v.por_cobrar = TRUE THEN dv.cantidad::BIGINT * dv.precio_venta ELSE 0 END) AS ventas_fiadas
    FROM venta v
    JOIN detalle_venta dv ON dv.id_factura = v.id_factura
    GROUP BY 1
),
cobros_mes AS (
    SELECT
        TO_CHAR(fecha_pago, 'YYYY-MM') AS periodo,
        SUM(monto)::BIGINT AS cobros_fiado_recibidos,
        COUNT(*) AS cuentas_cobradas
    FROM cuenta_por_cobrar
    WHERE estado = 'PAGADA' AND fecha_pago IS NOT NULL
    GROUP BY 1
),
gastos_mes AS (
    SELECT
        TO_CHAR(fecha, 'YYYY-MM') AS periodo,
        SUM(monto)::BIGINT AS gastos_insumo,
        COUNT(*) AS num_gastos
    FROM gastos_insumo
    GROUP BY 1
),
periodos AS (
    SELECT periodo FROM facturado_mes
    UNION
    SELECT periodo FROM cobros_mes
    UNION
    SELECT periodo FROM gastos_mes
)
SELECT
    p.periodo,
    LEFT(p.periodo, 4)::INT AS anio,
    RIGHT(p.periodo, 2)::INT AS mes,
    CASE WHEN p.periodo <= '2020-12' THEN 'completa' ELSE 'parcial' END AS cobertura,
    COALESCE(f.ventas_facturadas, 0) AS ventas_facturadas,
    COALESCE(f.ingresos_contado, 0) AS ingresos_contado,
    COALESCE(f.ventas_fiadas, 0) AS ventas_fiadas,
    COALESCE(c.cobros_fiado_recibidos, 0) AS cobros_fiado_recibidos,
    COALESCE(f.ingresos_contado, 0) + COALESCE(c.cobros_fiado_recibidos, 0) AS ingresos_efectivamente_cobrados,
    COALESCE(g.gastos_insumo, 0) AS gastos_insumo,
    (COALESCE(f.ingresos_contado, 0) + COALESCE(c.cobros_fiado_recibidos, 0))
        - COALESCE(g.gastos_insumo, 0) AS flujo_caja_neto
FROM periodos p
LEFT JOIN facturado_mes f ON f.periodo = p.periodo
LEFT JOIN cobros_mes c ON c.periodo = p.periodo
LEFT JOIN gastos_mes g ON g.periodo = p.periodo
ORDER BY p.periodo;


-- Tarea 25: Cuentas por cobrar por cliente (cartera abierta al corte 2022-09-01 y resumen histórico)
CREATE OR REPLACE VIEW vw_cuentas_por_cobrar_cliente AS
SELECT
    c.id_cliente,
    c.nombre,
    c.contacto,
    COUNT(cxc.id_cuenta) AS total_cuentas_fiadas,
    SUM(cxc.monto)::BIGINT AS monto_total_fiado,
    SUM(CASE WHEN cxc.estado = 'PAGADA' THEN cxc.monto ELSE 0 END)::BIGINT AS monto_pagado,
    SUM(CASE WHEN cxc.estado IN ('PENDIENTE', 'VENCIDA') THEN cxc.monto ELSE 0 END)::BIGINT AS monto_adeudado_actual,
    SUM(CASE WHEN cxc.estado = 'VENCIDA' THEN cxc.monto ELSE 0 END)::BIGINT AS monto_vencido_actual,
    COUNT(*) FILTER (WHERE cxc.estado IN ('PENDIENTE', 'VENCIDA')) AS cuentas_abiertas,
    COUNT(*) FILTER (WHERE cxc.estado = 'VENCIDA') AS cuentas_vencidas,
    MIN(cxc.fecha_vencimiento) FILTER (WHERE cxc.estado IN ('PENDIENTE', 'VENCIDA')) AS proxima_fecha_cobro,
    MAX(
        CASE
            WHEN cxc.estado = 'VENCIDA' THEN (DATE '2022-09-01' - cxc.fecha_vencimiento)
            ELSE 0
        END
    ) AS max_dias_atraso_actual,
    ROUND(
        AVG(
            CASE
                WHEN cxc.estado = 'PAGADA' AND cxc.fecha_pago > cxc.fecha_vencimiento
                    THEN (cxc.fecha_pago - cxc.fecha_vencimiento)
                WHEN cxc.estado = 'PAGADA' THEN 0
            END
        ),
        1
    ) AS promedio_dias_atraso_historico
FROM cliente c
LEFT JOIN cuenta_por_cobrar cxc ON cxc.id_cliente = c.id_cliente
GROUP BY c.id_cliente, c.nombre, c.contacto;


-- Tarea 26: Indicador de morosidad (corte activo 2022-09-01, snapshot cobertura completa 2020-12-31 y tasa histórica)
CREATE OR REPLACE VIEW vw_indicador_morosidad AS
SELECT
    'Corte Final Dataset (2022-09-01)' AS escenario,
    COUNT(*) FILTER (WHERE estado IN ('PENDIENTE', 'VENCIDA')) AS cuentas_por_cobrar_abiertas,
    COUNT(*) FILTER (WHERE estado = 'VENCIDA') AS cuentas_vencidas,
    COALESCE(SUM(monto) FILTER (WHERE estado IN ('PENDIENTE', 'VENCIDA')), 0)::BIGINT AS monto_por_cobrar,
    COALESCE(SUM(monto) FILTER (WHERE estado = 'VENCIDA'), 0)::BIGINT AS monto_vencido,
    ROUND(
        COALESCE(SUM(monto) FILTER (WHERE estado = 'VENCIDA'), 0)::NUMERIC
        / NULLIF(SUM(monto) FILTER (WHERE estado IN ('PENDIENTE', 'VENCIDA')), 0) * 100,
        2
    ) AS morosidad_monto_pct,
    ROUND(
        COUNT(*) FILTER (WHERE estado = 'VENCIDA')::NUMERIC
        / NULLIF(COUNT(*) FILTER (WHERE estado IN ('PENDIENTE', 'VENCIDA')), 0) * 100,
        2
    ) AS morosidad_cuentas_pct
FROM cuenta_por_cobrar
UNION ALL
SELECT
    'Cierre Cobertura Completa (2020-12-31)' AS escenario,
    COUNT(*) FILTER (WHERE v.fecha <= DATE '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > DATE '2020-12-31')) AS cuentas_por_cobrar_abiertas,
    COUNT(*) FILTER (WHERE v.fecha <= DATE '2020-12-31' AND c.fecha_vencimiento <= DATE '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > DATE '2020-12-31')) AS cuentas_vencidas,
    COALESCE(SUM(c.monto) FILTER (WHERE v.fecha <= DATE '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > DATE '2020-12-31')), 0)::BIGINT AS monto_por_cobrar,
    COALESCE(SUM(c.monto) FILTER (WHERE v.fecha <= DATE '2020-12-31' AND c.fecha_vencimiento <= DATE '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > DATE '2020-12-31')), 0)::BIGINT AS monto_vencido,
    ROUND(
        COALESCE(SUM(c.monto) FILTER (WHERE v.fecha <= DATE '2020-12-31' AND c.fecha_vencimiento <= DATE '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > DATE '2020-12-31')), 0)::NUMERIC
        / NULLIF(SUM(c.monto) FILTER (WHERE v.fecha <= DATE '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > DATE '2020-12-31')), 0) * 100,
        2
    ) AS morosidad_monto_pct,
    ROUND(
        COUNT(*) FILTER (WHERE v.fecha <= DATE '2020-12-31' AND c.fecha_vencimiento <= DATE '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > DATE '2020-12-31'))::NUMERIC
        / NULLIF(COUNT(*) FILTER (WHERE v.fecha <= DATE '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > DATE '2020-12-31')), 0) * 100,
        2
    ) AS morosidad_cuentas_pct
FROM cuenta_por_cobrar c
JOIN venta v ON v.id_factura = c.id_factura
UNION ALL
SELECT
    'Histórico Pagos con Atraso (2010-2022)' AS escenario,
    COUNT(*) AS cuentas_por_cobrar_abiertas,
    COUNT(*) FILTER (WHERE estado = 'VENCIDA' OR (estado = 'PAGADA' AND fecha_pago > fecha_vencimiento)) AS cuentas_vencidas,
    SUM(monto)::BIGINT AS monto_por_cobrar,
    COALESCE(SUM(monto) FILTER (WHERE estado = 'VENCIDA' OR (estado = 'PAGADA' AND fecha_pago > fecha_vencimiento)), 0)::BIGINT AS monto_vencido,
    ROUND(
        COALESCE(SUM(monto) FILTER (WHERE estado = 'VENCIDA' OR (estado = 'PAGADA' AND fecha_pago > fecha_vencimiento)), 0)::NUMERIC
        / NULLIF(SUM(monto), 0) * 100,
        2
    ) AS morosidad_monto_pct,
    ROUND(
        COUNT(*) FILTER (WHERE estado = 'VENCIDA' OR (estado = 'PAGADA' AND fecha_pago > fecha_vencimiento))::NUMERIC
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS morosidad_cuentas_pct
FROM cuenta_por_cobrar;


-- Tarea 27: Ranking de productos estrella y de baja venta (cobertura completa 2010-2020)
CREATE OR REPLACE VIEW vw_ranking_productos AS
WITH base AS (
    SELECT
        p.id_producto,
        p.producto,
        p.categoria,
        COUNT(DISTINCT dv.id_factura) AS num_facturas,
        SUM(dv.cantidad) AS unidades_vendidas,
        SUM(dv.cantidad::BIGINT * dv.precio_venta) AS ventas,
        SUM(dv.cantidad::BIGINT * dv.costo_venta) AS costo,
        SUM((dv.precio_venta - dv.costo_venta)::BIGINT * dv.cantidad) AS margen,
        ROUND(
            SUM((dv.precio_venta - dv.costo_venta)::BIGINT * dv.cantidad)::NUMERIC
            / NULLIF(SUM(dv.cantidad::BIGINT * dv.precio_venta), 0) * 100,
            2
        ) AS margen_pct,
        CASE
            WHEN MAX(dv.precio_venta)::NUMERIC / NULLIF(MIN(dv.precio_venta), 0) > 5 THEN TRUE
            ELSE FALSE
        END AS alerta_escala_etapa2
    FROM detalle_venta dv
    JOIN venta v ON v.id_factura = dv.id_factura
    JOIN producto p ON p.id_producto = dv.id_producto
    WHERE v.fecha <= DATE '2020-12-31'
    GROUP BY p.id_producto, p.producto, p.categoria
),
medianas AS (
    SELECT
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ventas) AS med_ventas,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY margen) AS med_margen
    FROM base
)
SELECT
    b.*,
    RANK() OVER (ORDER BY b.ventas DESC) AS rank_ventas,
    RANK() OVER (ORDER BY b.margen DESC) AS rank_margen,
    CASE
        WHEN b.ventas >= m.med_ventas AND b.margen >= m.med_margen THEN 'Estrella'
        WHEN b.ventas >= m.med_ventas AND b.margen < m.med_margen THEN 'Alto volumen / Bajo margen'
        WHEN b.ventas < m.med_ventas AND b.margen >= m.med_margen THEN 'Nicho rentable'
        ELSE 'Baja venta'
    END AS clasificacion_desempeno
FROM base b
CROSS JOIN medianas m;


-- Tarea 28: Evaluación anual de sustentabilidad del negocio (margen vs gastos vs fiado)
CREATE OR REPLACE VIEW vw_sustentabilidad_negocio AS
WITH ventas_anio AS (
    SELECT
        EXTRACT(YEAR FROM v.fecha)::INT AS anio,
        CASE WHEN EXTRACT(YEAR FROM v.fecha)::INT <= 2020 THEN 'completa' ELSE 'parcial' END AS cobertura,
        SUM(dv.cantidad::BIGINT * dv.precio_venta) AS ventas,
        SUM(dv.cantidad::BIGINT * dv.costo_venta) AS costo,
        SUM((dv.precio_venta - dv.costo_venta)::BIGINT * dv.cantidad) AS margen_bruto,
        SUM(CASE WHEN v.por_cobrar THEN dv.cantidad::BIGINT * dv.precio_venta ELSE 0 END) AS monto_fiado
    FROM detalle_venta dv
    JOIN venta v ON v.id_factura = dv.id_factura
    GROUP BY 1, 2
),
gastos_anio AS (
    SELECT
        EXTRACT(YEAR FROM fecha)::INT AS anio,
        SUM(monto)::BIGINT AS gastos_insumo
    FROM gastos_insumo
    GROUP BY 1
)
SELECT
    va.anio,
    va.cobertura,
    va.ventas,
    va.costo,
    va.margen_bruto,
    COALESCE(ga.gastos_insumo, 0) AS gastos_insumo,
    va.margen_bruto - COALESCE(ga.gastos_insumo, 0) AS utilidad_neta_operativa,
    va.monto_fiado,
    ROUND(va.margen_bruto::NUMERIC / NULLIF(ga.gastos_insumo, 0), 2) AS ratio_margen_sobre_gastos,
    ROUND(va.monto_fiado::NUMERIC / NULLIF(va.ventas, 0) * 100, 2) AS pct_ventas_fiadas,
    ROUND(va.monto_fiado::NUMERIC / NULLIF(va.margen_bruto, 0) * 100, 2) AS fiado_sobre_margen_pct
FROM ventas_anio va
LEFT JOIN gastos_anio ga ON ga.anio = va.anio
ORDER BY va.anio;

GRANT SELECT ON
    vw_margen_producto_categoria,
    vw_ventas_categoria_mes,
    vw_flujo_caja_mensual,
    vw_cuentas_por_cobrar_cliente,
    vw_indicador_morosidad,
    vw_ranking_productos,
    vw_sustentabilidad_negocio
TO cajaclara_lectura_bi, cajaclara_app_rw;
