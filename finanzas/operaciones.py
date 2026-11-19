"""
Endpoints pensados para las pantallas del frontend (rama ux), usando solo lo que
existe en el esquema del equipo de datos:

- /operaciones/        → ventas y gastos en una sola lista (pantalla "Compras y ventas"
                         y "Operaciones recientes" del dashboard).
- /opciones/clientes/  → lista liviana para el selector de cliente de los formularios.
- /opciones/productos/ → lista liviana para el selector de producto, con el último
                         precio y costo (la base no tiene precio de catálogo).
"""

from datetime import date, timedelta

from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    DateField,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Cast
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cliente, CuentaPorCobrar, DetalleVenta, GastoInsumo, Producto, Venta
from .views import StandardResultsSetPagination, _rango_opcional, _tipo_compra_o_400

VENTA, GASTO = "VENTA", "GASTO"
TIPOS = {"VENTA": VENTA, "VENTAS": VENTA, "GASTO": GASTO, "GASTOS": GASTO, "COMPRA": GASTO, "COMPRAS": GASTO}
ESTADOS = {"PAGADO": "PAGADO", "PAGADA": "PAGADO", "PENDIENTE": "PENDIENTE", "PENDIENTES": "PENDIENTE"}
ORDENES = ("fecha", "monto")
COLUMNAS = (
    "tipo", "id", "fecha", "detalle", "monto", "items_count", "tipo_compra", "por_cobrar", "estado_pago",
    "fecha_vencimiento", "id_cliente", "id_producto",
)


def _texto(valor):
    return Value(valor, output_field=CharField())


