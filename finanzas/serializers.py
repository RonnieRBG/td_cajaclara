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
    # Unidades vendidas y monto vendido (en el período pedido, sin ventas anuladas)
    total_vendido = serializers.IntegerField(read_only=True, default=0)
    total_ingresos = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)

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
            "total_ingresos",
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



# ==============================================================================
# DETALLE DE UNA FACTURA (respuesta al registrar o consultar una venta)
# ==============================================================================

class LineaFacturaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="no_parte.producto", read_only=True)
    total_venta = serializers.DecimalField(source="total_linea_venta", max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ["id", "no_parte", "producto_nombre", "cantidad", "precio_unitario", "costo_unitario", "total_venta"]


class FacturaDetalleSerializer(FacturaSerializer):
    """Factura con sus productos y su cuenta por cobrar (si fue a crédito)."""

    detalles = LineaFacturaSerializer(many=True, read_only=True)
    cuenta_por_cobrar = serializers.SerializerMethodField()

    class Meta(FacturaSerializer.Meta):
        fields = FacturaSerializer.Meta.fields + ["detalles", "cuenta_por_cobrar"]

    def get_cuenta_por_cobrar(self, obj):
        cuenta = getattr(obj, "cuenta_por_cobrar", None)
        return CuentaPorCobrarSerializer(cuenta).data if cuenta else None


# ==============================================================================
# ENTRADA DE DATOS (POST): validan lo que envía el frontend
# ==============================================================================

class ItemVentaEntradaSerializer(serializers.Serializer):
    producto = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        error_messages={"does_not_exist": "No existe el producto '{pk_value}'."},
    )
    cantidad = serializers.IntegerField(min_value=1, max_value=100000)
    # Si no se envía, se usa el precio del catálogo del producto.
    precio_unitario = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, allow_null=True
    )


class VentaEntradaSerializer(serializers.Serializer):
    """POST /api/finanzas/facturas/"""

    items = ItemVentaEntradaSerializer(many=True, allow_empty=False, max_length=200)
    tipo_compra = serializers.ChoiceField(choices=TipoCompra.TIPO_CHOICES, default="FISICA")
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        required=False,
        allow_null=True,
        error_messages={"does_not_exist": "No existe el cliente '{pk_value}'."},
    )
    fecha = serializers.DateTimeField(required=False, help_text="Por defecto, ahora.")
    por_cobrar = serializers.BooleanField(default=False, help_text="true = venta a crédito.")
    fecha_vencimiento = serializers.DateField(required=False, allow_null=True)

    def validate(self, datos):
        if datos.get("por_cobrar"):
            errores = {}
            if not datos.get("cliente"):
                errores["cliente"] = "Una venta a crédito necesita un cliente."
            if not datos.get("fecha_vencimiento"):
                errores["fecha_vencimiento"] = "Una venta a crédito necesita la fecha de vencimiento."
            if errores:
                raise serializers.ValidationError(errores)
        elif datos.get("fecha_vencimiento"):
            raise serializers.ValidationError(
                {"fecha_vencimiento": "Solo las ventas a crédito (por_cobrar=true) llevan fecha de vencimiento."}
            )
        return datos


class PagoEntradaSerializer(serializers.Serializer):
    """POST /api/finanzas/cuentas-por-cobrar/{id}/pagar/"""

    fecha_pago = serializers.DateField(required=False, allow_null=True, help_text="Por defecto, hoy.")


class GastoEntradaSerializer(serializers.ModelSerializer):
    """POST /api/finanzas/gastos/"""

    producto = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        required=False,
        allow_null=True,
        error_messages={"does_not_exist": "No existe el producto '{pk_value}'."},
    )
    categoria = serializers.ChoiceField(choices=GastoInsumo.CATEGORIA_CHOICES, required=False)
    fecha = serializers.DateField(required=False)
    monto = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)

    class Meta:
        model = GastoInsumo
        fields = ["tipo", "categoria", "producto", "proveedor", "descripcion", "fecha", "monto"]

    def validate(self, datos):
        tipo = datos.get("tipo", GastoInsumo.COMPRA)
        if tipo == GastoInsumo.COMPRA and not datos.get("producto"):
            raise serializers.ValidationError({"producto": "Una compra debe indicar qué producto se compró."})
        if tipo == GastoInsumo.OTRO and datos.get("producto"):
            raise serializers.ValidationError({"producto": "Solo las compras (tipo COMPRA) llevan producto."})
        # Categoría por defecto según el tipo
        datos.setdefault("categoria", "INSUMOS" if tipo == GastoInsumo.COMPRA else "OTROS")
        if datos.get("fecha") is None:
            from django.utils import timezone
            datos["fecha"] = timezone.localdate()
        return datos


class ClienteEntradaSerializer(serializers.Serializer):
    """POST /api/finanzas/clientes/"""

    nombre = serializers.CharField(max_length=150)
    contacto = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
