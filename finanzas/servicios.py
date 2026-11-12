"""
Operaciones del negocio que modifican datos (registrar una venta, pagar una deuda, etc.).

Están aquí y no en las vistas para que cada regla viva en un solo lugar: la API,
el admin o un comando pueden usarlas y siempre se cumplen igual.
Cada operación es atómica: o se guarda todo, o no se guarda nada.
"""

import uuid
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import IntegerField, Max
from django.db.models.functions import Cast
from django.utils import timezone

from .models import CERO, Cliente, CuentaPorCobrar, DetalleVenta, Factura


class ReglaDeNegocio(Exception):
    """Error que se muestra tal cual al usuario (ej.: 'La cuenta ya está pagada')."""


def _nuevo_id_factura(fecha, tipo_compra):
    # Mismo estilo que las del CSV (INV7811414-20100105-F), con prefijo propio "CC"
    # para distinguir las ventas registradas desde la app.
    canal = "L" if tipo_compra == "ONLINE" else "F"
    return f"CC{uuid.uuid4().hex[:8].upper()}-{timezone.localtime(fecha):%Y%m%d}-{canal}"


@transaction.atomic
def registrar_venta(*, items, tipo_compra="FISICA", cliente=None, fecha=None, por_cobrar=False,
                    fecha_vencimiento=None):
    """Crea la factura con sus líneas. Si es a crédito, crea también su cuenta por cobrar.

    items: lista de dicts con "producto" (Producto), "cantidad" y opcionalmente "precio_unitario".
    El costo de cada línea se toma del catálogo del producto en ese momento.
    """
    if not items:
        raise ReglaDeNegocio("La venta debe tener al menos un producto.")
    fecha = fecha or timezone.now()
    if por_cobrar:
        if cliente is None:
            raise ReglaDeNegocio("Una venta a crédito necesita un cliente.")
        if fecha_vencimiento is None:
            raise ReglaDeNegocio("Una venta a crédito necesita la fecha de vencimiento.")
        if fecha_vencimiento < timezone.localtime(fecha).date():
            raise ReglaDeNegocio("La fecha de vencimiento no puede ser anterior a la fecha de la venta.")

    factura = Factura.objects.create(
        factura=_nuevo_id_factura(fecha, tipo_compra),
        cliente=cliente,
        fecha=fecha,
        tipo_compra_id=tipo_compra,
        por_cobrar=por_cobrar,
    )
    lineas = []
    for item in items:
        producto = item["producto"]
        precio = item.get("precio_unitario")
        lineas.append(
            DetalleVenta(
                factura=factura,
                no_parte=producto,
                cantidad=item["cantidad"],
                precio_unitario=producto.precio_venta if precio is None else precio,
                costo_unitario=producto.costo_venta,
            )
        )
    DetalleVenta.objects.bulk_create(lineas)

    if por_cobrar:
        total = sum((linea.total_linea_venta for linea in lineas), CERO)
        CuentaPorCobrar.objects.create(
            factura=factura,
            cliente=cliente,
            monto=total,
            fecha_vencimiento=fecha_vencimiento,
        )
    return factura


@transaction.atomic
def anular_factura(factura):
    """Anula una venta completa. Si era a crédito y aún no se pagaba, su deuda desaparece."""
    factura = Factura.objects.select_for_update().get(pk=factura.pk)
    if factura.anulada:
        raise ReglaDeNegocio("La venta ya estaba anulada.")
    cuenta = CuentaPorCobrar.objects.filter(factura=factura).first()
    if cuenta and cuenta.estado == CuentaPorCobrar.PAGADA:
        raise ReglaDeNegocio("La venta ya fue pagada. Primero revierte el pago y luego anúlala.")
    if cuenta:
        cuenta.delete()  # la deuda deja de existir junto con la venta
    factura.anulada = True
    factura.save(update_fields=["anulada"])
    return factura


@transaction.atomic
def pagar_cuenta(cuenta, fecha_pago=None):
    """Marca una cuenta por cobrar como pagada (pago completo)."""
    cuenta = CuentaPorCobrar.objects.select_for_update().select_related("factura").get(pk=cuenta.pk)
    if cuenta.estado == CuentaPorCobrar.PAGADA:
        raise ReglaDeNegocio(f"La cuenta ya está pagada (el {cuenta.fecha_pago:%d/%m/%Y}).")
    if cuenta.factura.anulada:
        raise ReglaDeNegocio("La venta de esta cuenta está anulada.")
    hoy = timezone.localdate()
    fecha_pago = fecha_pago or hoy
    if fecha_pago > hoy:
        raise ReglaDeNegocio("La fecha de pago no puede ser futura.")
    if cuenta.factura.fecha and fecha_pago < timezone.localtime(cuenta.factura.fecha).date():
        raise ReglaDeNegocio("La fecha de pago no puede ser anterior a la venta.")
    cuenta.estado = CuentaPorCobrar.PAGADA
    cuenta.fecha_pago = fecha_pago
    cuenta.save(update_fields=["estado", "fecha_pago"])
    return cuenta


@transaction.atomic
def revertir_pago(cuenta):
    """Deshace un pago registrado por error: la cuenta vuelve a quedar pendiente."""
    cuenta = CuentaPorCobrar.objects.select_for_update().get(pk=cuenta.pk)
    if cuenta.estado != CuentaPorCobrar.PAGADA:
        raise ReglaDeNegocio("La cuenta no está pagada.")
    cuenta.estado = CuentaPorCobrar.PENDIENTE
    cuenta.fecha_pago = None
    cuenta.save(update_fields=["estado", "fecha_pago"])
    return cuenta


def crear_cliente(*, nombre, contacto=""):
    """Los clientes del CSV tienen IDs numéricos ("1" a "2000"); los nuevos siguen la numeración.
    Si dos personas crean un cliente al mismo tiempo y chocan, se reintenta con el siguiente número."""
    for _ in range(5):
        ultimo = (
            Cliente.objects.filter(cliente_id__regex=r"^\d+$")
            .aggregate(maximo=Max(Cast("cliente_id", IntegerField())))["maximo"]
        ) or 0
        try:
            with transaction.atomic():
                return Cliente.objects.create(cliente_id=str(ultimo + 1), nombre=nombre, contacto=contacto)
        except IntegrityError:
            continue
    raise ReglaDeNegocio("No se pudo asignar un número al cliente. Intenta de nuevo.")


def total_factura(factura):
    return sum((d.total_linea_venta for d in factura.detalles.all()), Decimal("0"))
