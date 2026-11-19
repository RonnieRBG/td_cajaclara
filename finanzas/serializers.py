"""
Serializers de Django REST Framework para la aplicación Finanzas (Caja Clara).

Los nombres de los campos en el JSON son los mismos de las columnas del esquema del
equipo de datos (id_factura, id_cliente, id_producto, precio_venta, ...), así el
frontend, la base de datos y Power BI hablan el mismo idioma.
Los montos son enteros (pesos chilenos).
"""

import unicodedata

from django.utils import timezone
from rest_framework import serializers

from .models import Cliente, CuentaPorCobrar, DetalleVenta, GastoInsumo, Producto, Venta


def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


ALIAS_TIPO_COMPRA = {
    "FISICA": Venta.FISICA,
    "EN LINEA": Venta.EN_LINEA,
    "ENLINEA": Venta.EN_LINEA,
    "EN_LINEA": Venta.EN_LINEA,
    "ONLINE": Venta.EN_LINEA,
}


def normalizar_tipo_compra(texto):
    """'Física', 'fisica', 'FISICA' → 'Física'; 'En Línea', 'en linea', 'ONLINE' → 'En Línea'.
    Devuelve None si no es un tipo válido."""
    return ALIAS_TIPO_COMPRA.get(_sin_tildes(texto or "").strip().upper())


class TipoCompraField(serializers.CharField):
    def to_internal_value(self, data):
        tipo = normalizar_tipo_compra(str(data))
        if tipo is None:
            raise serializers.ValidationError("Tipo de compra inválido. Usa 'Física' o 'En Línea'.")
        return tipo


class ClienteSerializer(serializers.ModelSerializer):
    total_facturas = serializers.IntegerField(read_only=True, default=0)
    total_deuda = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Cliente
        fields = ["id_cliente", "nombre", "contacto", "total_facturas", "total_deuda"]


class ProductoSerializer(serializers.ModelSerializer):
    total_vendido = serializers.IntegerField(read_only=True, default=0)
    total_ingresos = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Producto
        fields = ["id_producto", "producto", "categoria", "unidad_negocio", "total_vendido", "total_ingresos"]


class VentaSerializer(serializers.ModelSerializer):
    id_cliente = serializers.IntegerField(source="cliente_id", read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default="")
    total_venta = serializers.IntegerField(read_only=True, default=0)
    items_count = serializers.IntegerField(read_only=True, default=0)
    estado_pago = serializers.CharField(read_only=True)
    fecha_vencimiento = serializers.DateField(
        source="cuenta_por_cobrar.fecha_vencimiento", read_only=True, default=None
    )

    class Meta:
        model = Venta
        fields = [
            "id_factura",
            "id_cliente",
            "cliente_nombre",
            "fecha",
            "tipo_compra",
            "por_cobrar",
            "estado_pago",
            "fecha_vencimiento",
            "total_venta",
            "items_count",
        ]


class DetalleVentaSerializer(serializers.ModelSerializer):
    id_factura = serializers.CharField(source="venta_id", read_only=True)
    id_producto = serializers.CharField(source="producto_id", read_only=True)
    producto_nombre = serializers.CharField(source="producto.producto", read_only=True, default="")
    categoria = serializers.CharField(source="producto.categoria", read_only=True, default="")
    fecha = serializers.DateField(source="venta.fecha", read_only=True)
    tipo_compra = serializers.CharField(source="venta.tipo_compra", read_only=True)
    estado_pago = serializers.CharField(read_only=True)
    total_venta = serializers.IntegerField(source="total_linea_venta", read_only=True)
    total_costo = serializers.IntegerField(source="total_linea_costo", read_only=True)
    utilidad = serializers.IntegerField(source="utilidad_linea", read_only=True)

    class Meta:
        model = DetalleVenta
        fields = [
            "id_detalle",
            "id_factura",
            "id_producto",
            "producto_nombre",
            "categoria",
            "tipo_compra",
            "fecha",
            "cantidad",
            "precio_venta",
            "costo_venta",
            "total_venta",
            "total_costo",
            "utilidad",
            "estado_pago",
        ]


