"""
Endpoints que REGISTRAN datos (POST). Los listados de solo lectura están en views.py.

Errores de validación: 400 con {"campo": ["mensaje"]}.
Reglas del negocio no cumplidas (ej.: pagar dos veces): 400 con {"error": "mensaje"}.
"""

from django.db.models import Count, F, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import servicios
from .models import CuentaPorCobrar, Factura
from .serializers import (
    ClienteEntradaSerializer,
    ClienteSerializer,
    CuentaPorCobrarSerializer,
    FacturaDetalleSerializer,
    GastoEntradaSerializer,
    GastoInsumoSerializer,
    PagoEntradaSerializer,
    VentaEntradaSerializer,
)
from .views import ClienteListView, FacturaListView, GastoInsumoListView


def _error(regla):
    return Response({"error": str(regla)}, status=status.HTTP_400_BAD_REQUEST)


def _factura_con_detalle(pk):
    return get_object_or_404(
        Factura.objects.select_related("cliente", "tipo_compra", "cuenta_por_cobrar__cliente")
        .prefetch_related("detalles__no_parte")
        .annotate(
            total_venta=Sum(F("detalles__cantidad") * F("detalles__precio_unitario")),
            items_count=Count("detalles"),
        ),
        pk=pk,
    )


# ------------------------------------------------------------------------------
# Ventas
# ------------------------------------------------------------------------------

class FacturaListCreateView(FacturaListView):
    """
    GET  /api/finanzas/facturas/  → listado (ver FacturaListView)
    POST /api/finanzas/facturas/  → registrar una venta

    Cuerpo:
    {
      "items": [{"producto": "P100055", "cantidad": 2, "precio_unitario": 1500}],
      "tipo_compra": "FISICA",          // o "ONLINE" (por defecto FISICA)
      "cliente": "179",                 // obligatorio si es a crédito
      "por_cobrar": false,              // true = venta a crédito
      "fecha_vencimiento": "2026-12-15",// obligatorio si es a crédito
      "fecha": "2026-11-11T10:30:00"    // opcional, por defecto ahora
    }
    Si "precio_unitario" no se envía, se usa el precio de catálogo del producto.
    Si es a crédito, se crea su cuenta por cobrar por el total de la venta.
    """

    def post(self, request):
        entrada = VentaEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            factura = servicios.registrar_venta(**entrada.validated_data)
        except servicios.ReglaDeNegocio as regla:
            return _error(regla)
        datos = FacturaDetalleSerializer(_factura_con_detalle(factura.pk)).data
        return Response(datos, status=status.HTTP_201_CREATED)


class FacturaDetalleView(APIView):
    """GET /api/finanzas/facturas/{factura}/ → la venta con sus productos y su cuenta por cobrar."""

    def get(self, request, pk):
        return Response(FacturaDetalleSerializer(_factura_con_detalle(pk)).data)


class AnularFacturaView(APIView):
    """
    POST /api/finanzas/facturas/{factura}/anular/
    Anula la venta completa: deja de sumar en los resúmenes. Si era a crédito y no se
    había pagado, su deuda desaparece. Si ya se pagó, primero hay que revertir el pago.
    """

    def post(self, request, pk):
        factura = get_object_or_404(Factura, pk=pk)
        try:
            servicios.anular_factura(factura)
        except servicios.ReglaDeNegocio as regla:
            return _error(regla)
        return Response(FacturaDetalleSerializer(_factura_con_detalle(pk)).data)


# ------------------------------------------------------------------------------
# Cobros
# ------------------------------------------------------------------------------

class PagarCuentaView(APIView):
    """
    POST /api/finanzas/cuentas-por-cobrar/{id}/pagar/
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
    POST /api/finanzas/cuentas-por-cobrar/{id}/revertir-pago/
    Deshace un pago registrado por error: la cuenta vuelve a quedar pendiente.
    """

    def post(self, request, pk):
        cuenta = get_object_or_404(CuentaPorCobrar, pk=pk)
        try:
            cuenta = servicios.revertir_pago(cuenta)
        except servicios.ReglaDeNegocio as regla:
            return _error(regla)
        return Response(CuentaPorCobrarSerializer(cuenta).data)


# ------------------------------------------------------------------------------
# Gastos y clientes
# ------------------------------------------------------------------------------

class GastoListCreateView(GastoInsumoListView):
    """
    GET  /api/finanzas/gastos/  → listado (ver GastoInsumoListView)
    POST /api/finanzas/gastos/  → registrar un gasto

    Compra de productos:  {"tipo": "COMPRA", "producto": "P100055", "monto": 24000, "proveedor": "Distribuidora Central"}
    Otro gasto:           {"tipo": "OTRO", "categoria": "ARRIENDO", "monto": 350000, "descripcion": "Arriendo noviembre"}
    "fecha" es opcional (por defecto, hoy).
    """

    def post(self, request):
        entrada = GastoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        gasto = entrada.save()
        return Response(GastoInsumoSerializer(gasto).data, status=status.HTTP_201_CREATED)


class ClienteListCreateView(ClienteListView):
    """
    GET  /api/finanzas/clientes/  → listado (ver ClienteListView)
    POST /api/finanzas/clientes/  → registrar un cliente: {"nombre": "...", "contacto": "+56 9 ..."}
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
