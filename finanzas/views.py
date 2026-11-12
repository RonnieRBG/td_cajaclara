from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.db.models import (
    Count,
    DecimalField,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncQuarter, TruncYear
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Cliente,
    CuentaPorCobrar,
    DetalleVenta,
    Factura,
    GastoInsumo,
    Producto,
    TipoCompra,
)
from .serializers import (
    ClienteSerializer,
    CuentaPorCobrarSerializer,
    DetalleVentaSerializer,
    FacturaSerializer,
    GastoInsumoSerializer,
    ProductoSerializer,
    TipoCompraSerializer,
)

FORMATO_FECHA = "%d/%m/%Y"
FORMATOS_ENTRADA = ("%d/%m/%Y", "%Y-%m-%d")
PERIODOS_VALIDOS = ("mensual", "trimestral", "anual")
TIPOS_COMPRA_VALIDOS = [codigo for codigo, _ in TipoCompra.TIPO_CHOICES]
NOMBRES_TIPO_COMPRA = dict(TipoCompra.TIPO_CHOICES)
NOMBRES_ESTADO_PAGO = dict(DetalleVenta.ESTADO_PAGO_CHOICES)
DOS_DECIMALES = Decimal("0.01")

AGRUPACIONES = {
    "diaria": TruncDay,
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
    return timezone.localdate() if settings.USE_TZ else date.today()


def _inicio_del_dia(dia):
    momento = datetime.combine(dia, time.min)
    return timezone.make_aware(momento) if settings.USE_TZ else momento


def _a_fecha_local(momento):
    if momento is None:
        return None
    if isinstance(momento, datetime):
        if settings.USE_TZ and timezone.is_aware(momento):
            momento = timezone.localtime(momento)
        return momento.date()
    return momento


def _monto(valor):
    return float((valor or Decimal("0")).quantize(DOS_DECIMALES))


def _margen(ingresos, utilidad):
    return _monto(utilidad / ingresos * 100) if ingresos else 0.0


def _parsear_fecha(texto, nombre_param):
    for formato in FORMATOS_ENTRADA:
        try:
            return datetime.strptime(texto.strip(), formato).date()
        except ValueError:
            continue
    raise FiltroInvalido(f"'{nombre_param}' tiene un formato inválido. Usa DD/MM/AAAA.")


def _q_rango(fecha_inicio, fecha_fin):
    return Q(fecha__gte=_inicio_del_dia(fecha_inicio)) & Q(
        fecha__lt=_inicio_del_dia(fecha_fin + timedelta(days=1))
    )


def _leer_tipo_compra(params):
    tipo_param = params.get("tipo_compra")
    if not tipo_param:
        return None
    tipo_compra = tipo_param.strip().upper()
    if tipo_compra not in TIPOS_COMPRA_VALIDOS:
        raise FiltroInvalido(f"'tipo_compra' inválido. Usa: {', '.join(TIPOS_COMPRA_VALIDOS)}.")
    return tipo_compra


def _armar_filtros(fecha_inicio, fecha_fin, periodo, tipo_compra):
    q = _q_rango(fecha_inicio, fecha_fin)
    if tipo_compra:
        q &= Q(tipo_compra_id=tipo_compra)
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
    if agrupacion == "mensual":
        return dia.replace(day=1)
    if agrupacion == "trimestral":
        return date(dia.year, 3 * ((dia.month - 1) // 3) + 1, 1)
    return date(dia.year, 1, 1)


def _siguiente_periodo(inicio, agrupacion):
    if agrupacion == "diaria":
        return inicio + timedelta(days=1)
    if agrupacion == "mensual":
        return _sumar_meses(inicio, 1)
    if agrupacion == "trimestral":
        return _sumar_meses(inicio, 3)
    return date(inicio.year + 1, 1, 1)


def _etiqueta(inicio, agrupacion):
    if agrupacion == "diaria":
        return inicio.strftime(FORMATO_FECHA)
    if agrupacion == "mensual":
        return f"{MESES[inicio.month - 1]} {inicio.year}"
    if agrupacion == "trimestral":
        return f"T{(inicio.month - 1) // 3 + 1} {inicio.year}"
    return str(inicio.year)


def _resumen(transacciones, ingresos, costos):
    ingresos = ingresos or Decimal("0")
    costos = costos or Decimal("0")
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

        ventas = DetalleVenta.objects.filter(filtros.q).con_totales().order_by()
        totales = ventas.exclude(estado_pago="ANULADO").aggregate(
            transacciones=Count("pk"),
            ingresos=Sum("total_venta"),
            costos=Sum("total_costo"),
        )
        ingresos = totales["ingresos"] or Decimal("0")
        costos = totales["costos"] or Decimal("0")
        utilidad = ingresos - costos

        por_estado = {
            codigo: {"nombre": nombre, "transacciones": 0, "ingresos": 0.0}
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
            "total_ingresos": _monto(ingresos),
            "total_costos": _monto(costos),
            "flujo_caja_neto": _monto(utilidad),
            "margen_porcentaje": _margen(ingresos, utilidad),
            "por_estado_pago": por_estado,
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
            .exclude(estado_pago="ANULADO")
            .con_totales()
            .order_by()
            .annotate(grupo=AGRUPACIONES[agrupacion]("fecha"))
            .values("grupo")
            .annotate(
                transacciones=Count("pk"),
                ingresos=Sum("total_venta"),
                costos=Sum("total_costo"),
            )
        )
        por_grupo = {_inicio_periodo(_a_fecha_local(f["grupo"]), agrupacion): f for f in filas}

        resultado = []
        total_transacciones, total_ingresos, total_costos = 0, Decimal("0"), Decimal("0")
        for inicio in periodos:
            fila = por_grupo.get(inicio, {})
            transacciones = fila.get("transacciones", 0)
            ingresos = fila.get("ingresos") or Decimal("0")
            costos = fila.get("costos") or Decimal("0")
            total_transacciones += transacciones
            total_ingresos += ingresos
            total_costos += costos

            desde = max(inicio, fecha_inicio)
            hasta = min(_siguiente_periodo(inicio, agrupacion) - timedelta(days=1), fecha_fin)
            resultado.append({
                "periodo": _etiqueta(inicio, agrupacion),
                "fecha_inicio": desde.strftime(FORMATO_FECHA),
                "fecha_fin": hasta.strftime(FORMATO_FECHA),
                **_resumen(transacciones, ingresos, costos),
            })

        return Response({
            "rango_aplicado": {
                "fecha_inicio": fecha_inicio.strftime(FORMATO_FECHA),
                "fecha_fin": fecha_fin.strftime(FORMATO_FECHA),
            },
            "agrupacion": agrupacion,
            "filtro_tipo_compra": filtros.tipo_compra or "TODOS",
            "totales": _resumen(total_transacciones, total_ingresos, total_costos),
            "periodos": resultado,
        })


class ExportarExcelView(APIView):
    COLUMNAS = [
        "ID Registro (_id)", "Fecha", "Factura", "Producto (N° Parte)", "Nombre Producto",
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
            .order_by("fecha", "factura_id")
            .values(
                "id", "fecha", "factura_id", "no_parte_id", "no_parte__producto",
                "tipo_compra_id", "cantidad", "precio_unitario", "costo_unitario",
                "total_venta", "total_costo", "utilidad", "estado_pago",
            )
        )

        datos = [
            {
                "ID Registro (_id)": f["id"],
                "Fecha": _a_fecha_local(f["fecha"]),
                "Factura": f["factura_id"],
                "Producto (N° Parte)": f["no_parte_id"],
                "Nombre Producto": f["no_parte__producto"],
                "Tipo Compra": NOMBRES_TIPO_COMPRA.get(f["tipo_compra_id"], "No asignado"),
                "Cantidad": f["cantidad"],
                "Precio Venta Unitario": _monto(f["precio_unitario"]),
                "Costo Venta Unitario": _monto(f["costo_unitario"]),
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
                formato = "#,##0.00"
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
        # (facturas y cuentas) en la misma consulta, las filas se multiplican y
        # la deuda sale inflada (deuda real × número de facturas del cliente).
        facturas_del_cliente = (
            Factura.objects.filter(cliente=OuterRef("pk"))
            .order_by()
            .values("cliente")
            .annotate(total=Count("pk"))
            .values("total")
        )
        deuda_del_cliente = (
            CuentaPorCobrar.objects.filter(cliente=OuterRef("pk"))
            .order_by()
            .values("cliente")
            .annotate(total=Sum("monto"))
            .values("total")
        )
        qs = Cliente.objects.annotate(
            total_facturas=Coalesce(Subquery(facturas_del_cliente, output_field=IntegerField()), 0),
            total_deuda=Coalesce(
                Subquery(deuda_del_cliente, output_field=DecimalField(max_digits=14, decimal_places=2)),
                Value(Decimal("0")),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        ).order_by("nombre")

        search = self.request.query_params.get("search")
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(nombre__icontains=search)
                | Q(cliente_id__icontains=search)
                | Q(contacto__icontains=search)
            )
        return qs


class ProductoListView(generics.ListAPIView):
    """
    GET /api/finanzas/productos/
    Parámetros de consulta opcionales:
      - search: Filtra por nombre o N° de parte.
      - categoria: Filtra por categoría exacta (ej: Abarrotes, Limpieza).
      - unidad_negocio: Filtra por unidad de negocio.
      - page, page_size: Paginación.
    """
    serializer_class = ProductoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Producto.objects.all().order_by("producto")
        params = self.request.query_params

        search = params.get("search")
        if search:
            search = search.strip()
            qs = qs.filter(Q(producto__icontains=search) | Q(no_parte__icontains=search))

        categoria = params.get("categoria")
        if categoria:
            qs = qs.filter(categoria__iexact=categoria.strip())

        unidad = params.get("unidad_negocio")
        if unidad:
            qs = qs.filter(unidad_negocio__iexact=unidad.strip())

        return qs


class FacturaListView(generics.ListAPIView):
    """
    GET /api/finanzas/facturas/
    Parámetros de consulta opcionales:
      - cliente: ID del cliente.
      - tipo_compra: FISICA o ONLINE.
      - por_cobrar: true o false.
      - fecha_inicio: Formato DD/MM/AAAA o AAAA-MM-DD.
      - fecha_fin: Formato DD/MM/AAAA o AAAA-MM-DD.
      - page, page_size: Paginación.
    """
    serializer_class = FacturaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = (
            Factura.objects.select_related("cliente", "tipo_compra")
            .annotate(
                total_venta=Sum(F("detalles__cantidad") * F("detalles__precio_unitario")),
                items_count=Count("detalles"),
            )
            .order_by("-fecha")
        )
        params = self.request.query_params

        cliente = params.get("cliente")
        if cliente:
            qs = qs.filter(cliente_id=cliente.strip())

        tipo_compra = params.get("tipo_compra")
        if tipo_compra:
            qs = qs.filter(tipo_compra_id=tipo_compra.strip().upper())

        por_cobrar = params.get("por_cobrar")
        if por_cobrar is not None and por_cobrar != "":
            qs = qs.filter(por_cobrar=por_cobrar.strip().lower() in ("true", "1", "si"))

        fecha_ini = params.get("fecha_inicio")
        if fecha_ini:
            try:
                dt_ini = _parsear_fecha(fecha_ini, "fecha_inicio")
                qs = qs.filter(fecha__gte=_inicio_del_dia(dt_ini))
            except FiltroInvalido:
                pass

        fecha_fin = params.get("fecha_fin")
        if fecha_fin:
            try:
                dt_fin = _parsear_fecha(fecha_fin, "fecha_fin")
                qs = qs.filter(fecha__lt=_inicio_del_dia(dt_fin + timedelta(days=1)))
            except FiltroInvalido:
                pass

        return qs


class DetalleVentaListView(generics.ListAPIView):
    """
    GET /api/finanzas/ventas/
    Parámetros de consulta opcionales:
      - factura: ID de la factura.
      - producto: N° de parte del producto.
      - tipo_compra: FISICA o ONLINE.
      - estado_pago: PAGADO, PENDIENTE o ANULADO.
      - page, page_size: Paginación.
    """
    serializer_class = DetalleVentaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = DetalleVenta.objects.select_related("no_parte", "tipo_compra", "factura").order_by("-fecha")
        params = self.request.query_params

        factura = params.get("factura")
        if factura:
            qs = qs.filter(factura_id=factura.strip())

        producto = params.get("producto")
        if producto:
            qs = qs.filter(no_parte_id=producto.strip())

        estado_pago = params.get("estado_pago")
        if estado_pago:
            qs = qs.filter(estado_pago=estado_pago.strip().upper())

        tipo_compra = params.get("tipo_compra")
        if tipo_compra:
            qs = qs.filter(tipo_compra_id=tipo_compra.strip().upper())

        return qs


class CuentaPorCobrarListView(generics.ListAPIView):
    """
    GET /api/finanzas/cuentas-por-cobrar/
    Parámetros de consulta opcionales:
      - cliente: ID del cliente.
      - factura: ID de la factura.
      - vencidas: true para solo vencidas, false para solo no vencidas.
      - page, page_size: Paginación.
    """
    serializer_class = CuentaPorCobrarSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = CuentaPorCobrar.objects.select_related("cliente", "factura").order_by("fecha_vencimiento")
        params = self.request.query_params

        cliente = params.get("cliente")
        if cliente:
            qs = qs.filter(cliente_id=cliente.strip())

        factura = params.get("factura")
        if factura:
            qs = qs.filter(factura_id=factura.strip())

        vencidas = params.get("vencidas")
        if vencidas is not None and vencidas != "":
            hoy = timezone.localdate() if settings.USE_TZ else date.today()
            if vencidas.strip().lower() in ("true", "1", "si"):
                qs = qs.filter(fecha_vencimiento__lt=hoy)
            else:
                qs = qs.filter(fecha_vencimiento__gte=hoy)

        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Inyectar totales calculados en la cabecera del JSON para widgets de dashboard
        qs_filtrado = self.filter_queryset(self.get_queryset())
        total_monto = qs_filtrado.aggregate(total=Sum("monto"))["total"] or Decimal("0")
        response.data["resumen"] = {
            "total_cuentas": qs_filtrado.count(),
            "monto_total_por_cobrar": float(total_monto),
        }
        return response


class GastoInsumoListView(generics.ListAPIView):
    """
    GET /api/finanzas/gastos/
    Parámetros de consulta opcionales:
      - producto: N° de parte del producto.
      - categoria: Categoría del producto del gasto.
      - fecha_inicio, fecha_fin: Rango de fechas.
      - page, page_size: Paginación.
    """
    serializer_class = GastoInsumoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = GastoInsumo.objects.select_related("producto").order_by("-fecha")
        params = self.request.query_params

        producto = params.get("producto")
        if producto:
            qs = qs.filter(producto_id=producto.strip())

        categoria = params.get("categoria")
        if categoria:
            qs = qs.filter(producto__categoria__iexact=categoria.strip())

        fecha_ini = params.get("fecha_inicio")
        if fecha_ini:
            try:
                dt_ini = _parsear_fecha(fecha_ini, "fecha_inicio")
                qs = qs.filter(fecha__gte=dt_ini)
            except FiltroInvalido:
                pass

        fecha_fin = params.get("fecha_fin")
        if fecha_fin:
            try:
                dt_fin = _parsear_fecha(fecha_fin, "fecha_fin")
                qs = qs.filter(fecha__lte=dt_fin)
            except FiltroInvalido:
                pass

        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        qs_filtrado = self.filter_queryset(self.get_queryset())
        total_gastos = qs_filtrado.aggregate(total=Sum("monto"))["total"] or Decimal("0")
        response.data["resumen"] = {
            "total_registros_gasto": qs_filtrado.count(),
            "monto_total_gastos": float(total_gastos),
        }
        return response


class OpcionesFiltrosView(APIView):
    """
    GET /api/finanzas/opciones-filtros/
    Devuelve listas precomputadas de categorías, unidades de negocio,
    tipos de compra y rango de fechas disponibles en la base de datos para
    que el equipo de Frontend inicialice selects, filtros y calendarios.
    """
    def get(self, request):
        from django.db.models import Max, Min

        categorias = list(
            Producto.objects.values_list("categoria", flat=True)
            .distinct()
            .order_by("categoria")
        )
        unidades = list(
            Producto.objects.values_list("unidad_negocio", flat=True)
            .distinct()
            .order_by("unidad_negocio")
        )
        tipos_compra = [
            {"codigo": codigo, "nombre": nombre}
            for codigo, nombre in TipoCompra.TIPO_CHOICES
        ]
        estados_pago = [
            {"codigo": codigo, "nombre": nombre}
            for codigo, nombre in DetalleVenta.ESTADO_PAGO_CHOICES
        ]

        rango_fechas = Factura.objects.aggregate(
            min_fecha=Min("fecha"),
            max_fecha=Max("fecha"),
        )

        min_f = _a_fecha_local(rango_fechas.get("min_fecha"))
        max_f = _a_fecha_local(rango_fechas.get("max_fecha"))

        return Response({
            "categorias": [c for c in categorias if c],
            "unidades_negocio": [u for u in unidades if u],
            "tipos_compra": tipos_compra,
            "estados_pago": estados_pago,
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
    Índice interactivo de la API para los equipos de Frontend y Base de Datos.
    """
    def get(self, request):
        host = request.build_absolute_uri("/").rstrip("/")
        return Response({
            "nombre": "API Caja Clara - Módulo Finanzas Supermercado",
            "version": "1.0",
            "descripcion": "Endpoints REST listos para consumo del Frontend y agnósticos al motor de base de datos.",
            "endpoints": {
                "opciones_filtros": {
                    "url": f"{host}/api/finanzas/opciones-filtros/",
                    "metodo": "GET",
                    "descripcion": "Metadatos para llenar dropdowns de categorías, unidades y rangos de fechas.",
                },
                "kpis_resumen": {
                    "url": f"{host}/api/finanzas/resumen-mensual/",
                    "metodo": "GET",
                    "descripcion": "Resumen financiero de KPIs (ingresos, costos, utilidad, margen %, pagos pendientes).",
                    "parametros": ["fecha_inicio", "fecha_fin", "tipo_compra"],
                },
                "serie_temporal": {
                    "url": f"{host}/api/finanzas/resumen-agrupado/",
                    "metodo": "GET",
                    "descripcion": "Datos agrupados para gráficos (diaria, mensual, trimestral, anual).",
                    "parametros": ["fecha_inicio", "fecha_fin", "agrupacion", "tipo_compra"],
                },
                "exportar_excel": {
                    "url": f"{host}/api/finanzas/exportar-excel/",
                    "metodo": "GET",
                    "descripcion": "Descarga de archivo XLSX con formato contable.",
                    "parametros": ["fecha_inicio", "fecha_fin", "tipo_compra"],
                },
                "clientes": {
                    "url": f"{host}/api/finanzas/clientes/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de clientes con conteo de facturas y saldo deudor.",
                    "parametros": ["search", "page", "page_size"],
                },
                "productos": {
                    "url": f"{host}/api/finanzas/productos/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de productos.",
                    "parametros": ["search", "categoria", "unidad_negocio", "page", "page_size"],
                },
                "facturas": {
                    "url": f"{host}/api/finanzas/facturas/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de facturas/ventas con montos calculados.",
                    "parametros": ["cliente", "tipo_compra", "por_cobrar", "fecha_inicio", "fecha_fin", "page", "page_size"],
                },
                "ventas_detalles": {
                    "url": f"{host}/api/finanzas/ventas/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de líneas de venta individuales.",
                    "parametros": ["factura", "producto", "tipo_compra", "estado_pago", "page", "page_size"],
                },
                "cuentas_por_cobrar": {
                    "url": f"{host}/api/finanzas/cuentas-por-cobrar/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de cuentas por cobrar con indicador de vencimiento y total.",
                    "parametros": ["cliente", "factura", "vencidas", "page", "page_size"],
                },
                "gastos": {
                    "url": f"{host}/api/finanzas/gastos/",
                    "metodo": "GET",
                    "descripcion": "Listado paginado de gastos de insumos y costos asociados.",
                    "parametros": ["producto", "categoria", "fecha_inicio", "fecha_fin", "page", "page_size"],
                },
            },
        })