class CuentaPorCobrarSerializer(serializers.ModelSerializer):
    id_factura = serializers.CharField(source="venta_id", read_only=True)
    id_cliente = serializers.IntegerField(source="cliente_id", read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default="")
    cliente_contacto = serializers.CharField(source="cliente.contacto", read_only=True, default="")
    fecha_emision = serializers.DateField(source="venta.fecha", read_only=True)
    estado_actual = serializers.SerializerMethodField()
    dias_atraso = serializers.SerializerMethodField()

    class Meta:
        model = CuentaPorCobrar
        fields = [
            "id_cuenta",
            "id_factura",
            "fecha_emision",
            "id_cliente",
            "cliente_nombre",
            "cliente_contacto",
            "monto",
            "fecha_vencimiento",
            "estado",
            "estado_actual",
            "dias_atraso",
            "fecha_pago",
        ]

    def get_estado_actual(self, obj):
        if hasattr(obj, "estado_actual"):
            return obj.estado_actual
        return obj.calcular_estado_actual()

    def get_dias_atraso(self, obj):
        if obj.estado == CuentaPorCobrar.PAGADA:
            return 0
        return max((timezone.localdate() - obj.fecha_vencimiento).days, 0)


class GastoInsumoSerializer(serializers.ModelSerializer):
    id_producto = serializers.CharField(source="producto_id", read_only=True)
    producto_nombre = serializers.CharField(source="producto.producto", read_only=True, default="")
    categoria = serializers.CharField(source="producto.categoria", read_only=True, default="")

    class Meta:
        model = GastoInsumo
        fields = ["id_gasto", "id_producto", "producto_nombre", "categoria", "fecha", "monto"]


class LineaVentaSerializer(serializers.ModelSerializer):
    id_producto = serializers.CharField(source="producto_id", read_only=True)
    producto_nombre = serializers.CharField(source="producto.producto", read_only=True)
    total_venta = serializers.IntegerField(source="total_linea_venta", read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ["id_detalle", "id_producto", "producto_nombre", "cantidad", "precio_venta", "costo_venta", "total_venta"]


class VentaDetalleSerializer(VentaSerializer):
    """Venta con sus productos y su cuenta por cobrar (si fue a crédito)."""

    detalles = LineaVentaSerializer(many=True, read_only=True)
    cuenta_por_cobrar = serializers.SerializerMethodField()

    class Meta(VentaSerializer.Meta):
        fields = VentaSerializer.Meta.fields + ["detalles", "cuenta_por_cobrar"]

    def get_cuenta_por_cobrar(self, obj):
        cuenta = getattr(obj, "cuenta_por_cobrar", None)
        return CuentaPorCobrarSerializer(cuenta).data if cuenta else None


class ItemVentaEntradaSerializer(serializers.Serializer):
    id_producto = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source="producto",
        error_messages={"does_not_exist": "No existe el producto '{pk_value}'."},
    )
    cantidad = serializers.IntegerField(min_value=1, max_value=100000)
    precio_venta = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    costo_venta = serializers.IntegerField(min_value=1, required=False, allow_null=True)


class VentaEntradaSerializer(serializers.Serializer):
    """POST /api/finanzas/facturas/"""

    items = ItemVentaEntradaSerializer(many=True, allow_empty=False, max_length=200)
    id_cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        source="cliente",
        error_messages={"does_not_exist": "No existe el cliente '{pk_value}'."},
    )
    tipo_compra = TipoCompraField(default=Venta.FISICA)
    fecha = serializers.DateField(required=False, help_text="Por defecto, hoy.")
    por_cobrar = serializers.BooleanField(default=False, help_text="true = venta a crédito.")
    fecha_vencimiento = serializers.DateField(required=False, allow_null=True)

    def validate(self, datos):
        if datos.get("por_cobrar"):
            if not datos.get("fecha_vencimiento"):
                raise serializers.ValidationError(
                    {"fecha_vencimiento": "Una venta a crédito necesita la fecha de vencimiento."}
                )
        elif datos.get("fecha_vencimiento"):
            raise serializers.ValidationError(
                {"fecha_vencimiento": "Solo las ventas a crédito (por_cobrar=true) llevan fecha de vencimiento."}
            )
        return datos


class PagoEntradaSerializer(serializers.Serializer):
    """POST /api/finanzas/cuentas-por-cobrar/{id_cuenta}/pagar/"""

    fecha_pago = serializers.DateField(required=False, allow_null=True, help_text="Por defecto, hoy.")


class GastoEntradaSerializer(serializers.Serializer):
    """POST /api/finanzas/gastos/"""

    id_producto = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source="producto",
        error_messages={"does_not_exist": "No existe el producto '{pk_value}'."},
    )
    monto = serializers.IntegerField(min_value=1)
    fecha = serializers.DateField(required=False, allow_null=True, help_text="Por defecto, hoy.")


class ClienteEntradaSerializer(serializers.Serializer):
    """POST /api/finanzas/clientes/"""

    nombre = serializers.CharField(max_length=100)
    contacto = serializers.CharField(max_length=100)

    def validate_contacto(self, contacto):
        contacto = contacto.strip()
        if Cliente.objects.filter(contacto=contacto).exists():
            raise serializers.ValidationError("Ya existe un cliente con ese contacto.")
        return contacto
