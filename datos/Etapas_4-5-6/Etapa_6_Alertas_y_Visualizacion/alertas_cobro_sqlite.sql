-- ============================================================================
-- Caja Clara — Etapa 6: Vista de Alertas de Cobro (SQLite 3)
-- Equivalente exacto de alertas_cobro_postgresql.sql para ejecución local
-- ============================================================================

DROP VIEW IF EXISTS vw_alertas_cobro;

CREATE VIEW vw_alertas_cobro AS
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
    CAST(julianday(cxc.fecha_vencimiento) - julianday('2022-09-01') AS INTEGER) AS dias_para_vencer,
    CASE
        WHEN cxc.fecha_vencimiento < '2022-09-01'
            THEN CAST(julianday('2022-09-01') - julianday(cxc.fecha_vencimiento) AS INTEGER)
        ELSE 0
    END AS dias_atraso,
    CASE
        WHEN cxc.estado = 'VENCIDA' OR cxc.fecha_vencimiento < '2022-09-01'
            THEN 'VENCIDA'
        ELSE 'POR_VENCER'
    END AS tipo_alerta,
    CASE
        WHEN cxc.estado = 'VENCIDA' OR cxc.fecha_vencimiento < '2022-09-01'
            THEN '1_CRITICA_VENCIDA'
        WHEN (julianday(cxc.fecha_vencimiento) - julianday('2022-09-01')) <= 7
            THEN '2_ALTA_PROXIMA_7D'
        WHEN (julianday(cxc.fecha_vencimiento) - julianday('2022-09-01')) <= 15
            THEN '3_MEDIA_PROXIMA_15D'
        ELSE '4_BAJA_VIGENTE'
    END AS prioridad_alerta,
    CASE
        WHEN cxc.estado = 'VENCIDA' OR cxc.fecha_vencimiento < '2022-09-01'
            THEN 'Vencida'
        WHEN (julianday(cxc.fecha_vencimiento) - julianday('2022-09-01')) <= 7
            THEN 'Vence en <= 7 días'
        WHEN (julianday(cxc.fecha_vencimiento) - julianday('2022-09-01')) <= 15
            THEN 'Vence en 8-15 días'
        ELSE 'Vigente > 15 días'
    END AS ventana_alerta,
    CASE
        WHEN cxc.estado = 'VENCIDA'
          OR (julianday(cxc.fecha_vencimiento) - julianday('2022-09-01')) <= 15
            THEN 1
        ELSE 0
    END AS requiere_notificacion,
    CASE
        WHEN cxc.estado = 'VENCIDA' OR cxc.fecha_vencimiento < '2022-09-01'
            THEN 'Recordatorio urgente: cliente ' || c.nombre || ' mantiene factura '
                 || cxc.id_factura || ' vencida hace '
                 || CAST(julianday('2022-09-01') - julianday(cxc.fecha_vencimiento) AS INTEGER)
                 || ' días por $' || cxc.monto || '.'
        ELSE 'Aviso preventivo: factura ' || cxc.id_factura || ' de ' || c.nombre
             || ' vence el ' || cxc.fecha_vencimiento
             || ' (en ' || CAST(julianday(cxc.fecha_vencimiento) - julianday('2022-09-01') AS INTEGER)
             || ' días) por $' || cxc.monto || '.'
    END AS mensaje_sugerido
FROM cuenta_por_cobrar cxc
JOIN cliente c ON c.id_cliente = cxc.id_cliente
JOIN venta v ON v.id_factura = cxc.id_factura
WHERE cxc.estado IN ('PENDIENTE', 'VENCIDA')
  AND cxc.fecha_pago IS NULL;
