from django.contrib import admin
from .models import TipoCompra, Cliente, Producto, Factura, Replicacion, DetalleVenta

admin.site.register(TipoCompra)
admin.site.register(Cliente)
admin.site.register(Producto)
admin.site.register(Factura)
admin.site.register(Replicacion)
admin.site.register(DetalleVenta)