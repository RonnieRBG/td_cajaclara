from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd
from django.db.models import (
    Count,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    Q,
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncQuarter, TruncWeek, TruncYear
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import flujo_caja
from .models import (
    ESTADO_PAGO_CHOICES,
    Cliente,
    CuentaPorCobrar,
    DetalleVenta,
    GastoInsumo,
    Producto,
    Venta,
)
from .serializers import (
    ClienteSerializer,
    CuentaPorCobrarSerializer,
    DetalleVentaSerializer,
    GastoInsumoSerializer,
    ProductoSerializer,
    VentaSerializer,
    normalizar_tipo_compra,
)

FORMATO_FECHA = "%d/%m/%Y"
FORMATOS_ENTRADA = ("%d/%m/%Y", "%Y-%m-%d")
PERIODOS_VALIDOS = ("mensual", "trimestral", "anual")
TIPOS_COMPRA_VALIDOS = [codigo for codigo, _ in Venta.TIPO_COMPRA_CHOICES]
NOMBRES_ESTADO_PAGO = dict(ESTADO_PAGO_CHOICES)
ESTADOS_CUENTA_VALIDOS = [codigo for codigo, _ in CuentaPorCobrar.ESTADO_CHOICES]
VALORES_VERDADEROS = ("true", "1", "si", "sí")

# Función de la base de datos con la que se agrupa cada opción. "semanas_mes" agrupa por
# día y luego se juntan los días en las semanas del mes (1-7, 8-14, 15-21 y 22 a fin de mes).
AGRUPACIONES = {
    "diaria": TruncDay,
    "semanal": TruncWeek,
    "semanas_mes": TruncDay,
    "mensual": TruncMonth,
    "trimestral": TruncQuarter,
    "anual": TruncYear,
}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MAX_PERIODOS = 400


class FiltroInvalido(Exception):
    pass


@dataclass
class Filtros:
    fecha_inicio: date
    fecha_fin: date
    periodo: str
    tipo_compra: str | None
    q: Q


def _hoy():
    return timezone.localdate()


def _a_fecha(valor):
    if isinstance(valor, datetime):
        return valor.date()
    return valor


def _monto(valor):
    """Montos en pesos chilenos: enteros."""
    return int(valor or 0)


def _margen(ingresos, utilidad):
    return round(utilidad / ingresos * 100, 2) if ingresos else 0.0


def _parsear_fecha(texto, nombre_param):
    for formato in FORMATOS_ENTRADA:
        try:
            return datetime.strptime(texto.strip(), formato).date()
        except ValueError:
            continue
    raise FiltroInvalido(f"'{nombre_param}' tiene un formato inválido. Usa DD/MM/AAAA.")


def _q_rango(fecha_inicio, fecha_fin, campo="venta__fecha"):
    """Rango de días [fecha_inicio, fecha_fin], ambos incluidos.
    Por defecto filtra líneas de venta por la fecha de su venta."""
    return Q(**{f"{campo}__gte": fecha_inicio, f"{campo}__lte": fecha_fin})


def _leer_tipo_compra(params):
    tipo_param = params.get("tipo_compra")
    if not tipo_param:
        return None
    tipo_compra = normalizar_tipo_compra(tipo_param)
    if tipo_compra is None:
        raise FiltroInvalido(f"'tipo_compra' inválido. Usa: {', '.join(TIPOS_COMPRA_VALIDOS)}.")
    return tipo_compra


def _armar_filtros(fecha_inicio, fecha_fin, periodo, tipo_compra):
    q = _q_rango(fecha_inicio, fecha_fin)
    if tipo_compra:
        q &= Q(venta__tipo_compra=tipo_compra)
    return Filtros(fecha_inicio, fecha_fin, periodo, tipo_compra, q)


def _obtener_filtros(request):
    params = request.query_params
    periodo = (params.get("periodo") or "").strip().lower()
    inicio_param = params.get("fecha_inicio")
    fin_param = params.get("fecha_fin")
    hoy = _hoy()

    if inicio_param or fin_param:
        if not (inicio_param and fin_param):
            raise FiltroInvalido("Envía 'fecha_inicio' y 'fecha_fin' juntas.")
        fecha_inicio = _parsear_fecha(inicio_param, "fecha_inicio")
        fecha_fin = _parsear_fecha(fin_param, "fecha_fin")
        if fecha_inicio > fecha_fin:
            raise FiltroInvalido("'fecha_inicio' no puede ser posterior a 'fecha_fin'.")
        periodo_aplicado = "personalizado"
    else:
        periodo_aplicado = periodo or "mensual"
        if periodo_aplicado == "mensual":
            fecha_inicio = hoy.replace(day=1)
        elif periodo_aplicado == "trimestral":
            fecha_inicio = date(hoy.year, 3 * ((hoy.month - 1) // 3) + 1, 1)
        elif periodo_aplicado == "anual":
            fecha_inicio = date(hoy.year, 1, 1)
        else:
            raise FiltroInvalido(f"'periodo' inválido. Usa: {', '.join(PERIODOS_VALIDOS)}.")
        fecha_fin = hoy

    return _armar_filtros(fecha_inicio, fecha_fin, periodo_aplicado, _leer_tipo_compra(params))


def _sumar_meses(dia, meses):
    anios, mes = divmod(dia.month - 1 + meses, 12)
    return date(dia.year + anios, mes + 1, 1)


def _inicio_periodo(dia, agrupacion):
    if agrupacion == "diaria":
        return dia
    if agrupacion == "semanal":  # semana de lunes a domingo
        return dia - timedelta(days=dia.weekday())
    if agrupacion == "semanas_mes":  # semanas del mes: días 1, 8, 15 y 22
        return dia.replace(day=min((dia.day - 1) // 7, 3) * 7 + 1)
    if agrupacion == "mensual":
        return dia.replace(day=1)
    if agrupacion == "trimestral":
        return date(dia.year, 3 * ((dia.month - 1) // 3) + 1, 1)
    return date(dia.year, 1, 1)


def _siguiente_periodo(inicio, agrupacion):
    if agrupacion == "diaria":
        return inicio + timedelta(days=1)
    if agrupacion == "semanal":
        return inicio + timedelta(days=7)
    if agrupacion == "semanas_mes":
        # la 4ª semana (desde el día 22) llega hasta fin de mes
        return _sumar_meses(inicio, 1) if inicio.day == 22 else inicio + timedelta(days=7)
    if agrupacion == "mensual":
        return _sumar_meses(inicio, 1)
    if agrupacion == "trimestral":
        return _sumar_meses(inicio, 3)
    return date(inicio.year + 1, 1, 1)


def _etiqueta(inicio, agrupacion):
    if agrupacion == "diaria":
        return inicio.strftime(FORMATO_FECHA)
    if agrupacion == "semanal":
        return f"Sem {inicio.isocalendar().week} {inicio.isocalendar().year}"
    if agrupacion == "semanas_mes":
        return f"Sem {(inicio.day - 1) // 7 + 1} {MESES[inicio.month - 1]} {inicio.year}"
    if agrupacion == "mensual":
        return f"{MESES[inicio.month - 1]} {inicio.year}"
    if agrupacion == "trimestral":
        return f"T{(inicio.month - 1) // 3 + 1} {inicio.year}"
    return str(inicio.year)


def _rango_corto(desde, hasta):
    """'05 Nov', '01 - 07 Oct' o '29 Sep - 05 Oct'."""
    if desde == hasta:
        return f"{desde:%d} {MESES[desde.month - 1]}"
    if (desde.year, desde.month) == (hasta.year, hasta.month):
        return f"{desde:%d} - {hasta:%d} {MESES[hasta.month - 1]}"
    return f"{desde:%d} {MESES[desde.month - 1]} - {hasta:%d} {MESES[hasta.month - 1]}"


def _resumen(transacciones, ingresos, costos):
    ingresos = ingresos or 0
    costos = costos or 0
    utilidad = ingresos - costos
    return {
        "total_transacciones": transacciones,
        "total_ingresos": _monto(ingresos),
        "total_costos": _monto(costos),
        "utilidad": _monto(utilidad),
        "margen_porcentaje": _margen(ingresos, utilidad),
    }


class ResumenFinancieroView(APIView):
    def get(self, request):
        try:
            filtros = _obtener_filtros(request)
        except FiltroInvalido as error:
            return Response({"error": str(error)}, status=400)

        ventas = DetalleVenta.objects.filter(filtros.q).con_totales().con_estado_pago().order_by()
        totales = ventas.aggregate(
            transacciones=Count("pk"),
            unidades=Sum("cantidad"),
            ingresos=Sum("total_venta"),
            costos=Sum("total_costo"),
        )
        flujo = flujo_caja.calcular(filtros.fecha_inicio, filtros.fecha_fin, filtros.tipo_compra)
        ingresos = totales["ingresos"] or 0
        costos = totales["costos"] or 0
        utilidad = ingresos - costos

        por_estado = {
            codigo: {"nombre": nombre, "transacciones": 0, "ingresos": 0}
            for codigo, nombre in NOMBRES_ESTADO_PAGO.items()
        }
        for fila in ventas.values("estado_pago").annotate(
            transacciones=Count("pk"), ingresos=Sum("total_venta")
        ):
            por_estado[fila["estado_pago"]].update(
                transacciones=fila["transacciones"], ingresos=_monto(fila["ingresos"])
            )

        return Response({
            "rango_aplicado": {
                "fecha_inicio": filtros.fecha_inicio.strftime(FORMATO_FECHA),
                "fecha_fin": filtros.fecha_fin.strftime(FORMATO_FECHA),
                "periodo_tipo": filtros.periodo,
            },
            "filtro_tipo_compra": filtros.tipo_compra or "TODOS",
            "total_transacciones": totales["transacciones"],
            "total_unidades": totales["unidades"] or 0,
            # Ventas del período (al contado y a crédito) y su costo de mercadería
            "total_ingresos": _monto(ingresos),
            "total_costos": _monto(costos),
            "utilidad_bruta": _monto(utilidad),
            "margen_porcentaje": _margen(ingresos, utilidad),
            "por_estado_pago": por_estado,
            # Dinero que realmente entró y salió (ver finanzas/flujo_caja.py)
            "flujo_caja": flujo_caja.a_json(flujo),
        })


class ResumenAgrupadoView(APIView):
    def get(self, request):
        params = request.query_params
        try:
            inicio_param = params.get("fecha_inicio")
            if not inicio_param:
                raise FiltroInvalido("'fecha_inicio' es obligatoria.")
            fecha_inicio = _parsear_fecha(inicio_param, "fecha_inicio")
            fin_param = params.get("fecha_fin")
            fecha_fin = _parsear_fecha(fin_param, "fecha_fin") if fin_param else _hoy()
            if fecha_inicio > fecha_fin:
                raise FiltroInvalido("'fecha_inicio' no puede ser posterior a 'fecha_fin'.")

            agrupacion = (params.get("agrupacion") or "mensual").strip().lower()
            if agrupacion not in AGRUPACIONES:
                raise FiltroInvalido(f"'agrupacion' inválida. Usa: {', '.join(AGRUPACIONES)}.")

            periodos = []
            inicio = _inicio_periodo(fecha_inicio, agrupacion)
            while inicio <= fecha_fin:
                periodos.append(inicio)
                inicio = _siguiente_periodo(inicio, agrupacion)
            if len(periodos) > MAX_PERIODOS:
                raise FiltroInvalido(
                    f"El rango genera {len(periodos)} periodos (máximo {MAX_PERIODOS}). "
                    "Usa una agrupación más amplia o un rango más corto."
                )

            filtros = _armar_filtros(fecha_inicio, fecha_fin, agrupacion, _leer_tipo_compra(params))
        except FiltroInvalido as error:
            return Response({"error": str(error)}, status=400)

        filas = (
            DetalleVenta.objects.filter(filtros.q)
            .con_totales()
            .order_by()
            .annotate(grupo=AGRUPACIONES[agrupacion]("venta__fecha"))
            .values("grupo")
            .annotate(
                transacciones=Count("pk"),
                ingresos=Sum("total_venta"),
                costos=Sum("total_costo"),
            )
        )
        # Varias filas pueden caer en el mismo período (ej.: los días de una semana del mes)
        por_grupo = {}
        for f in filas:
            clave = _inicio_periodo(_a_fecha(f["grupo"]), agrupacion)
            acumulado = por_grupo.setdefault(clave, {"transacciones": 0, "ingresos": 0, "costos": 0})
            acumulado["transacciones"] += f["transacciones"]
            acumulado["ingresos"] += f["ingresos"] or 0
            acumulado["costos"] += f["costos"] or 0
        flujo_por_periodo = flujo_caja.calcular(
            fecha_inicio,
            fecha_fin,
            filtros.tipo_compra,
            trunc=AGRUPACIONES[agrupacion],
            a_clave=lambda dia: _inicio_periodo(_a_fecha(dia), agrupacion),
        )

        resultado = []
        total_transacciones, total_ingresos, total_costos = 0, 0, 0
        for inicio in periodos:
            fila = por_grupo.get(inicio, {})
            transacciones = fila.get("transacciones", 0)
            ingresos = fila.get("ingresos") or 0
            costos = fila.get("costos") or 0
            total_transacciones += transacciones
            total_ingresos += ingresos
            total_costos += costos

            desde = max(inicio, fecha_inicio)
            hasta = min(_siguiente_periodo(inicio, agrupacion) - timedelta(days=1), fecha_fin)
            resultado.append({
                "periodo": _etiqueta(inicio, agrupacion),
                "fecha_inicio": desde.strftime(FORMATO_FECHA),
                "fecha_fin": hasta.strftime(FORMATO_FECHA),
                # Texto corto para el gráfico, ej.: "01 - 07 Oct"
                "rango": _rango_corto(desde, hasta),
                **_resumen(transacciones, ingresos, costos),
                "flujo_caja": flujo_caja.a_json(flujo_por_periodo.get(inicio, flujo_caja.vacio())),
            })

        return Response({
            "rango_aplicado": {
                "fecha_inicio": fecha_inicio.strftime(FORMATO_FECHA),
                "fecha_fin": fecha_fin.strftime(FORMATO_FECHA),
            },
            "agrupacion": agrupacion,
            "filtro_tipo_compra": filtros.tipo_compra or "TODOS",
            "totales": {
                **_resumen(total_transacciones, total_ingresos, total_costos),
                "flujo_caja": flujo_caja.a_json(
                    flujo_caja.calcular(fecha_inicio, fecha_fin, filtros.tipo_compra)
                ),
            },
            "periodos": resultado,
        })


class ExportarExcelView(APIView):
    COLUMNAS = [
        "ID Detalle", "Fecha", "Factura", "ID Producto", "Nombre Producto",
        "Tipo Compra", "Cantidad", "Precio Venta Unitario", "Costo Venta Unitario",
        "Total Venta", "Total Costo", "Utilidad", "Estado Pago",
    ]
    COLUMNAS_DINERO = [
        "Precio Venta Unitario", "Costo Venta Unitario", "Total Venta", "Total Costo", "Utilidad",
    ]

    def get(self, request):
        try:
            filtros = _obtener_filtros(request)
        except FiltroInvalido as error:
            return Response({"error": str(error)}, status=400)

        filas = (
            DetalleVenta.objects.filter(filtros.q)
            .con_totales()
            .con_estado_pago()
            .order_by("venta__fecha", "venta_id", "id_detalle")
            .values(
                "id_detalle", "venta__fecha", "venta_id", "producto_id", "producto__producto",
                "venta__tipo_compra", "cantidad", "precio_venta", "costo_venta",
                "total_venta", "total_costo", "utilidad", "estado_pago",
            )
        )

        datos = [
            {
                "ID Detalle": f["id_detalle"],
                "Fecha": f["venta__fecha"],
                "Factura": f["venta_id"],
                "ID Producto": f["producto_id"],
                "Nombre Producto": f["producto__producto"],
                "Tipo Compra": f["venta__tipo_compra"],
                "Cantidad": f["cantidad"],
                "Precio Venta Unitario": _monto(f["precio_venta"]),
                "Costo Venta Unitario": _monto(f["costo_venta"]),
                "Total Venta": _monto(f["total_venta"]),
                "Total Costo": _monto(f["total_costo"]),
                "Utilidad": _monto(f["utilidad"]),
                "Estado Pago": NOMBRES_ESTADO_PAGO.get(f["estado_pago"], f["estado_pago"]),
            }
            for f in filas.iterator()
        ]
        df = pd.DataFrame(datos, columns=self.COLUMNAS)

        nombre = f"reporte_ventas_{filtros.fecha_inicio:%d-%m-%Y}_al_{filtros.fecha_fin:%d-%m-%Y}.xlsx"
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{nombre}"'

        with pd.ExcelWriter(
            response, engine="openpyxl", date_format="DD/MM/YYYY", datetime_format="DD/MM/YYYY"
        ) as writer:
            df.to_excel(writer, sheet_name="Detalle Ventas", index=False)
            self._dar_formato(writer.sheets["Detalle Ventas"], df)

        return response

    def _dar_formato(self, hoja, df):
        for indice, columna in enumerate(df.columns, start=1):
            formato = None
            if columna == "Fecha":
                formato = "DD/MM/YYYY"
            elif columna in self.COLUMNAS_DINERO:
                formato = "#,##0"
            if formato:
                for (celda,) in hoja.iter_rows(min_row=2, min_col=indice, max_col=indice):
                    celda.number_format = formato
            largo = max([len(columna)] + [len(str(v)) for v in df[columna].head(500)])
            letra = hoja.cell(row=1, column=indice).column_letter
            hoja.column_dimensions[letra].width = min(largo + 2, 45)

        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions


# ==============================================================================
# PAGINACIÓN Y ENDPOINTS REST PARA EL EQUIPO DE FRONTEND
# ==============================================================================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500




def _rango_opcional(params):
    """fecha_inicio y fecha_fin opcionales (cada una por separado). Error 400 si el formato es inválido."""
    try:
        inicio = _parsear_fecha(params["fecha_inicio"], "fecha_inicio") if params.get("fecha_inicio") else None
        fin = _parsear_fecha(params["fecha_fin"], "fecha_fin") if params.get("fecha_fin") else None
    except FiltroInvalido as error:
        raise ValidationError({"error": str(error)})
    return inicio, fin


def _tipo_compra_o_400(params):
    try:
        return _leer_tipo_compra(params)
    except FiltroInvalido as error:
        raise ValidationError({"error": str(error)})


class ClienteListView(generics.ListAPIView):
    """
    GET /api/finanzas/clientes/
    Parámetros de consulta opcionales:
      - search: Filtra por nombre, ID o teléfono de contacto.
      - page: Número de página (default: 1).
      - page_size: Registros por página (default: 50, máx: 500).
    """
    serializer_class = ClienteSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # Cada total se calcula en su propia subconsulta. Si se hacen dos JOIN
        # (ventas y cuentas) en la misma consulta, las filas se multiplican y
        # la deuda sale inflada (deuda real × número de ventas del cliente).
        ventas_del_cliente = (
            Venta.objects.filter(cliente=OuterRef("pk"))
            .order_by()
            .values("cliente")
            .annotate(total=Count("pk"))
            .values("total")
        )
        deuda_del_cliente = (
            CuentaPorCobrar.objects.abiertas()
            .filter(cliente=OuterRef("pk"))
            .order_by()
            .values("cliente")
            .annotate(total=Sum("monto"))
            .values("total")
        )
        qs = Cliente.objects.annotate(
            total_facturas=Coalesce(Subquery(ventas_del_cliente, output_field=IntegerField()), 0),
            total_deuda=Coalesce(Subquery(deuda_del_cliente, output_field=IntegerField()), 0),
        ).order_by("nombre", "id_cliente")

        search = self.request.query_params.get("search")
        if search:
            search = search.strip()
            q = Q(nombre__icontains=search) | Q(contacto__icontains=search)
            if search.isdigit():
                q |= Q(id_cliente=int(search))
            qs = qs.filter(q)
        return qs


ORDEN_PRODUCTOS = ("producto", "total_vendido", "total_ingresos", "id_producto")


class ProductoListView(generics.ListAPIView):
    """
    GET /api/finanzas/productos/
    Parámetros de consulta opcionales:
      - search: Filtra por nombre o id_producto.
      - categoria: Filtra por categoría exacta (ej: Abarrotes, Limpieza).
      - unidad_negocio: Filtra por unidad de negocio.
      - fecha_inicio, fecha_fin: período para calcular total_vendido y total_ingresos
        (sin fechas = todas las ventas).
      - tipo_compra: Física o En Línea (para los mismos totales).
      - ordering: producto (por defecto), total_vendido, total_ingresos o id_producto;
        con "-" adelante es de mayor a menor. Productos más vendidos: ?ordering=-total_vendido
      - page, page_size: Paginación.
    """
    serializer_class = ProductoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        params = self.request.query_params

        # Ventas que cuentan para los totales de cada producto
        cuenta = Q()
        fecha_ini, fecha_fin = _rango_opcional(params)
        if fecha_ini:
            cuenta &= Q(ventas__venta__fecha__gte=fecha_ini)
        if fecha_fin:
            cuenta &= Q(ventas__venta__fecha__lte=fecha_fin)
        tipo_compra = _tipo_compra_o_400(params)
        if tipo_compra:
            cuenta &= Q(ventas__venta__tipo_compra=tipo_compra)

        qs = Producto.objects.annotate(
            total_vendido=Coalesce(Sum("ventas__cantidad", filter=cuenta), 0),
            total_ingresos=Coalesce(
                Sum(F("ventas__cantidad") * F("ventas__precio_venta"), filter=cuenta), 0
            ),
        )

        search = params.get("search")
        if search:
            search = search.strip()
            qs = qs.filter(Q(producto__icontains=search) | Q(id_producto__icontains=search))

        categoria = params.get("categoria")
        if categoria:
            qs = qs.filter(categoria__iexact=categoria.strip())

        unidad = params.get("unidad_negocio")
        if unidad:
            qs = qs.filter(unidad_negocio__iexact=unidad.strip())

        orden = (params.get("ordering") or "producto").strip()
        if orden.lstrip("-") not in ORDEN_PRODUCTOS:
            raise ValidationError(
                {"error": f"'ordering' inválido. Usa: {', '.join(ORDEN_PRODUCTOS)} (con '-' para mayor a menor)."}
            )
        return qs.order_by(orden, "id_producto")


class VentaListView(generics.ListAPIView):
    """
    GET /api/finanzas/facturas/
    Parámetros de consulta opcionales:
      - cliente: id_cliente.
      - tipo_compra: Física o En Línea.
      - por_cobrar: true o false.
      - fecha_inicio, fecha_fin: Formato DD/MM/AAAA o AAAA-MM-DD.
      - page, page_size: Paginación.
    """
    serializer_class = VentaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = (
            Venta.objects.select_related("cliente", "cuenta_por_cobrar")
            .annotate(
                total_venta=Sum(F("detalles__cantidad") * F("detalles__precio_venta")),
                items_count=Count("detalles"),
            )
            .order_by("-fecha", "-id_factura")
        )
        params = self.request.query_params

        cliente = params.get("cliente")
        if cliente:
            if not cliente.strip().isdigit():
                raise ValidationError({"error": "'cliente' debe ser un id_cliente numérico."})
            qs = qs.filter(cliente_id=int(cliente))

        tipo_compra = _tipo_compra_o_400(params)
        if tipo_compra:
            qs = qs.filter(tipo_compra=tipo_compra)

        por_cobrar = params.get("por_cobrar")
        if por_cobrar is not None and por_cobrar != "":
            qs = qs.filter(por_cobrar=por_cobrar.strip().lower() in VALORES_VERDADEROS)

        fecha_ini, fecha_fin = _rango_opcional(params)
        if fecha_ini:
            qs = qs.filter(fecha__gte=fecha_ini)
        if fecha_fin:
            qs = qs.filter(fecha__lte=fecha_fin)
        return qs


class DetalleVentaListView(generics.ListAPIView):
    """
    GET /api/finanzas/ventas/
    Parámetros de consulta opcionales:
      - factura: id_factura.
      - producto: id_producto.
      - tipo_compra: Física o En Línea.
      - estado_pago: PAGADO o PENDIENTE (se calcula desde la venta y su cuenta por cobrar).
      - page, page_size: Paginación.
    """
    serializer_class = DetalleVentaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = DetalleVenta.objects.con_estado_pago().order_by("-venta__fecha", "-id_detalle")
        params = self.request.query_params

        factura = params.get("factura")
        if factura:
            qs = qs.filter(venta_id=factura.strip())

        producto = params.get("producto")
        if producto:
            qs = qs.filter(producto_id=producto.strip())

        estado_pago = params.get("estado_pago")
        if estado_pago:
            qs = qs.filter(estado_pago=estado_pago.strip().upper())

        tipo_compra = _tipo_compra_o_400(params)
        if tipo_compra:
            qs = qs.filter(venta__tipo_compra=tipo_compra)
        return qs


class CuentaPorCobrarListView(generics.ListAPIView):
    """
    GET /api/finanzas/cuentas-por-cobrar/
    Parámetros de consulta opcionales:
      - cliente: id_cliente.
      - factura: id_factura.
      - estado: PENDIENTE (aún no vence), VENCIDA o PAGADA (estado a la fecha de hoy).
      - vencidas: true para solo vencidas, false para todas menos las vencidas.
      - page, page_size: Paginación.
    El bloque "resumen" trae el total por cobrar (pendientes + vencidas) y el detalle por estado.
    """
    serializer_class = CuentaPorCobrarSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = (
            CuentaPorCobrar.objects.con_estado_actual()
            .select_related("cliente", "venta")
            .order_by("fecha_vencimiento", "id_cuenta")
        )
        params = self.request.query_params

        cliente = params.get("cliente")
        if cliente:
            if not cliente.strip().isdigit():
                raise ValidationError({"error": "'cliente' debe ser un id_cliente numérico."})
            qs = qs.filter(cliente_id=int(cliente))

        factura = params.get("factura")
        if factura:
            qs = qs.filter(venta_id=factura.strip())

        estado = params.get("estado")
        if estado:
            estado = estado.strip().upper()
            if estado not in ESTADOS_CUENTA_VALIDOS:
                raise ValidationError({"error": f"'estado' inválido. Usa: {', '.join(ESTADOS_CUENTA_VALIDOS)}."})
            qs = qs.filter(estado_actual=estado)

        vencidas = params.get("vencidas")
        if vencidas is not None and vencidas != "":
            if vencidas.strip().lower() in VALORES_VERDADEROS:
                qs = qs.filter(estado_actual=CuentaPorCobrar.VENCIDA)
            else:
                qs = qs.exclude(estado_actual=CuentaPorCobrar.VENCIDA)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Totales para los indicadores del dashboard y de la pantalla de Cobros
        qs_filtrado = self.filter_queryset(self.get_queryset()).order_by()
        por_estado = {
            codigo: {"nombre": nombre, "cantidad": 0, "monto": 0}
            for codigo, nombre in CuentaPorCobrar.ESTADO_CHOICES
        }
        for fila in qs_filtrado.values("estado_actual").annotate(cantidad=Count("pk"), monto=Sum("monto")):
            por_estado[fila["estado_actual"]].update(cantidad=fila["cantidad"], monto=_monto(fila["monto"]))
        por_cobrar = por_estado[CuentaPorCobrar.PENDIENTE]["monto"] + por_estado[CuentaPorCobrar.VENCIDA]["monto"]
        response.data["resumen"] = {
            "total_cuentas": sum(e["cantidad"] for e in por_estado.values()),
            "monto_total_por_cobrar": por_cobrar,
            "por_estado": por_estado,
        }
        return response


class GastoInsumoListView(generics.ListAPIView):
    """
    GET /api/finanzas/gastos/
    Parámetros de consulta opcionales:
      - producto: id_producto.
      - categoria: categoría del producto comprado (ej: Abarrotes).
      - fecha_inicio, fecha_fin: Rango de fechas.
      - page, page_size: Paginación.
    """
    serializer_class = GastoInsumoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = GastoInsumo.objects.select_related("producto").order_by("-fecha", "-id_gasto")
        params = self.request.query_params

        categoria = params.get("categoria")
        if categoria:
            qs = qs.filter(producto__categoria__iexact=categoria.strip())

        producto = params.get("producto")
        if producto:
            qs = qs.filter(producto_id=producto.strip())

        fecha_ini, fecha_fin = _rango_opcional(params)
        if fecha_ini:
            qs = qs.filter(fecha__gte=fecha_ini)
        if fecha_fin:
            qs = qs.filter(fecha__lte=fecha_fin)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        qs_filtrado = self.filter_queryset(self.get_queryset()).order_by()
        totales = qs_filtrado.aggregate(cantidad=Count("pk"), monto=Sum("monto"))
        response.data["resumen"] = {
            "total_registros_gasto": totales["cantidad"],
            "monto_total_gastos": _monto(totales["monto"]),
        }
        return response


class OpcionesFiltrosView(APIView):
    """
    GET /api/finanzas/opciones-filtros/
    Devuelve listas de categorías, unidades de negocio, tipos de compra, estados y
    rango de fechas disponibles en la base de datos para que el Frontend inicialice
    selects, filtros y calendarios.
    """
    def get(self, request):
        categorias = list(Producto.objects.values_list("categoria", flat=True).distinct().order_by("categoria"))
        unidades = list(
            Producto.objects.values_list("unidad_negocio", flat=True).distinct().order_by("unidad_negocio")
        )

        def _opciones(choices):
            return [{"codigo": codigo, "nombre": nombre} for codigo, nombre in choices]

        rango = Venta.objects.aggregate(min_fecha=Min("fecha"), max_fecha=Max("fecha"))
        min_f, max_f = rango["min_fecha"], rango["max_fecha"]

        return Response({
            "categorias": [c for c in categorias if c],
            "unidades_negocio": [u for u in unidades if u],
            "tipos_compra": _opciones(Venta.TIPO_COMPRA_CHOICES),
            "estados_pago": _opciones(ESTADO_PAGO_CHOICES),
            "estados_cuenta": _opciones(CuentaPorCobrar.ESTADO_CHOICES),
            "rango_fechas_disponible": {
                "min": min_f.strftime("%Y-%m-%d") if min_f else None,
                "max": max_f.strftime("%Y-%m-%d") if max_f else None,
                "min_display": min_f.strftime(FORMATO_FECHA) if min_f else None,
                "max_display": max_f.strftime(FORMATO_FECHA) if max_f else None,
            },
        })


class ApiCatalogView(APIView):
    """
    GET /api/
    Índice de la API para los equipos de Frontend y Base de Datos.
    Es público: no requiere iniciar sesión.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        host = request.build_absolute_uri("/").rstrip("/")
        return Response({
            "nombre": "API Caja Clara - Módulo Finanzas Supermercado",
            "version": "2.0",
            "descripcion": "Endpoints REST sobre el esquema del equipo de datos (cliente, producto, venta, "
            "detalle_venta, cuenta_por_cobrar, gastos_insumo). Montos enteros en CLP.",
            "autenticacion": {
                "tipo": "JWT (Bearer)",
                "como_usar": "Inicia sesión en /api/auth/login/ y envía el token en cada consulta: "
                "'Authorization: Bearer <access>'. Todas las rutas de /api/finanzas/ lo exigen.",
                "endpoints": {
                    "login": {"url": f"{host}/api/auth/login/", "metodo": "POST", "cuerpo": ["username", "password"]},
                    "refresh": {"url": f"{host}/api/auth/refresh/", "metodo": "POST", "cuerpo": ["refresh"]},
                    "logout": {"url": f"{host}/api/auth/logout/", "metodo": "POST", "cuerpo": ["refresh"]},
                    "perfil": {"url": f"{host}/api/auth/perfil/", "metodo": "GET"},
                },
            },
            "endpoints": {
                "opciones_filtros": {
                    "url": f"{host}/api/finanzas/opciones-filtros/",
                    "metodo": "GET",
                    "descripcion": "Metadatos para llenar dropdowns: categorías, unidades, tipos y estados, y rango de fechas.",
                },
                "kpis_resumen": {
                    "url": f"{host}/api/finanzas/resumen-mensual/",
                    "metodo": "GET",
                    "descripcion": "Resumen financiero: ventas, costos, utilidad, margen %, pagos pendientes y flujo de caja (entradas, salidas, saldo).",
                    "parametros": ["periodo", "fecha_inicio", "fecha_fin", "tipo_compra"],
                },
                "serie_temporal": {
                    "url": f"{host}/api/finanzas/resumen-agrupado/",
                    "metodo": "GET",
                    "descripcion": "Datos agrupados para gráficos (diaria, semanal, semanas_mes, mensual, trimestral, anual).",
                    "parametros": ["fecha_inicio", "fecha_fin", "agrupacion", "tipo_compra"],
                },
                "exportar_excel": {
                    "url": f"{host}/api/finanzas/exportar-excel/",
                    "metodo": "GET",
                    "descripcion": "Descarga de archivo XLSX con el detalle de ventas.",
                    "parametros": ["periodo", "fecha_inicio", "fecha_fin", "tipo_compra"],
                },
                "clientes": {
                    "url": f"{host}/api/finanzas/clientes/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de clientes con conteo de facturas y deuda abierta.",
                    "parametros": ["search", "page", "page_size"],
                },
                "productos": {
                    "url": f"{host}/api/finanzas/productos/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de productos con unidades e ingresos vendidos; ?ordering=-total_vendido para los más vendidos.",
                    "parametros": ["search", "categoria", "unidad_negocio", "fecha_inicio", "fecha_fin", "tipo_compra", "ordering", "page", "page_size"],
                },
                "facturas": {
                    "url": f"{host}/api/finanzas/facturas/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de ventas (tabla venta) con total y estado de pago.",
                    "parametros": ["cliente", "tipo_compra", "por_cobrar", "fecha_inicio", "fecha_fin", "page", "page_size"],
                },
                "ventas_detalles": {
                    "url": f"{host}/api/finanzas/ventas/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de líneas de venta (tabla detalle_venta).",
                    "parametros": ["factura", "producto", "tipo_compra", "estado_pago", "page", "page_size"],
                },
                "cuentas_por_cobrar": {
                    "url": f"{host}/api/finanzas/cuentas-por-cobrar/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de cuentas por cobrar con estado (pendiente, vencida, pagada) y totales.",
                    "parametros": ["cliente", "factura", "estado", "vencidas", "page", "page_size"],
                },
                "gastos": {
                    "url": f"{host}/api/finanzas/gastos/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de gastos en insumos (tabla gastos_insumo).",
                    "parametros": ["producto", "categoria", "fecha_inicio", "fecha_fin", "page", "page_size"],
                },
                "registrar_venta": {
                    "url": f"{host}/api/finanzas/facturas/",
                    "metodo": "POST",
                    "descripcion": "Registra una venta al contado o a crédito (crea su cuenta por cobrar).",
                    "cuerpo": ["items[id_producto, cantidad, precio_venta?, costo_venta?]", "id_cliente",
                               "tipo_compra", "por_cobrar", "fecha_vencimiento", "fecha"],
                },
                "detalle_venta": {
                    "url": f"{host}/api/finanzas/facturas/<id_factura>/",
                    "metodo": "GET",
                    "descripcion": "Una venta con sus productos y su cuenta por cobrar.",
                },
                "pagar_cuenta": {
                    "url": f"{host}/api/finanzas/cuentas-por-cobrar/<id_cuenta>/pagar/",
                    "metodo": "POST",
                    "descripcion": "Registra el pago completo de una deuda.",
                    "cuerpo": ["fecha_pago?"],
                },
                "revertir_pago": {
                    "url": f"{host}/api/finanzas/cuentas-por-cobrar/<id_cuenta>/revertir-pago/",
                    "metodo": "POST",
                    "descripcion": "Deshace un pago registrado por error.",
                },
                "registrar_gasto": {
                    "url": f"{host}/api/finanzas/gastos/",
                    "metodo": "POST",
                    "descripcion": "Registra un gasto en insumos (compra de un producto).",
                    "cuerpo": ["id_producto", "monto", "fecha?"],
                },
                "registrar_cliente": {
                    "url": f"{host}/api/finanzas/clientes/",
                    "metodo": "POST",
                    "descripcion": "Registra un cliente.",
                    "cuerpo": ["nombre", "contacto"],
                },
            },
        })
