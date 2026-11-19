from django.contrib import admin

from .models import Cliente, CuentaPorCobrar, DetalleVenta, GastoInsumo, Producto, Venta


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id_cliente", "nombre", "contacto")
    search_fields = ("nombre", "contacto")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id_producto", "producto", "categoria", "unidad_negocio")
    list_filter = ("categoria", "unidad_negocio")
    search_fields = ("id_producto", "producto")


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    raw_id_fields = ("producto",)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id_factura", "cliente", "fecha", "tipo_compra", "por_cobrar")
    list_filter = ("tipo_compra", "por_cobrar")
    search_fields = ("id_factura",)
    raw_id_fields = ("cliente",)
    inlines = [DetalleVentaInline]


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ("id_detalle", "venta", "producto", "cantidad", "precio_venta", "costo_venta")
    list_filter = ("venta__tipo_compra", "venta__por_cobrar")
    search_fields = ("venta__id_factura", "producto__id_producto")
    raw_id_fields = ("venta", "producto")


@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    list_display = ("id_cuenta", "venta", "cliente", "monto", "fecha_vencimiento", "estado", "fecha_pago")
    list_filter = ("estado", "fecha_vencimiento")
    search_fields = ("venta__id_factura", "cliente__nombre")
    raw_id_fields = ("venta", "cliente")


@admin.register(GastoInsumo)
class GastoInsumoAdmin(admin.ModelAdmin):
    list_display = ("id_gasto", "producto", "fecha", "monto")
    list_filter = ("fecha",)
    search_fields = ("producto__id_producto", "producto__producto")
    raw_id_fields = ("producto",)