def _rango_fechas(params):
    """?mes=AAAA-MM o bien fecha_inicio / fecha_fin."""
    mes = (params.get("mes") or "").strip()
    if mes:
        try:
            anio, numero = (int(parte) for parte in mes.split("-"))
            inicio = date(anio, numero, 1)
        except ValueError:
            raise ValidationError({"error": "'mes' debe tener la forma AAAA-MM (ej. 2022-08)."})
        siguiente = date(anio + numero // 12, numero % 12 + 1, 1)
        return inicio, siguiente - timedelta(days=1)
    return _rango_opcional(params)


PENDIENTE = Q(por_cobrar=True) & (
    Q(cuenta_por_cobrar__isnull=True) | ~Q(cuenta_por_cobrar__estado=CuentaPorCobrar.PAGADA)
)


def _ventas_filtradas(inicio, fin, tipo_compra, estado, buscar):
    qs = Venta.objects.order_by()
    if inicio:
        qs = qs.filter(fecha__gte=inicio)
    if fin:
        qs = qs.filter(fecha__lte=fin)
    if tipo_compra:
        qs = qs.filter(tipo_compra=tipo_compra)
    if estado == "PENDIENTE":
        qs = qs.filter(PENDIENTE)
    elif estado == "PAGADO":
        qs = qs.exclude(PENDIENTE)
    if buscar:
        con_producto = DetalleVenta.objects.order_by().filter(
            venta=OuterRef("pk"), producto__producto__icontains=buscar
        )
        qs = qs.filter(
            Q(id_factura__icontains=buscar) | Q(cliente__nombre__icontains=buscar) | Exists(con_producto)
        )
    return qs


def _ventas_como_operaciones(qs):
    return qs.annotate(
        tipo=_texto(VENTA),
        id=F("id_factura"),
        detalle=F("cliente__nombre"),
        monto=Sum(F("detalles__cantidad") * F("detalles__precio_venta")),
        items_count=Count("detalles"),
        estado_pago=Case(When(PENDIENTE, then=_texto("PENDIENTE")), default=_texto("PAGADO")),
        fecha_vencimiento=F("cuenta_por_cobrar__fecha_vencimiento"),
        id_cliente=F("cliente_id"),
        id_producto=Value(None, output_field=CharField()),
    ).values(*COLUMNAS)


def _gastos(inicio, fin, buscar):
    qs = GastoInsumo.objects.order_by()
    if inicio:
        qs = qs.filter(fecha__gte=inicio)
    if fin:
        qs = qs.filter(fecha__lte=fin)
    if buscar:
        qs = qs.filter(Q(producto__producto__icontains=buscar) | Q(producto__id_producto__icontains=buscar))
    return qs.annotate(
        tipo=_texto(GASTO),
        id=Cast("id_gasto", CharField()),
        detalle=F("producto__producto"),
        items_count=Value(1, output_field=IntegerField()),
        tipo_compra=Value(None, output_field=CharField()),
        por_cobrar=Value(False, output_field=BooleanField()),
        estado_pago=_texto("PAGADO"),
        fecha_vencimiento=Value(None, output_field=DateField()),
        id_cliente=Value(None, output_field=IntegerField()),
        id_producto=F("producto_id"),
    ).values(*COLUMNAS)


class OperacionesView(generics.GenericAPIView):
    """
    GET /api/finanzas/operaciones/
    Ventas (tabla venta, una fila por factura) y gastos (tabla gastos_insumo) en una
    sola lista ordenada por fecha.

    Parámetros opcionales:
      - tipo: venta o gasto (omitir = ambos).
      - mes: AAAA-MM. O bien fecha_inicio y fecha_fin.
      - estado: pendiente (ventas al fiado sin pagar) o pagado.
      - tipo_compra: Física o En Línea (solo aplica a ventas).
      - search: busca en N° de factura, cliente y producto.
      - ordering: -fecha (por defecto), fecha, monto, -monto.
      - page, page_size: paginación.
    El bloque "resumen" trae cantidad y monto de ventas, gastos y ventas pendientes.
    """

    pagination_class = StandardResultsSetPagination

    def get(self, request):
        params = request.query_params
        inicio, fin = _rango_fechas(params)
        tipo_compra = _tipo_compra_o_400(params)
        buscar = (params.get("search") or "").strip()

        tipo = (params.get("tipo") or "").strip().upper()
        if tipo and tipo not in TIPOS:
            raise ValidationError({"error": "'tipo' inválido. Usa: venta o gasto."})
        tipo = TIPOS.get(tipo)
        estado = (params.get("estado") or "").strip().upper()
        if estado and estado not in ESTADOS:
            raise ValidationError({"error": "'estado' inválido. Usa: pendiente o pagado."})
        estado = ESTADOS.get(estado)
        orden = (params.get("ordering") or "-fecha").strip()
        if orden.lstrip("-") not in ORDENES:
            raise ValidationError({"error": "'ordering' inválido. Usa: fecha, -fecha, monto o -monto."})

        ventas_base = _ventas_filtradas(inicio, fin, tipo_compra, estado, buscar)
        ventas = _ventas_como_operaciones(ventas_base)
        gastos = _gastos(inicio, fin, buscar)
        incluir_ventas = tipo in (None, VENTA)
        incluir_gastos = tipo in (None, GASTO) and not tipo_compra and estado != "PENDIENTE"

        if incluir_ventas and incluir_gastos:
            lista = ventas.union(gastos, all=True)
        elif incluir_ventas:
            lista = ventas
        elif incluir_gastos:
            lista = gastos
        else:
            lista = ventas.none()
        lista = lista.order_by(orden, "-tipo", "-id")

        pagina = self.paginate_queryset(lista)
        respuesta = self.get_paginated_response(list(pagina))
        respuesta.data["resumen"] = self._resumen(
            ventas_base if incluir_ventas else None, gastos if incluir_gastos else None
        )
        return respuesta

    def _resumen(self, ventas, gastos):
        """Totales de todo lo filtrado (no solo de la página), calculados por la base de datos."""
        def de_ventas(qs):
            if qs is None:
                return {"cantidad": 0, "monto": 0}
            monto = DetalleVenta.objects.order_by().filter(venta__in=qs.values("pk")).aggregate(
                total=Sum(F("cantidad") * F("precio_venta"))
            )["total"]
            return {"cantidad": qs.count(), "monto": monto or 0}

        g = gastos.aggregate(cantidad=Count("pk"), total=Sum("monto")) if gastos is not None else {}
        return {
            "ventas": de_ventas(ventas),
            "gastos": {"cantidad": g.get("cantidad") or 0, "monto": g.get("total") or 0},
            "ventas_pendientes": de_ventas(ventas.filter(PENDIENTE) if ventas is not None else None),
        }


def _limite(params):
    limite = (params.get("limit") or "20").strip()
    if not limite.isdigit() or not 1 <= int(limite) <= 100:
        raise ValidationError({"error": "'limit' debe ser un número entre 1 y 100."})
    return int(limite)


class OpcionesClientesView(APIView):
    """
    GET /api/finanzas/opciones/clientes/?search=texto&limit=20
    Para el selector de cliente: solo id_cliente, nombre y contacto (sin totales, es rápido).
    """

    def get(self, request):
        buscar = (request.query_params.get("search") or "").strip()
        qs = Cliente.objects.order_by("nombre", "id_cliente")
        if buscar:
            q = Q(nombre__icontains=buscar) | Q(contacto__icontains=buscar)
            if buscar.isdigit():
                q |= Q(id_cliente=int(buscar))
            qs = qs.filter(q)
        filas = qs.values("id_cliente", "nombre", "contacto")[: _limite(request.query_params)]
        return Response({"results": list(filas)})


class OpcionesProductosView(APIView):
    """
    GET /api/finanzas/opciones/productos/?search=texto&limit=20
    Para el selector de producto: id_producto, producto, categoria y el precio y costo
    unitarios de su última venta (null si nunca se ha vendido). Son los mismos valores
    que usa la API cuando una venta nueva no trae precio.
    """

    def get(self, request):
        buscar = (request.query_params.get("search") or "").strip()
        ultima = DetalleVenta.objects.order_by().filter(producto=OuterRef("pk")).order_by(
            "-venta__fecha", "-id_detalle"
        )
        qs = Producto.objects.order_by("producto", "id_producto")
        if buscar:
            qs = qs.filter(Q(producto__icontains=buscar) | Q(id_producto__icontains=buscar))
        categoria = (request.query_params.get("categoria") or "").strip()
        if categoria:
            qs = qs.filter(categoria__iexact=categoria)
        ids = list(qs.values_list("pk", flat=True)[: _limite(request.query_params)])
        filas = (
            Producto.objects.filter(pk__in=ids)
            .order_by("producto", "id_producto")
            .annotate(
                ultimo_precio_venta=Subquery(ultima.values("precio_venta")[:1]),
                ultimo_costo_venta=Subquery(ultima.values("costo_venta")[:1]),
            )
            .values("id_producto", "producto", "categoria", "ultimo_precio_venta", "ultimo_costo_venta")
        )
        return Response({"results": list(filas)})
