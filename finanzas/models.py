"""
Modelos de Caja Clara.

Siguen el esquema que definió el equipo de datos
(rama `datos`: Etapa_4_Carga_y_Nube/schema_postgresql.sql),:

    cliente, producto, venta, detalle_venta, cuenta_por_cobrar, gastos_insumo

- Los montos son enteros (pesos chilenos, sin decimales).
- La fecha de una venta es solo fecha (sin hora).
- Los ID (id_detalle, id_cuenta, id_gasto, id_cliente) no los genera la base de
  datos: en el esquema de datos son INTEGER PRIMARY KEY sin secuencia. Los asigna
  el backend (ver finanzas/ids.py).
- No hay columnas extra.
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, CharField, F, Q, Value, When
from django.utils import timezone


class Cliente(models.Model):
    id_cliente = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "cliente"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.nombre} ({self.id_cliente})"


class Producto(models.Model):
    id_producto = models.CharField(max_length=10, primary_key=True)
    categoria = models.CharField(max_length=100)
    producto = models.CharField(max_length=150)
    unidad_negocio = models.CharField(max_length=100)

    class Meta:
        db_table = "producto"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        indexes = [models.Index(fields=["categoria"], name="idx_producto_categoria")]

    def __str__(self):
        return f"{self.producto} ({self.id_producto})"


class Venta(models.Model):
    """Cabecera de una venta (una fila por factura)."""

    FISICA = "Física"
    EN_LINEA = "En Línea"
    TIPO_COMPRA_CHOICES = [(FISICA, "Física"), (EN_LINEA, "En Línea")]

    id_factura = models.CharField(max_length=30, primary_key=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, db_column="id_cliente", related_name="ventas",
        db_index=False,
    )
    fecha = models.DateField()
    tipo_compra = models.CharField(max_length=20, choices=TIPO_COMPRA_CHOICES)
    por_cobrar = models.BooleanField(default=False)

    class Meta:
        db_table = "venta"
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"], name="idx_venta_fecha"),
            models.Index(fields=["cliente"], name="idx_venta_cliente"),
            models.Index(fields=["por_cobrar"], name="idx_venta_por_cobrar", condition=Q(por_cobrar=True)),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo_compra__in=["Física", "En Línea"]), name="chk_venta_tipo_compra"
            ),
        ]

    def __str__(self):
        return f"Factura {self.id_factura}"

    @property
    def estado_pago(self):
        
        if not self.por_cobrar:
            return "PAGADO"
        cuenta = getattr(self, "cuenta_por_cobrar", None)
        if cuenta is None or cuenta.estado != CuentaPorCobrar.PAGADA:
            return "PENDIENTE"
        return "PAGADO"


ESTADO_PAGO_CHOICES = [
    ("PAGADO", "Pagado"),
    ("PENDIENTE", "Pendiente"),
]


class DetalleVentaQuerySet(models.QuerySet):
    def con_totales(self):
    
        return self.annotate(
            total_venta=F("cantidad") * F("precio_venta"),
            total_costo=F("cantidad") * F("costo_venta"),
        ).annotate(utilidad=F("total_venta") - F("total_costo"))

    def con_estado_pago(self):
       
        return self.annotate(
            estado_pago=Case(
                When(
                    Q(venta__por_cobrar=True)
                    & (
                        Q(venta__cuenta_por_cobrar__isnull=True)
                        | ~Q(venta__cuenta_por_cobrar__estado=CuentaPorCobrar.PAGADA)
                    ),
                    then=Value("PENDIENTE"),
                ),
                default=Value("PAGADO"),
                output_field=CharField(),
            )
        )


class DetalleVentaManager(models.Manager.from_queryset(DetalleVentaQuerySet)):
    def get_queryset(self):
        return super().get_queryset().select_related("venta", "producto")


class DetalleVenta(models.Model):
    

    id_detalle = models.IntegerField(primary_key=True)
    venta = models.ForeignKey(
        Venta, on_delete=models.CASCADE, db_column="id_factura", related_name="detalles",
        db_index=False,
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, db_column="id_producto", related_name="ventas",
        db_index=False,
    )
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_venta = models.IntegerField(validators=[MinValueValidator(1)])
    costo_venta = models.IntegerField(validators=[MinValueValidator(1)])

    objects = DetalleVentaManager()

    class Meta:
        db_table = "detalle_venta"
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"
        ordering = ["-venta__fecha", "-id_detalle"]
        indexes = [
            models.Index(fields=["venta"], name="idx_detalle_factura"),
            models.Index(fields=["producto"], name="idx_detalle_producto"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(cantidad__gt=0), name="chk_detalle_cantidad"),
            models.CheckConstraint(condition=Q(precio_venta__gt=0), name="chk_detalle_precio"),
            models.CheckConstraint(condition=Q(costo_venta__gt=0), name="chk_detalle_costo"),
        ]

    @property
    def total_linea_venta(self):
        return self.cantidad * self.precio_venta

    @property
    def total_linea_costo(self):
        return self.cantidad * self.costo_venta

    @property
    def utilidad_linea(self):
        return self.total_linea_venta - self.total_linea_costo

    def __str__(self):
        return f"Detalle {self.id_detalle} - Factura {self.venta_id}"


class CuentaPorCobrarQuerySet(models.QuerySet):
    def con_estado_actual(self, hoy=None):
       
        hoy = hoy or timezone.localdate()
        return self.annotate(
            estado_actual=Case(
                When(estado=CuentaPorCobrar.PAGADA, then=Value(CuentaPorCobrar.PAGADA)),
                When(
                    Q(estado=CuentaPorCobrar.VENCIDA) | Q(fecha_vencimiento__lt=hoy),
                    then=Value(CuentaPorCobrar.VENCIDA),
                ),
                default=Value(CuentaPorCobrar.PENDIENTE),
                output_field=CharField(),
            ),
        )

    def abiertas(self):
        
        return self.exclude(estado=CuentaPorCobrar.PAGADA)


class CuentaPorCobrar(models.Model):
  

    PENDIENTE = "PENDIENTE"
    VENCIDA = "VENCIDA"
    PAGADA = "PAGADA"
    ESTADO_CHOICES = [
        (PENDIENTE, "Pendiente"),
        (VENCIDA, "Vencida"),
        (PAGADA, "Pagada"),
    ]

    id_cuenta = models.IntegerField(primary_key=True)
    venta = models.OneToOneField(
        Venta, on_delete=models.PROTECT, db_column="id_factura", related_name="cuenta_por_cobrar"
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, db_column="id_cliente", related_name="cuentas_por_cobrar",
        db_index=False,
    )
    monto = models.IntegerField(validators=[MinValueValidator(1)])
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default=PENDIENTE)
    fecha_pago = models.DateField(blank=True, null=True)

    objects = CuentaPorCobrarQuerySet.as_manager()

    class Meta:
        db_table = "cuenta_por_cobrar"
        verbose_name = "Cuenta por cobrar"
        verbose_name_plural = "Cuentas por cobrar"
        ordering = ["fecha_vencimiento"]
        indexes = [
            models.Index(fields=["cliente"], name="idx_cxc_cliente"),
            models.Index(fields=["estado", "fecha_vencimiento"], name="idx_cxc_estado_vencimiento"),
            models.Index(
                fields=["fecha_pago"], name="idx_cxc_fecha_pago", condition=Q(fecha_pago__isnull=False)
            ),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(monto__gt=0), name="chk_cxc_monto"),
            models.CheckConstraint(
                condition=Q(estado__in=["PAGADA", "PENDIENTE", "VENCIDA"]), name="chk_cxc_estado"
            ),
            models.CheckConstraint(
                condition=(Q(estado="PAGADA") & Q(fecha_pago__isnull=False))
                | (Q(estado__in=["PENDIENTE", "VENCIDA"]) & Q(fecha_pago__isnull=True)),
                name="chk_cxc_estado_pago",
            ),
        ]

    def __str__(self):
        return f"Cuenta {self.id_cuenta} - Factura {self.venta_id} - ${self.monto}"

    def calcular_estado_actual(self, hoy=None):
        """PAGADA, VENCIDA o PENDIENTE a la fecha de hoy
        (en consultas usa CuentaPorCobrar.objects.con_estado_actual())."""
        hoy = hoy or timezone.localdate()
        if self.estado == self.PAGADA:
            return self.PAGADA
        if self.estado == self.VENCIDA or self.fecha_vencimiento < hoy:
            return self.VENCIDA
        return self.PENDIENTE


class GastoInsumo(models.Model):
   

    id_gasto = models.IntegerField(primary_key=True)
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, db_column="id_producto", related_name="gastos",
        db_index=False,
    )
    fecha = models.DateField()
    monto = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "gastos_insumo"
        verbose_name = "Gasto en insumos"
        verbose_name_plural = "Gastos en insumos"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"], name="idx_gastos_fecha"),
            models.Index(fields=["producto"], name="idx_gastos_producto"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(monto__gt=0), name="chk_gastos_monto"),
        ]

    def __str__(self):
        return f"Gasto {self.id_gasto} - {self.producto_id} - ${self.monto}"
