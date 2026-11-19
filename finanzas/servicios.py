"""
Operaciones del negocio que modifican datos (registrar una venta, pagar una deuda, etc.).

Están aquí y no en las vistas para que cada regla viva en un solo lugar: la API,
el admin o un comando pueden usarlas y siempre se cumplen igual.
Cada operación es atómica: o se guarda todo, o no se guarda nada.

Ninguna operación BORRA filas: el usuario de la API en la base del equipo de datos
(cajaclara_app_rw) solo tiene permisos SELECT, INSERT y UPDATE.
"""

from django.db import transaction
from django.utils import timezone

from . import ids
from .models import Cliente, CuentaPorCobrar, DetalleVenta, GastoInsumo, Venta


class ReglaDeNegocio(Exception):
    """Error que se muestra tal cual al usuario (ej.: 'La cuenta ya está pagada')."""


def ultimo_precio_y_costo(producto):
    """Precio y costo unitarios de la venta más reciente del producto, o (None, None)
    si nunca se ha vendido. El esquema de datos no tiene precio de catálogo."""
    ultima = (
        DetalleVenta.objects.filter(producto=producto)
        .order_by("-venta__fecha", "-id_detalle")
        .values("precio_venta", "costo_venta")
        .first()
    )
    if ultima is None:
        return None, None
    return ultima["precio_venta"], ultima["costo_venta"]


@transaction.atomic
def registrar_venta(*, items, cliente, tipo_compra=Venta.FISICA, fecha=None, por_cobrar=False,
                    fecha_vencimiento=None):
    """Crea la venta con sus líneas. Si es a crédito, crea también su cuenta por cobrar.

    items: lista de dicts con "producto" (Producto), "cantidad" y opcionalmente
    "precio_venta" y "costo_venta" (unitarios). Si no vienen, se usan los de la última
    venta del producto.
    """
    if not items:
        raise ReglaDeNegocio("La venta debe tener al menos un producto.")
    if cliente is None:
        raise ReglaDeNegocio("La venta necesita un cliente.")
    fecha = fecha or timezone.localdate()
    if por_cobrar:
        if fecha_vencimiento is None:
            raise ReglaDeNegocio("Una venta a crédito necesita la fecha de vencimiento.")
        if fecha_vencimiento < fecha:
            raise ReglaDeNegocio("La fecha de vencimiento no puede ser anterior a la fecha de la venta.")

    lineas = []
    for item in items:
        producto = item["producto"]
        precio, costo = item.get("precio_venta"), item.get("costo_venta")
        if precio is None or costo is None:
            ultimo_precio, ultimo_costo = ultimo_precio_y_costo(producto)
            precio = ultimo_precio if precio is None else precio
            costo = ultimo_costo if costo is None else costo
        if precio is None or costo is None:
            raise ReglaDeNegocio(
                f"El producto {producto.id_producto} nunca se ha vendido: indica su precio_venta y costo_venta."
            )
        lineas.append((producto, item["cantidad"], precio, costo))

    def guardar():
        venta = Venta.objects.create(
            id_factura=ids.nuevo_id_factura(fecha, tipo_compra),
            cliente=cliente,
            fecha=fecha,
            tipo_compra=tipo_compra,
            por_cobrar=por_cobrar,
        )
        primer_id = ids.siguiente_id(DetalleVenta)
        detalles = DetalleVenta.objects.bulk_create([
            DetalleVenta(
                id_detalle=primer_id + i,
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_venta=precio,
                costo_venta=costo,
            )
            for i, (producto, cantidad, precio, costo) in enumerate(lineas)
        ])
        if por_cobrar:
            CuentaPorCobrar.objects.create(
                id_cuenta=ids.siguiente_id(CuentaPorCobrar),
                venta=venta,
                cliente=cliente,
                monto=sum(d.total_linea_venta for d in detalles),
                fecha_vencimiento=fecha_vencimiento,
                estado=CuentaPorCobrar.PENDIENTE,
            )
        return venta

    try:
        return ids.con_reintentos(guardar)
    except ids.SinIdDisponible as error:
        raise ReglaDeNegocio(str(error))


@transaction.atomic
def pagar_cuenta(cuenta, fecha_pago=None):
    """Marca una cuenta por cobrar como pagada (pago completo)."""
    cuenta = CuentaPorCobrar.objects.select_for_update().select_related("venta").get(pk=cuenta.pk)
    if cuenta.estado == CuentaPorCobrar.PAGADA:
        raise ReglaDeNegocio(f"La cuenta ya está pagada (el {cuenta.fecha_pago:%d/%m/%Y}).")
    hoy = timezone.localdate()
    fecha_pago = fecha_pago or hoy
    if fecha_pago > hoy:
        raise ReglaDeNegocio("La fecha de pago no puede ser futura.")
    if fecha_pago < cuenta.venta.fecha:
        raise ReglaDeNegocio("La fecha de pago no puede ser anterior a la venta.")
    cuenta.estado = CuentaPorCobrar.PAGADA
    cuenta.fecha_pago = fecha_pago
    cuenta.save(update_fields=["estado", "fecha_pago"])
    return cuenta


@transaction.atomic
def revertir_pago(cuenta):
    """Deshace un pago registrado por error: la cuenta vuelve a quedar abierta
    (VENCIDA si su fecha ya pasó, PENDIENTE si no)."""
    cuenta = CuentaPorCobrar.objects.select_for_update().get(pk=cuenta.pk)
    if cuenta.estado != CuentaPorCobrar.PAGADA:
        raise ReglaDeNegocio("La cuenta no está pagada.")
    vencida = cuenta.fecha_vencimiento < timezone.localdate()
    cuenta.estado = CuentaPorCobrar.VENCIDA if vencida else CuentaPorCobrar.PENDIENTE
    cuenta.fecha_pago = None
    cuenta.save(update_fields=["estado", "fecha_pago"])
    return cuenta


def registrar_gasto(*, producto, monto, fecha=None):
    """Registra una compra de insumos (siempre ligada a un producto)."""
    def guardar():
        return GastoInsumo.objects.create(
            id_gasto=ids.siguiente_id(GastoInsumo),
            producto=producto,
            fecha=fecha or timezone.localdate(),
            monto=monto,
        )

    try:
        return ids.con_reintentos(guardar)
    except ids.SinIdDisponible as error:
        raise ReglaDeNegocio(str(error))


def crear_cliente(*, nombre, contacto):
    """Los clientes siguen la numeración de id_cliente (1, 2, 3...)."""
    if Cliente.objects.filter(contacto=contacto).exists():
        raise ReglaDeNegocio("Ya existe un cliente con ese contacto.")

    def guardar():
        return Cliente.objects.create(id_cliente=ids.siguiente_id(Cliente), nombre=nombre, contacto=contacto)

    try:
        return ids.con_reintentos(guardar)
    except ids.SinIdDisponible as error:
        raise ReglaDeNegocio(str(error))
