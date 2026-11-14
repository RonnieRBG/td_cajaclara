-- ============================================================================
-- Caja Clara — Etapa 6: Consultas y Vistas de Alertas de Cobro (PostgreSQL / Neon)
-- Tarea 29: Definir consulta para detectar cuentas vencidas o próximas a vencer
--           para alertas desde Python (y consumo operativo en Power BI)
-- Tarea 30: Complemento de vistas SQL analíticas de Etapa 5
-- ============================================================================
-- NOTA SOBRE FECHA DE CORTE:
-- En el dataset histórico cargado en Etapa 4, la fecha de corte operativa es
-- 2022-09-01 (coincidente con vw_cuentas_por_cobrar_cliente y vw_indicador_morosidad).
-- La vista `vw_alertas_cobro` usa DATE '2022-09-01' para mantener coherencia 1:1
-- con las vistas históricas y los KPIs del dashboard. En la Sección B al final de
-- este archivo se incluye la consulta parametrizada para el backend Python/Django
-- usando CURRENT_DATE en operación en vivo.
-- ============================================================================

DROP VIEW IF EXISTS vw_alertas_cobro;

CREATE VIEW vw_alertas_cobro AS
WITH corte AS (
    SELECT DATE '2022-09-01' AS fecha_corte
)
SELECT
    cxc.id_cuenta,
    cxc.id_factura,
    c.id_cliente,
    c.nombre AS cliente_nombre,
    c.contacto AS cliente_contacto,
    v.fecha AS fecha_emision,
    cxc.fecha_vencimiento,
    cxc.estado,
    cxc.monto AS monto,
    (cxc.fecha_vencimiento - k.fecha_corte)::INT AS dias_para_vencer,
    CASE
        WHEN cxc.fecha_vencimiento < k.fecha_corte
            THEN (k.fecha_corte - cxc.fecha_vencimiento)::INT
        ELSE 0
    END AS dias_atraso,
    CASE
        WHEN cxc.estado = 'VENCIDA' OR cxc.fecha_vencimiento < k.fecha_corte
            THEN 'VENCIDA'
        ELSE 'POR_VENCER'
    END AS tipo_alerta,
    CASE
        WHEN cxc.estado = 'VENCIDA' OR cxc.fecha_vencimiento < k.fecha_corte
            THEN '1_CRITICA_VENCIDA'
        WHEN (cxc.fecha_vencimiento - k.fecha_corte) <= 7
            THEN '2_ALTA_PROXIMA_7D'
        WHEN (cxc.fecha_vencimiento - k.fecha_corte) <= 15
            THEN '3_MEDIA_PROXIMA_15D'
        ELSE '4_BAJA_VIGENTE'
    END AS prioridad_alerta,
    CASE
        WHEN cxc.estado = 'VENCIDA' OR cxc.fecha_vencimiento < k.fecha_corte
            THEN 'Vencida'
        WHEN (cxc.fecha_vencimiento - k.fecha_corte) <= 7
            THEN 'Vence en <= 7 días'
        WHEN (cxc.fecha_vencimiento - k.fecha_corte) <= 15
            THEN 'Vence en 8-15 días'
        ELSE 'Vigente > 15 días'
    END AS ventana_alerta,
    (
        cxc.estado = 'VENCIDA'
        OR cxc.fecha_vencimiento <= k.fecha_corte + INTERVAL '15 days'
    ) AS requiere_notificacion,
    CASE
        WHEN cxc.estado = 'VENCIDA' OR cxc.fecha_vencimiento < k.fecha_corte
            THEN 'Recordatorio urgente: cliente ' || c.nombre || ' mantiene factura '
                 || cxc.id_factura || ' vencida hace '
                 || (k.fecha_corte - cxc.fecha_vencimiento)::INT
                 || ' días por $' || cxc.monto || '.'
        ELSE 'Aviso preventivo: factura ' || cxc.id_factura || ' de ' || c.nombre
             || ' vence el ' || TO_CHAR(cxc.fecha_vencimiento, 'YYYY-MM-DD')
             || ' (en ' || (cxc.fecha_vencimiento - k.fecha_corte)::INT
             || ' días) por $' || cxc.monto || '.'
    END AS mensaje_sugerido
FROM cuenta_por_cobrar cxc
JOIN cliente c ON c.id_cliente = cxc.id_cliente
JOIN venta v ON v.id_factura = cxc.id_factura
CROSS JOIN corte k
WHERE cxc.estado IN ('PENDIENTE', 'VENCIDA')
  AND cxc.fecha_pago IS NULL;

-- Otorgar lectura a roles creados en Etapa 4
GRANT SELECT ON vw_alertas_cobro TO cajaclara_lectura_bi, cajaclara_app_rw;


-- ============================================================================
-- SECCIÓN B: Consulta SQL parametrizada para Python / Django en producción
-- (Usa CURRENT_DATE o un parámetro explícito %(fecha_corte)s / %(dias_aviso)s)
-- ============================================================================
/*
SELECT
    cxc.id_cuenta,
    cxc.id_factura,
    c.id_cliente,
    c.nombre AS cliente_nombre,
    c.contacto AS cliente_contacto,
    cxc.fecha_vencimiento,
    cxc.estado,
    cxc.monto AS monto,
    (cxc.fecha_vencimiento - COALESCE(%(fecha_corte)s::date, CURRENT_DATE))::INT AS dias_para_vencer,
    CASE
        WHEN cxc.fecha_vencimiento < COALESCE(%(fecha_corte)s::date, CURRENT_DATE)
            THEN 'VENCIDA'
        ELSE 'PROXIMA_A_VENCER'
    END AS tipo_alerta
FROM cuenta_por_cobrar cxc
JOIN cliente c ON c.id_cliente = cxc.id_cliente
WHERE cxc.estado IN ('PENDIENTE', 'VENCIDA')
  AND cxc.fecha_pago IS NULL
  AND cxc.fecha_vencimiento <= COALESCE(%(fecha_corte)s::date, CURRENT_DATE)
                               + MAKE_INTERVAL(days => COALESCE(%(dias_aviso)s::int, 15))
ORDER BY
    CASE WHEN cxc.fecha_vencimiento < COALESCE(%(fecha_corte)s::date, CURRENT_DATE) THEN 0 ELSE 1 END,
    cxc.fecha_vencimiento ASC,
    cxc.monto DESC;
*/
