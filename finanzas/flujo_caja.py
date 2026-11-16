"""
Flujo de caja: el dinero que realmente ENTRÓ y SALIÓ del negocio en un período.

Es distinto de la utilidad (ingresos - costo de lo vendido):
- Una venta a crédito no entra a la caja el día que se vende, sino el día que se paga.
- Los gastos en insumos salen de la caja el día que se registran.

Entradas = ventas al contado del período + cobros de deudas pagadas en el período.
Salidas  = gastos en insumos del período.
Saldo    = entradas - salidas.

Es la misma lógica que la vista vw_flujo_caja_mensual del equipo de datos.
El filtro de canal (tipo_compra) se aplica a las entradas; los gastos no tienen
canal, así que siempre se cuentan completos.
"""

from django.db.models import F, Sum

from .models import CuentaPorCobrar, DetalleVenta, GastoInsumo


def _sumar(queryset, campo_monto, trunc=None, campo_fecha=None, a_clave=None):
    """Suma un monto; si se indica trunc, devuelve {inicio_del_periodo: monto}."""
    if trunc is None:
        return queryset.aggregate(total=Sum(campo_monto))["total"] or 0
    filas = (
        queryset.order_by()
        .annotate(grupo=trunc(campo_fecha))
        .values("grupo")
        .annotate(total=Sum(campo_monto))
    )
    resultado = {}
    for fila in filas:
        clave = a_clave(fila["grupo"])
        resultado[clave] = resultado.get(clave, 0) + (fila["total"] or 0)
    return resultado


def calcular(fecha_inicio, fecha_fin, tipo_compra=None, trunc=None, a_clave=None):
    """Calcula las entradas y salidas entre dos fechas (ambas incluidas).

    Sin trunc devuelve los totales. Con trunc (TruncMonth, etc.) y a_clave (función que
    convierte el valor truncado en la fecha de inicio del período) devuelve un dict
    por período con las mismas claves.
    """
    contado = DetalleVenta.objects.filter(
        venta__fecha__gte=fecha_inicio,
        venta__fecha__lte=fecha_fin,
        venta__por_cobrar=False,
    ).annotate(total_linea=F("cantidad") * F("precio_venta"))
    cobros = CuentaPorCobrar.objects.filter(
        estado=CuentaPorCobrar.PAGADA,
        fecha_pago__gte=fecha_inicio,
        fecha_pago__lte=fecha_fin,
    )
    if tipo_compra:
        contado = contado.filter(venta__tipo_compra=tipo_compra)
        cobros = cobros.filter(venta__tipo_compra=tipo_compra)
    gastos = GastoInsumo.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)

    def suma(qs, monto, campo_fecha):
        if trunc is None:
            return _sumar(qs, monto)
        return _sumar(qs, monto, trunc, campo_fecha, a_clave)

    partes = {
        "ventas_contado": suma(contado, "total_linea", "venta__fecha"),
        "cobros": suma(cobros, "monto", "fecha_pago"),
        "gastos_insumo": suma(gastos, "monto", "fecha"),
    }
    if trunc is None:
        return _armar(partes)
    claves = set().union(*(p.keys() for p in partes.values()))
    return {clave: _armar({k: v.get(clave, 0) for k, v in partes.items()}) for clave in claves}


def _armar(p):
    entradas = p["ventas_contado"] + p["cobros"]
    salidas = p["gastos_insumo"]
    return {
        "entradas": {
            "ventas_contado": p["ventas_contado"],
            "cobros": p["cobros"],
            "total": entradas,
        },
        "salidas": {
            "gastos_insumo": p["gastos_insumo"],
            "total": salidas,
        },
        "saldo": entradas - salidas,
    }


def vacio():
    return _armar({"ventas_contado": 0, "cobros": 0, "gastos_insumo": 0})


def a_json(flujo):
    return {
        "entradas": {k: int(v) for k, v in flujo["entradas"].items()},
        "salidas": {k: int(v) for k, v in flujo["salidas"].items()},
        "saldo": int(flujo["saldo"]),
    }
