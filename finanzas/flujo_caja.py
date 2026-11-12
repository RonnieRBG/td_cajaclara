"""
Flujo de caja: el dinero que realmente ENTRÓ y SALIÓ del negocio en un período.

Es distinto de la utilidad (ingresos - costo de lo vendido):
- Una venta a crédito no entra a la caja el día que se vende, sino el día que se paga.
- Los gastos (compras para reponer, arriendo, flete, etc.) salen de la caja el día que se pagan.

Entradas = ventas al contado del período + cobros de deudas pagadas en el período.
Salidas  = compras + otros gastos del período.
Saldo    = entradas - salidas.

Las ventas anuladas no cuentan. El filtro de canal (tipo_compra) se aplica a las
entradas; los gastos no tienen canal, así que siempre se cuentan completos.
"""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from .models import CuentaPorCobrar, DetalleVenta, GastoInsumo

CERO = Decimal("0")
_MONTO = DecimalField(max_digits=14, decimal_places=2)


def _momento(dia):
    return timezone.make_aware(datetime.combine(dia, time.min))


def _sumar(queryset, campo_monto, trunc=None, campo_fecha=None, a_clave=None):
    """Suma un monto; si se indica trunc, devuelve {inicio_del_periodo: monto}."""
    if trunc is None:
        return queryset.aggregate(total=Sum(campo_monto))["total"] or CERO
    filas = (
        queryset.order_by()
        .annotate(grupo=trunc(campo_fecha))
        .values("grupo")
        .annotate(total=Sum(campo_monto))
    )
    resultado = {}
    for fila in filas:
        clave = a_clave(fila["grupo"])
        resultado[clave] = resultado.get(clave, CERO) + (fila["total"] or CERO)
    return resultado


def calcular(fecha_inicio, fecha_fin, tipo_compra=None, trunc=None, a_clave=None):
    """Calcula las entradas y salidas entre dos fechas (ambas incluidas).

    Sin trunc devuelve los totales. Con trunc (TruncMonth, etc.) y a_clave (función que
    convierte el valor truncado en la fecha de inicio del período) devuelve un dict
    por período con las mismas claves.
    """
    desde, hasta = _momento(fecha_inicio), _momento(fecha_fin + timedelta(days=1))

    contado = DetalleVenta.objects.filter(
        factura__fecha__gte=desde,
        factura__fecha__lt=hasta,
        factura__anulada=False,
        factura__por_cobrar=False,
    ).annotate(total_linea=ExpressionWrapper(F("cantidad") * F("precio_unitario"), output_field=_MONTO))
    cobros = CuentaPorCobrar.objects.filter(
        estado=CuentaPorCobrar.PAGADA,
        fecha_pago__gte=fecha_inicio,
        fecha_pago__lte=fecha_fin,
        factura__anulada=False,
    )
    if tipo_compra:
        contado = contado.filter(factura__tipo_compra_id=tipo_compra)
        cobros = cobros.filter(factura__tipo_compra_id=tipo_compra)
    gastos = GastoInsumo.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)

    def suma(qs, monto, campo_fecha, es_fecha_hora=False):
        if trunc is None:
            return _sumar(qs, monto)
        convertir = (lambda v: a_clave(timezone.localtime(v).date())) if es_fecha_hora else a_clave
        return _sumar(qs, monto, trunc, campo_fecha, convertir)

    partes = {
        "ventas_contado": suma(contado, "total_linea", "factura__fecha", es_fecha_hora=True),
        "cobros": suma(cobros, "monto", "fecha_pago"),
        "compras": suma(gastos.filter(tipo=GastoInsumo.COMPRA), "monto", "fecha"),
        "otros_gastos": suma(gastos.filter(tipo=GastoInsumo.OTRO), "monto", "fecha"),
    }
    if trunc is None:
        return _armar(partes)
    claves = set().union(*(p.keys() for p in partes.values()))
    return {clave: _armar({k: v.get(clave, CERO) for k, v in partes.items()}) for clave in claves}


def _armar(p):
    entradas = p["ventas_contado"] + p["cobros"]
    salidas = p["compras"] + p["otros_gastos"]
    return {
        "entradas": {
            "ventas_contado": p["ventas_contado"],
            "cobros": p["cobros"],
            "total": entradas,
        },
        "salidas": {
            "compras": p["compras"],
            "otros_gastos": p["otros_gastos"],
            "total": salidas,
        },
        "saldo": entradas - salidas,
    }


def vacio():
    return _armar({"ventas_contado": CERO, "cobros": CERO, "compras": CERO, "otros_gastos": CERO})


def a_json(flujo, redondear):
    """Convierte los Decimal a números para la respuesta (con la misma función _monto de las vistas)."""
    return {
        "entradas": {k: redondear(v) for k, v in flujo["entradas"].items()},
        "salidas": {k: redondear(v) for k, v in flujo["salidas"].items()},
        "saldo": redondear(flujo["saldo"]),
    }
