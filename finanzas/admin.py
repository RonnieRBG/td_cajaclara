from django.contrib import admin

from .models import (
    Cliente,
    CuentaPorCobrar,
    DetalleVenta,
    Factura,
    GastoInsumo,
    Producto,
    TipoCompra,
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


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    raw_id_fields = ("no_parte",)


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ("factura", "cliente", "fecha", "tipo_compra", "por_cobrar", "anulada")
    list_filter = ("tipo_compra", "por_cobrar", "anulada")
    search_fields = ("factura",)
    raw_id_fields = ("cliente",)
    inlines = [DetalleVentaInline]


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ("id", "factura", "no_parte", "cantidad", "precio_unitario", "costo_unitario")
    list_filter = ("factura__tipo_compra", "factura__por_cobrar")
    search_fields = ("factura__factura", "no_parte__no_parte")
    raw_id_fields = ("factura", "no_parte")


@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    list_display = ("pk", "factura", "cliente", "monto", "fecha_vencimiento", "estado", "fecha_pago")
    list_filter = ("estado", "fecha_vencimiento")
    search_fields = ("factura__factura", "cliente__nombre")
    raw_id_fields = ("factura", "cliente")


@admin.register(GastoInsumo)
class GastoInsumoAdmin(admin.ModelAdmin):
    list_display = ("pk", "tipo", "categoria", "producto", "proveedor", "fecha", "monto")
    list_filter = ("tipo", "categoria", "fecha")
    search_fields = ("producto__no_parte", "producto__producto", "proveedor", "descripcion")
    raw_id_fields = ("producto",)
