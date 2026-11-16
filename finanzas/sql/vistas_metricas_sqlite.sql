-- ============================================================================
-- Caja Clara — Vistas Analíticas Reutilizables (SQLite 3)
-- Equivalente exacto de vistas_metricas_postgresql.sql para ejecución local
-- ============================================================================

DROP VIEW IF EXISTS vw_margen_producto_categoria;
DROP VIEW IF EXISTS vw_ventas_categoria_mes;
DROP VIEW IF EXISTS vw_flujo_caja_mensual;
DROP VIEW IF EXISTS vw_cuentas_por_cobrar_cliente;
DROP VIEW IF EXISTS vw_indicador_morosidad;
DROP VIEW IF EXISTS vw_ranking_productos;
DROP VIEW IF EXISTS vw_sustentabilidad_negocio;

-- Tarea 22: Margen por producto, categoría y período
CREATE VIEW vw_margen_producto_categoria AS
SELECT
    CAST(strftime('%Y', v.fecha) AS INTEGER) AS anio,
    CAST(strftime('%m', v.fecha) AS INTEGER) AS mes,
    strftime('%Y-%m', v.fecha) AS periodo,
    CASE WHEN v.fecha <= '2020-12-31' THEN 'completa' ELSE 'parcial' END AS cobertura,
    p.id_producto,
    p.producto,
    p.categoria,
    COUNT(DISTINCT dv.id_factura) AS num_facturas,
    SUM(dv.cantidad) AS unidades,
    SUM(dv.cantidad * dv.precio_venta) AS ventas,
    SUM(dv.cantidad * dv.costo_venta) AS costo,
    SUM((dv.precio_venta - dv.costo_venta) * dv.cantidad) AS margen,
    ROUND(
        CAST(SUM((dv.precio_venta - dv.costo_venta) * dv.cantidad) AS REAL)
        / NULLIF(SUM(dv.cantidad * dv.precio_venta), 0) * 100,
        2
    ) AS margen_pct
FROM detalle_venta dv
JOIN venta v ON v.id_factura = dv.id_factura
JOIN producto p ON p.id_producto = dv.id_producto
GROUP BY 1, 2, 3, 4, p.id_producto, p.producto, p.categoria;

-- Tarea 23: Ventas por categoría y mes
CREATE VIEW vw_ventas_categoria_mes AS
SELECT
    CAST(strftime('%Y', v.fecha) AS INTEGER) AS anio,
    CAST(strftime('%m', v.fecha) AS INTEGER) AS mes,
    strftime('%Y-%m', v.fecha) AS periodo,
    CASE WHEN v.fecha <= '2020-12-31' THEN 'completa' ELSE 'parcial' END AS cobertura,
    p.categoria,
    COUNT(DISTINCT v.id_factura) AS facturas,
    SUM(dv.cantidad) AS unidades,
    SUM(dv.cantidad * dv.precio_venta) AS ventas,
    SUM((dv.precio_venta - dv.costo_venta) * dv.cantidad) AS margen
FROM detalle_venta dv
JOIN venta v ON v.id_factura = dv.id_factura
JOIN producto p ON p.id_producto = dv.id_producto
GROUP BY 1, 2, 3, 4, p.categoria;

