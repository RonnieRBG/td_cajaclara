from django.contrib import admin
from .models import (
    TipoCompra, Cliente, Producto, Factura,
    Replicacion, DetalleVenta, CuentaPorCobrar, GastoInsumo,
)


@admin.register(TipoCompra)
class TipoCompraAdmin(admin.ModelAdmin):
    list_display = ("tipo_compra", "descripcion")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("cliente_id", "nombre", "contacto")
    search_fields = ("nombre", "contacto")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("no_parte", "producto", "categoria", "unidad_negocio", "precio_venta", "costo_venta")
    list_filter = ("categoria", "unidad_negocio")
    search_fields = ("no_parte", "producto")


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ("factura", "cliente", "fecha", "tipo_compra", "por_cobrar")
    list_filter = ("tipo_compra", "por_cobrar")
    search_fields = ("factura",)
    raw_id_fields = ("cliente",)


@admin.register(Replicacion)
class ReplicacionAdmin(admin.ModelAdmin):
    list_display = ("replica_id", "source_row_id")


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ("id", "factura", "no_parte", "cantidad", "precio_unitario", "costo_unitario", "estado_pago")
    list_filter = ("estado_pago", "tipo_compra")
    search_fields = ("id", "factura__factura")
    raw_id_fields = ("factura", "no_parte")


@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    list_display = ("pk", "factura", "cliente", "monto", "fecha_vencimiento")
    list_filter = ("fecha_vencimiento",)
    search_fields = ("factura__factura",)
    raw_id_fields = ("factura", "cliente")


@admin.register(GastoInsumo)
class GastoInsumoAdmin(admin.ModelAdmin):
    list_display = ("pk", "producto", "fecha", "monto")
    list_filter = ("fecha",)
    search_fields = ("producto__no_parte", "producto__producto")
    raw_id_fields = ("producto",)
