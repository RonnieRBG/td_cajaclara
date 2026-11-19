"""
Endpoints que REGISTRAN datos (POST). Los listados de solo lectura están en views.py.

Errores de validación: 400 con {"campo": ["mensaje"]}.
Reglas del negocio no cumplidas (ej.: pagar dos veces): 400 con {"error": "mensaje"}.

No hay endpoints para borrar: el usuario de la API en la base del equipo de datos
(cajaclara_app_rw) solo puede leer, insertar y actualizar.
"""

from django.db.models import Count, F, Prefetch, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import servicios
from .models import CuentaPorCobrar, DetalleVenta, Venta
from .serializers import (
    ClienteEntradaSerializer,
    ClienteSerializer,
    CuentaPorCobrarSerializer,
    GastoEntradaSerializer,
    GastoInsumoSerializer,
    PagoEntradaSerializer,
    VentaDetalleSerializer,
    VentaEntradaSerializer,
)
from .views import ClienteListView, GastoInsumoListView, VentaListView


def _error(regla):
    return Response({"error": str(regla)}, status=status.HTTP_400_BAD_REQUEST)


def _venta_con_detalle(pk):
    return get_object_or_404(
        Venta.objects.select_related("cliente", "cuenta_por_cobrar__cliente")
        .prefetch_related(
            Prefetch("detalles", queryset=DetalleVenta.objects.order_by("id_detalle"))
        )
        .annotate(
            total_venta=Sum(F("detalles__cantidad") * F("detalles__precio_venta")),
            items_count=Count("detalles"),
        ),
        pk=pk,
    )


class VentaListCreateView(VentaListView):
    """
    GET  /api/finanzas/facturas/  → listado (ver VentaListView)
    POST /api/finanzas/facturas/  → registrar una venta

    Cuerpo:
    {
      "items": [{"id_producto": "P100055", "cantidad": 2, "precio_venta": 1500, "costo_venta": 1100}],
      "id_cliente": 179,                // obligatorio (en el esquema de datos toda venta tiene cliente)
      "tipo_compra": "Física",          // o "En Línea" (por defecto Física)
      "por_cobrar": false,              // true = venta a crédito
      "fecha_vencimiento": "2026-12-15",// obligatorio si es a crédito
      "fecha": "2026-11-11"             // opcional, por defecto hoy
    }
    Si "precio_venta" o "costo_venta" no se envían, se usan los de la última venta del producto.
    Si es a crédito, se crea su cuenta por cobrar por el total de la venta.
    """

    def post(self, request):
        entrada = VentaEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            venta = servicios.registrar_venta(**entrada.validated_data)
        except servicios.ReglaDeNegocio as regla:
            return _error(regla)
        datos = VentaDetalleSerializer(_venta_con_detalle(venta.pk)).data
        return Response(datos, status=status.HTTP_201_CREATED)


class VentaDetalleView(APIView):
    """GET /api/finanzas/facturas/{id_factura}/ → la venta con sus productos y su cuenta por cobrar."""

    def get(self, request, pk):
        return Response(VentaDetalleSerializer(_venta_con_detalle(pk)).data)


class PagarCuentaView(APIView):
    """
    POST /api/finanzas/cuentas-por-cobrar/{id_cuenta}/pagar/
    Cuerpo (opcional): {"fecha_pago": "2026-11-11"}  → por defecto, hoy.
    Registra el pago completo de la deuda.
    """

    def post(self, request, pk):
        cuenta = get_object_or_404(CuentaPorCobrar, pk=pk)
        entrada = PagoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            cuenta = servicios.pagar_cuenta(cuenta, entrada.validated_data.get("fecha_pago"))
        except servicios.ReglaDeNegocio as regla:
            return _error(regla)
        return Response(CuentaPorCobrarSerializer(cuenta).data)


class RevertirPagoView(APIView):
    """
    POST /api/finanzas/cuentas-por-cobrar/{id_cuenta}/revertir-pago/
    Deshace un pago registrado por error: la cuenta vuelve a quedar abierta.
    """

    def post(self, request, pk):
        cuenta = get_object_or_404(CuentaPorCobrar, pk=pk)
        try:
            cuenta = servicios.revertir_pago(cuenta)
        except servicios.ReglaDeNegocio as regla:
            return _error(regla)
        return Response(CuentaPorCobrarSerializer(cuenta).data)


class GastoListCreateView(GastoInsumoListView):
    """
    GET  /api/finanzas/gastos/  → listado (ver GastoInsumoListView)
    POST /api/finanzas/gastos/  → registrar un gasto en insumos:
         {"id_producto": "P100055", "monto": 24000, "fecha": "2026-11-11"}   ("fecha" opcional, por defecto hoy)
    """

    def post(self, request):
        entrada = GastoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            gasto = servicios.registrar_gasto(**entrada.validated_data)
        except servicios.ReglaDeNegocio as regla:
            return _error(regla)
        return Response(GastoInsumoSerializer(gasto).data, status=status.HTTP_201_CREATED)


class ClienteListCreateView(ClienteListView):
    """
    GET  /api/finanzas/clientes/  → listado (ver ClienteListView)
    POST /api/finanzas/clientes/  → registrar un cliente: {"nombre": "...", "contacto": "+56 9 ..."}
         (contacto es obligatorio y único, como en el esquema de datos)
    """

    def post(self, request):
        entrada = ClienteEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            cliente = servicios.crear_cliente(**entrada.validated_data)
        except servicios.ReglaDeNegocio as regla:
            return _error(regla)
        cliente.total_facturas, cliente.total_deuda = 0, 0
        return Response(ClienteSerializer(cliente).data, status=status.HTTP_201_CREATED)