-- Tarea 24: Flujo de caja mensual
CREATE VIEW vw_flujo_caja_mensual AS
WITH facturado_mes AS (
    SELECT
        strftime('%Y-%m', v.fecha) AS periodo,
        SUM(dv.cantidad * dv.precio_venta) AS ventas_facturadas,
        SUM(CASE WHEN v.por_cobrar = 0 THEN dv.cantidad * dv.precio_venta ELSE 0 END) AS ingresos_contado,
        SUM(CASE WHEN v.por_cobrar = 1 THEN dv.cantidad * dv.precio_venta ELSE 0 END) AS ventas_fiadas
    FROM venta v
    JOIN detalle_venta dv ON dv.id_factura = v.id_factura
    GROUP BY 1
),
cobros_mes AS (
    SELECT
        strftime('%Y-%m', fecha_pago) AS periodo,
        SUM(monto) AS cobros_fiado_recibidos,
        COUNT(*) AS cuentas_cobradas
    FROM cuenta_por_cobrar
    WHERE estado = 'PAGADA' AND fecha_pago IS NOT NULL
    GROUP BY 1
),
gastos_mes AS (
    SELECT
        strftime('%Y-%m', fecha) AS periodo,
        SUM(monto) AS gastos_insumo,
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
    CAST(substr(p.periodo, 1, 4) AS INTEGER) AS anio,
    CAST(substr(p.periodo, 6, 2) AS INTEGER) AS mes,
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

-- Tarea 25: Cuentas por cobrar por cliente
CREATE VIEW vw_cuentas_por_cobrar_cliente AS
SELECT
    c.id_cliente,
    c.nombre,
    c.contacto,
    COUNT(cxc.id_cuenta) AS total_cuentas_fiadas,
    COALESCE(SUM(cxc.monto), 0) AS monto_total_fiado,
    COALESCE(SUM(CASE WHEN cxc.estado = 'PAGADA' THEN cxc.monto ELSE 0 END), 0) AS monto_pagado,
    COALESCE(SUM(CASE WHEN cxc.estado IN ('PENDIENTE', 'VENCIDA') THEN cxc.monto ELSE 0 END), 0) AS monto_adeudado_actual,
    COALESCE(SUM(CASE WHEN cxc.estado = 'VENCIDA' THEN cxc.monto ELSE 0 END), 0) AS monto_vencido_actual,
    SUM(CASE WHEN cxc.estado IN ('PENDIENTE', 'VENCIDA') THEN 1 ELSE 0 END) AS cuentas_abiertas,
    SUM(CASE WHEN cxc.estado = 'VENCIDA' THEN 1 ELSE 0 END) AS cuentas_vencidas,
    MIN(CASE WHEN cxc.estado IN ('PENDIENTE', 'VENCIDA') THEN cxc.fecha_vencimiento END) AS proxima_fecha_cobro,
    MAX(
        CASE
            WHEN cxc.estado = 'VENCIDA' THEN CAST(julianday('2022-09-01') - julianday(cxc.fecha_vencimiento) AS INTEGER)
            ELSE 0
        END
    ) AS max_dias_atraso_actual,
    ROUND(
        AVG(
            CASE
                WHEN cxc.estado = 'PAGADA' AND cxc.fecha_pago > cxc.fecha_vencimiento
                    THEN julianday(cxc.fecha_pago) - julianday(cxc.fecha_vencimiento)
                WHEN cxc.estado = 'PAGADA' THEN 0.0
            END
        ),
        1
    ) AS promedio_dias_atraso_historico
FROM cliente c
LEFT JOIN cuenta_por_cobrar cxc ON cxc.id_cliente = c.id_cliente
GROUP BY c.id_cliente, c.nombre, c.contacto;

-- Tarea 26: Indicador de morosidad
CREATE VIEW vw_indicador_morosidad AS
SELECT
    'Corte Final Dataset (2022-09-01)' AS escenario,
    SUM(CASE WHEN estado IN ('PENDIENTE', 'VENCIDA') THEN 1 ELSE 0 END) AS cuentas_por_cobrar_abiertas,
    SUM(CASE WHEN estado = 'VENCIDA' THEN 1 ELSE 0 END) AS cuentas_vencidas,
    COALESCE(SUM(CASE WHEN estado IN ('PENDIENTE', 'VENCIDA') THEN monto ELSE 0 END), 0) AS monto_por_cobrar,
    COALESCE(SUM(CASE WHEN estado = 'VENCIDA' THEN monto ELSE 0 END), 0) AS monto_vencido,
    ROUND(
        CAST(COALESCE(SUM(CASE WHEN estado = 'VENCIDA' THEN monto ELSE 0 END), 0) AS REAL)
        / NULLIF(SUM(CASE WHEN estado IN ('PENDIENTE', 'VENCIDA') THEN monto ELSE 0 END), 0) * 100,
        2
    ) AS morosidad_monto_pct,
    ROUND(
        CAST(SUM(CASE WHEN estado = 'VENCIDA' THEN 1 ELSE 0 END) AS REAL)
        / NULLIF(SUM(CASE WHEN estado IN ('PENDIENTE', 'VENCIDA') THEN 1 ELSE 0 END), 0) * 100,
        2
    ) AS morosidad_cuentas_pct
FROM cuenta_por_cobrar
UNION ALL
SELECT
    'Cierre Cobertura Completa (2020-12-31)' AS escenario,
    SUM(CASE WHEN v.fecha <= '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > '2020-12-31') THEN 1 ELSE 0 END),
    SUM(CASE WHEN v.fecha <= '2020-12-31' AND c.fecha_vencimiento <= '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > '2020-12-31') THEN 1 ELSE 0 END),
    COALESCE(SUM(CASE WHEN v.fecha <= '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > '2020-12-31') THEN c.monto ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN v.fecha <= '2020-12-31' AND c.fecha_vencimiento <= '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > '2020-12-31') THEN c.monto ELSE 0 END), 0),
    ROUND(
        CAST(COALESCE(SUM(CASE WHEN v.fecha <= '2020-12-31' AND c.fecha_vencimiento <= '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > '2020-12-31') THEN c.monto ELSE 0 END), 0) AS REAL)
        / NULLIF(SUM(CASE WHEN v.fecha <= '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > '2020-12-31') THEN c.monto ELSE 0 END), 0) * 100,
        2
    ),
    ROUND(
        CAST(SUM(CASE WHEN v.fecha <= '2020-12-31' AND c.fecha_vencimiento <= '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > '2020-12-31') THEN 1 ELSE 0 END) AS REAL)
        / NULLIF(SUM(CASE WHEN v.fecha <= '2020-12-31' AND (c.fecha_pago IS NULL OR c.fecha_pago > '2020-12-31') THEN 1 ELSE 0 END), 0) * 100,
        2
    )
FROM cuenta_por_cobrar c
JOIN venta v ON v.id_factura = c.id_factura
UNION ALL
SELECT
    'Histórico Pagos con Atraso (2010-2022)' AS escenario,
    COUNT(*),
    SUM(CASE WHEN estado = 'VENCIDA' OR (estado = 'PAGADA' AND fecha_pago > fecha_vencimiento) THEN 1 ELSE 0 END),
    SUM(monto),
    COALESCE(SUM(CASE WHEN estado = 'VENCIDA' OR (estado = 'PAGADA' AND fecha_pago > fecha_vencimiento) THEN monto ELSE 0 END), 0),
    ROUND(
        CAST(COALESCE(SUM(CASE WHEN estado = 'VENCIDA' OR (estado = 'PAGADA' AND fecha_pago > fecha_vencimiento) THEN monto ELSE 0 END), 0) AS REAL)
        / NULLIF(SUM(monto), 0) * 100,
        2
    ),
    ROUND(
        CAST(SUM(CASE WHEN estado = 'VENCIDA' OR (estado = 'PAGADA' AND fecha_pago > fecha_vencimiento) THEN 1 ELSE 0 END) AS REAL)
        / NULLIF(COUNT(*), 0) * 100,
        2
    )
FROM cuenta_por_cobrar;

-- Tarea 27: Ranking de productos (cobertura completa 2010-2020)
CREATE VIEW vw_ranking_productos AS
WITH base AS (
    SELECT
        p.id_producto,
        p.producto,
        p.categoria,
        COUNT(DISTINCT dv.id_factura) AS num_facturas,
        SUM(dv.cantidad) AS unidades_vendidas,
        SUM(dv.cantidad * dv.precio_venta) AS ventas,
        SUM(dv.cantidad * dv.costo_venta) AS costo,
        SUM((dv.precio_venta - dv.costo_venta) * dv.cantidad) AS margen,
        ROUND(
            CAST(SUM((dv.precio_venta - dv.costo_venta) * dv.cantidad) AS REAL)
            / NULLIF(SUM(dv.cantidad * dv.precio_venta), 0) * 100,
            2
        ) AS margen_pct,
        CASE
            WHEN CAST(MAX(dv.precio_venta) AS REAL) / NULLIF(MIN(dv.precio_venta), 0) > 5 THEN 1
            ELSE 0
        END AS alerta_escala_etapa2
    FROM detalle_venta dv
    JOIN venta v ON v.id_factura = dv.id_factura
    JOIN producto p ON p.id_producto = dv.id_producto
    WHERE v.fecha <= '2020-12-31'
    GROUP BY p.id_producto, p.producto, p.categoria
),
stats AS (
    SELECT
        (SELECT ventas FROM base ORDER BY ventas LIMIT 1 OFFSET (SELECT COUNT(*) / 2 FROM base)) AS med_ventas,
        (SELECT margen FROM base ORDER BY margen LIMIT 1 OFFSET (SELECT COUNT(*) / 2 FROM base)) AS med_margen
)
SELECT
    b.*,
    RANK() OVER (ORDER BY b.ventas DESC) AS rank_ventas,
    RANK() OVER (ORDER BY b.margen DESC) AS rank_margen,
    CASE
        WHEN b.ventas >= s.med_ventas AND b.margen >= s.med_margen THEN 'Estrella'
        WHEN b.ventas >= s.med_ventas AND b.margen < s.med_margen THEN 'Alto volumen / Bajo margen'
        WHEN b.ventas < s.med_ventas AND b.margen >= s.med_margen THEN 'Nicho rentable'
        ELSE 'Baja venta'
    END AS clasificacion_desempeno
FROM base b
CROSS JOIN stats s;

-- Tarea 28: Evaluación anual de sustentabilidad del negocio
CREATE VIEW vw_sustentabilidad_negocio AS
WITH ventas_anio AS (
    SELECT
        CAST(strftime('%Y', v.fecha) AS INTEGER) AS anio,
        CASE WHEN strftime('%Y', v.fecha) <= '2020' THEN 'completa' ELSE 'parcial' END AS cobertura,
        SUM(dv.cantidad * dv.precio_venta) AS ventas,
        SUM(dv.cantidad * dv.costo_venta) AS costo,
        SUM((dv.precio_venta - dv.costo_venta) * dv.cantidad) AS margen_bruto,
        SUM(CASE WHEN v.por_cobrar = 1 THEN dv.cantidad * dv.precio_venta ELSE 0 END) AS monto_fiado
    FROM detalle_venta dv
    JOIN venta v ON v.id_factura = dv.id_factura
    GROUP BY 1, 2
),
gastos_anio AS (
    SELECT
        CAST(strftime('%Y', fecha) AS INTEGER) AS anio,
        SUM(monto) AS gastos_insumo
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
    ROUND(CAST(va.margen_bruto AS REAL) / NULLIF(ga.gastos_insumo, 0), 2) AS ratio_margen_sobre_gastos,
    ROUND(CAST(va.monto_fiado AS REAL) / NULLIF(va.ventas, 0) * 100, 2) AS pct_ventas_fiadas,
    ROUND(CAST(va.monto_fiado AS REAL) / NULLIF(va.margen_bruto, 0) * 100, 2) AS fiado_sobre_margen_pct
FROM ventas_anio va
LEFT JOIN gastos_anio ga ON ga.anio = va.anio
ORDER BY va.anio;
