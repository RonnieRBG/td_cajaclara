-- ============================================================================
-- Caja Clara — Esquema Relacional Definitivo (SQLite 3)
-- Equivalente local del esquema PostgreSQL para verificación y análisis offline
-- ============================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS gastos_insumo;
DROP TABLE IF EXISTS cuenta_por_cobrar;
DROP TABLE IF EXISTS detalle_venta;
DROP TABLE IF EXISTS venta;
DROP TABLE IF EXISTS producto;
DROP TABLE IF EXISTS cliente;

CREATE TABLE cliente (
    id_cliente      INTEGER PRIMARY KEY,
    nombre          TEXT NOT NULL,
    contacto        TEXT NOT NULL UNIQUE
);

CREATE TABLE producto (
    id_producto     TEXT PRIMARY KEY,
    categoria       TEXT NOT NULL,
    producto        TEXT NOT NULL,
    unidad_negocio  TEXT NOT NULL
);

CREATE TABLE venta (
    id_factura      TEXT PRIMARY KEY,
    id_cliente      INTEGER NOT NULL REFERENCES cliente(id_cliente) ON UPDATE CASCADE ON DELETE RESTRICT,
    fecha           TEXT NOT NULL,
    tipo_compra     TEXT NOT NULL CHECK (tipo_compra IN ('Física', 'En Línea')),
    por_cobrar      INTEGER NOT NULL DEFAULT 0 CHECK (por_cobrar IN (0, 1))
);

CREATE TABLE detalle_venta (
    id_detalle      INTEGER PRIMARY KEY,
    id_factura      TEXT NOT NULL REFERENCES venta(id_factura) ON UPDATE CASCADE ON DELETE CASCADE,
    id_producto     TEXT NOT NULL REFERENCES producto(id_producto) ON UPDATE CASCADE ON DELETE RESTRICT,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_venta    INTEGER NOT NULL CHECK (precio_venta > 0),
    costo_venta     INTEGER NOT NULL CHECK (costo_venta > 0)
);

CREATE TABLE cuenta_por_cobrar (
    id_cuenta           INTEGER PRIMARY KEY,
    id_factura          TEXT NOT NULL UNIQUE REFERENCES venta(id_factura) ON UPDATE CASCADE ON DELETE RESTRICT,
    id_cliente          INTEGER NOT NULL REFERENCES cliente(id_cliente) ON UPDATE CASCADE ON DELETE RESTRICT,
    monto               INTEGER NOT NULL CHECK (monto > 0),
    fecha_vencimiento   TEXT NOT NULL,
    estado              TEXT NOT NULL CHECK (estado IN ('PAGADA', 'PENDIENTE', 'VENCIDA')),
    fecha_pago          TEXT NULL,
    CHECK (
        (estado = 'PAGADA' AND fecha_pago IS NOT NULL)
        OR (estado IN ('PENDIENTE', 'VENCIDA') AND fecha_pago IS NULL)
    )
);

CREATE TABLE gastos_insumo (
    id_gasto        INTEGER PRIMARY KEY,
    id_producto     TEXT NOT NULL REFERENCES producto(id_producto) ON UPDATE CASCADE ON DELETE RESTRICT,
    fecha           TEXT NOT NULL,
    monto           INTEGER NOT NULL CHECK (monto > 0)
);

CREATE INDEX idx_venta_fecha ON venta (fecha);
CREATE INDEX idx_venta_cliente ON venta (id_cliente);
CREATE INDEX idx_detalle_factura ON detalle_venta (id_factura);
CREATE INDEX idx_detalle_producto ON detalle_venta (id_producto);
CREATE INDEX idx_cxc_cliente ON cuenta_por_cobrar (id_cliente);
CREATE INDEX idx_cxc_estado_vencimiento ON cuenta_por_cobrar (estado, fecha_vencimiento);
CREATE INDEX idx_cxc_fecha_pago ON cuenta_por_cobrar (fecha_pago);
CREATE INDEX idx_gastos_fecha ON gastos_insumo (fecha);
CREATE INDEX idx_gastos_producto ON gastos_insumo (id_producto);
CREATE INDEX idx_producto_categoria ON producto (categoria);
