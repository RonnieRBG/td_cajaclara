"""
Serializers de Django REST Framework para la aplicación Finanzas (Caja Clara).
Exponen todas las entidades del supermercado en formatos JSON limpios para el equipo Frontend.
"""

from rest_framework import serializers

from .models import (
    Cliente,
    CuentaPorCobrar,
    DetalleVenta,
    Factura,
    GastoInsumo,
    Producto,
    TipoCompra,
)


class TipoCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCompra
        fields = ["tipo_compra", "descripcion"]


class ClienteSerializer(serializers.ModelSerializer):
    total_facturas = serializers.IntegerField(read_only=True, default=0)
    total_deuda = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)

    class Meta:
        model = Cliente
        fields = [
            "cliente_id",
            "nombre",
            "contacto",
            "total_facturas",
            "total_deuda",
        ]


class ProductoSerializer(serializers.ModelSerializer):
    total_vendido = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Producto
        fields = [
            "no_parte",
            "producto",
            "categoria",
            "unidad_negocio",
            "precio_venta",
            "costo_venta",
            "total_vendido",
        ]


class FacturaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default="")
    tipo_compra_nombre = serializers.CharField(source="tipo_compra.get_tipo_compra_display", read_only=True, default="")
    total_venta = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)
    items_count = serializers.IntegerField(read_only=True, default=0)
    estado_pago = serializers.CharField(read_only=True)
    # Antes "fecha_cobro": es la fecha de vencimiento de su cuenta por cobrar (null si fue al contado).
    fecha_vencimiento = serializers.DateField(
        source="cuenta_por_cobrar.fecha_vencimiento", read_only=True, default=None
    )

    class Meta:
        model = Factura
        fields = [
            "factura",
            "cliente",
            "cliente_nombre",
            "fecha",
            "tipo_compra",
            "tipo_compra_nombre",
            "por_cobrar",
            "anulada",
            "estado_pago",
            "fecha_vencimiento",
            "total_venta",
            "items_count",
        ]


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="no_parte.producto", read_only=True, default="")
    categoria = serializers.CharField(source="no_parte.categoria", read_only=True, default="")
    # Fecha, tipo de compra y estado de pago vienen de la factura (antes se repetían en cada línea).
    fecha = serializers.DateTimeField(source="factura.fecha", read_only=True)
    tipo_compra = serializers.CharField(source="factura.tipo_compra_id", read_only=True, default=None)
    estado_pago = serializers.CharField(read_only=True)
    total_venta = serializers.DecimalField(
        source="total_linea_venta", max_digits=14, decimal_places=2, read_only=True
    )
    total_costo = serializers.DecimalField(
        source="total_linea_costo", max_digits=14, decimal_places=2, read_only=True
    )
    utilidad = serializers.DecimalField(
        source="utilidad_linea", max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = DetalleVenta
        fields = [
            "id",
            "factura",
            "no_parte",
            "producto_nombre",
            "categoria",
            "tipo_compra",
            "fecha",
            "cantidad",
            "precio_unitario",
            "costo_unitario",
            "total_venta",
            "total_costo",
            "utilidad",
            "estado_pago",
        ]


class CuentaPorCobrarSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default="")
    cliente_contacto = serializers.CharField(source="cliente.contacto", read_only=True, default="")
    fecha_emision = serializers.DateTimeField(source="factura.fecha", read_only=True)
    estado_actual = serializers.SerializerMethodField()
    vencida = serializers.SerializerMethodField()

    class Meta:
        model = CuentaPorCobrar
        fields = [
            "id",
            "factura",
            "fecha_emision",
            "cliente",
            "cliente_nombre",
            "cliente_contacto",
            "monto",
            "fecha_vencimiento",
            "estado",
            "estado_actual",
            "fecha_pago",
            "vencida",
        ]

    def get_estado_actual(self, obj):
        # Si la consulta ya lo calculó (con_estado_actual), se usa ese valor.
        if hasattr(obj, "estado_actual"):
            return obj.estado_actual
        return obj.calcular_estado_actual()

    def get_vencida(self, obj):
        return self.get_estado_actual(obj) == CuentaPorCobrar.VENCIDA


class GastoInsumoSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    categoria_nombre = serializers.CharField(source="get_categoria_display", read_only=True)
    producto_nombre = serializers.CharField(source="producto.producto", read_only=True, default="")
    categoria_producto = serializers.CharField(source="producto.categoria", read_only=True, default="")

    class Meta:
        model = GastoInsumo
        fields = [
            "id",
            "tipo",
            "tipo_nombre",
            "categoria",
            "categoria_nombre",
            "producto",
            "producto_nombre",
            "categoria_producto",
            "proveedor",
            "descripcion",
            "fecha",
            "monto",
        ]

