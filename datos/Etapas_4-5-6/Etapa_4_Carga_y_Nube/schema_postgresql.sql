-- ============================================================================
-- Caja Clara — Esquema Relacional Definitivo (PostgreSQL 16+)
-- Etapa 4: Carga y Nube (Tareas 17, 18, 19, 20)
-- Corrige las inconsistencias detectadas entre el MER SVG y los CSV de Etapa 3
-- ============================================================================

DROP TABLE IF EXISTS gastos_insumo CASCADE;
DROP TABLE IF EXISTS cuenta_por_cobrar CASCADE;
DROP TABLE IF EXISTS detalle_venta CASCADE;
DROP TABLE IF EXISTS venta CASCADE;
DROP TABLE IF EXISTS producto CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;

-- 1. Catálogo de clientes (ventas al fiado y trazabilidad de cobro)
CREATE TABLE cliente (
    id_cliente      INTEGER PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    contacto        VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Catálogo único de productos (incluye categoría de ingreso y unidad de negocio)
-- Nota: producto usa VARCHAR(150) porque el largo máximo observado es 108 caracteres.
CREATE TABLE producto (
    id_producto     VARCHAR(10) PRIMARY KEY,
    categoria       VARCHAR(100) NOT NULL,
    producto        VARCHAR(150) NOT NULL,
    unidad_negocio  VARCHAR(100) NOT NULL
);

-- 3. Cabecera de ventas (una fila por factura)
CREATE TABLE venta (
    id_factura      VARCHAR(30) PRIMARY KEY,
    id_cliente      INTEGER NOT NULL REFERENCES cliente(id_cliente) ON UPDATE CASCADE ON DELETE RESTRICT,
    fecha           DATE NOT NULL,
    tipo_compra     VARCHAR(20) NOT NULL CHECK (tipo_compra IN ('Física', 'En Línea')),
    por_cobrar      BOOLEAN NOT NULL DEFAULT FALSE
);

-- 4. Detalle de ventas (una fila por línea de factura; precios y costos unitarios en CLP)
CREATE TABLE detalle_venta (
    id_detalle      INTEGER PRIMARY KEY,
    id_factura      VARCHAR(30) NOT NULL REFERENCES venta(id_factura) ON UPDATE CASCADE ON DELETE CASCADE,
    id_producto     VARCHAR(10) NOT NULL REFERENCES producto(id_producto) ON UPDATE CASCADE ON DELETE RESTRICT,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_venta    INTEGER NOT NULL CHECK (precio_venta > 0),
    costo_venta     INTEGER NOT NULL CHECK (costo_venta > 0)
);

-- 5. Cuentas por cobrar (relación 1 : 0..1 con venta; enriquecida en Tarea 19 con estado y fecha_pago)
CREATE TABLE cuenta_por_cobrar (
    id_cuenta           INTEGER PRIMARY KEY,
    id_factura          VARCHAR(30) NOT NULL UNIQUE REFERENCES venta(id_factura) ON UPDATE CASCADE ON DELETE RESTRICT,
    id_cliente          INTEGER NOT NULL REFERENCES cliente(id_cliente) ON UPDATE CASCADE ON DELETE RESTRICT,
    monto               INTEGER NOT NULL CHECK (monto > 0),
    fecha_vencimiento   DATE NOT NULL,
    estado              VARCHAR(15) NOT NULL CHECK (estado IN ('PAGADA', 'PENDIENTE', 'VENCIDA')),
    fecha_pago          DATE NULL,
    CONSTRAINT chk_cxc_estado_pago CHECK (
        (estado = 'PAGADA' AND fecha_pago IS NOT NULL)
        OR (estado IN ('PENDIENTE', 'VENCIDA') AND fecha_pago IS NULL)
    )
);

-- 6. Gastos de insumos asociados a productos
CREATE TABLE gastos_insumo (
    id_gasto        INTEGER PRIMARY KEY,
    id_producto     VARCHAR(10) NOT NULL REFERENCES producto(id_producto) ON UPDATE CASCADE ON DELETE RESTRICT,
    fecha           DATE NOT NULL,
    monto           INTEGER NOT NULL CHECK (monto > 0)
);

-- Índices para consultas analíticas (Etapa 5) y alertas/API (Etapas 6 y 7)
CREATE INDEX idx_venta_fecha ON venta (fecha);
CREATE INDEX idx_venta_cliente ON venta (id_cliente);
CREATE INDEX idx_venta_por_cobrar ON venta (por_cobrar) WHERE por_cobrar = TRUE;

CREATE INDEX idx_detalle_factura ON detalle_venta (id_factura);
CREATE INDEX idx_detalle_producto ON detalle_venta (id_producto);

CREATE INDEX idx_cxc_cliente ON cuenta_por_cobrar (id_cliente);
CREATE INDEX idx_cxc_estado_vencimiento ON cuenta_por_cobrar (estado, fecha_vencimiento);
CREATE INDEX idx_cxc_fecha_pago ON cuenta_por_cobrar (fecha_pago) WHERE fecha_pago IS NOT NULL;

CREATE INDEX idx_gastos_fecha ON gastos_insumo (fecha);
CREATE INDEX idx_gastos_producto ON gastos_insumo (id_producto);
CREATE INDEX idx_producto_categoria ON producto (categoria);
