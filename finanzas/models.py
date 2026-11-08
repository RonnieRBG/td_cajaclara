from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F

CERO = Decimal("0.00")


class TipoCompra(models.Model):
    TIPO_CHOICES = [
        ("FISICA", "Física"),
        ("ONLINE", "En línea"),
    ]

   
    tipo_compra = models.CharField(max_length=50, primary_key=True, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Tipo de compra"
        verbose_name_plural = "Tipos de compra"

    def __str__(self):
        return self.get_tipo_compra_display()


class Cliente(models.Model):
    cliente_id = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=150, blank=True, null=True)
    contacto = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombre or f"Cliente {self.cliente_id}"


class Producto(models.Model):
    no_parte = models.CharField(max_length=50, primary_key=True)
    producto = models.CharField(max_length=200)
    categoria = models.CharField(max_length=100, blank=True, default="Otros / sin clasificar")
    unidad_negocio = models.CharField(max_length=100, blank=True, default="Supermercado")

   
    precio_venta = models.DecimalField(
        max_digits=12, decimal_places=2, default=CERO, validators=[MinValueValidator(CERO)]
    )
    costo_venta = models.DecimalField(
        max_digits=12, decimal_places=2, default=CERO, validators=[MinValueValidator(CERO)]
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.producto} ({self.no_parte})"


class Factura(models.Model):
    factura = models.CharField(max_length=50, primary_key=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,  # si se borra el cliente, la factura se conserva
        null=True,
        blank=True,
        related_name="facturas",
    )
    fecha = models.DateTimeField(blank=True, null=True)
    tipo_compra = models.ForeignKey(
        TipoCompra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="facturas",
    )
    por_cobrar = models.BooleanField(default=False)
    fecha_cobro = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Factura #{self.factura}"


class Replicacion(models.Model):
    """Metadato técnico: de qué carga/replicación (ETL) proviene cada registro."""

    replica_id = models.IntegerField(primary_key=True)
    source_row_id = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Replicación"
        verbose_name_plural = "Replicaciones"

    def __str__(self):
        return f"Replica #{self.replica_id}"



class DetalleVentaQuerySet(models.QuerySet):
    def con_totales(self):
        """Agrega total_venta, total_costo y utilidad calculados por la base de datos,
        de modo que se pueden usar en filter(), order_by() y aggregate()."""
        monto = DecimalField(max_digits=14, decimal_places=2)
        return self.annotate(
            total_venta=ExpressionWrapper(F("cantidad") * F("precio_unitario"), output_field=monto),
            total_costo=ExpressionWrapper(F("cantidad") * F("costo_unitario"), output_field=monto),
        ).annotate(
            utilidad=ExpressionWrapper(F("total_venta") - F("total_costo"), output_field=monto),
        )


class DetalleVentaManager(models.Manager.from_queryset(DetalleVentaQuerySet)):
    def get_queryset(self):
        # Trae factura y producto en la misma consulta (JOIN) 
        return super().get_queryset().select_related("factura", "no_parte", "tipo_compra")


class DetalleVenta(models.Model):
    ESTADO_PAGO_CHOICES = [
        ("PAGADO", "Pagado"),
        ("PENDIENTE", "Pendiente"),
        ("ANULADO", "Anulado"),
    ]

   
    id = models.CharField(max_length=24, primary_key=True, db_column="_id")

    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,  
        db_column="factura",
        related_name="detalles",
    )
   
    no_parte = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        db_column="no_parte",
        related_name="ventas",
    )
    tipo_compra = models.ForeignKey(
        TipoCompra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="tipo_compra",
        related_name="ventas",
    )
    replica = models.ForeignKey(
        Replicacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="replica_id",
        related_name="ventas",
    )

   
    fecha = models.DateTimeField(blank=True, null=True)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    estado_pago = models.CharField(max_length=15, choices=ESTADO_PAGO_CHOICES, default="PAGADO")
    source_row_id = models.IntegerField(blank=True, null=True)

    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(CERO)]
    )
    costo_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(CERO)]
    )

    objects = DetalleVentaManager()

    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["estado_pago"]),
        ]

    def save(self, *args, **kwargs):
      
        if self.precio_unitario is None:
            self.precio_unitario = self.no_parte.precio_venta
        if self.costo_unitario is None:
            self.costo_unitario = self.no_parte.costo_venta
       
        if self.fecha is None:
            self.fecha = self.factura.fecha
        super().save(*args, **kwargs)

   
    @property
    def total_linea_venta(self):
        return (self.cantidad or 0) * (self.precio_unitario or CERO)

    @property
    def total_linea_costo(self):
        return (self.cantidad or 0) * (self.costo_unitario or CERO)

    @property
    def utilidad_linea(self):
        return self.total_linea_venta - self.total_linea_costo

    def __str__(self):
     
        return f"Venta {self.id} - Factura {self.factura_id}"


class CuentaPorCobrar(models.Model):
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="cuentas_por_cobrar",
        null=True,
        blank=True,
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cuentas_por_cobrar",
    )
    monto = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(CERO)]
    )
    fecha_vencimiento = models.DateField()

    class Meta:
        verbose_name = "Cuenta por cobrar"
        verbose_name_plural = "Cuentas por cobrar"
        ordering = ["fecha_vencimiento"]

    def __str__(self):
        return f"Cuenta #{self.pk} - Factura {self.factura_id} - ${self.monto}"


class GastoInsumo(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="gastos",
    )
    fecha = models.DateField()
    monto = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(CERO)]
    )

    class Meta:
        verbose_name = "Gasto de insumo"
        verbose_name_plural = "Gastos de insumo"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"]),
        ]

    def __str__(self):
        return f"Gasto #{self.pk} - {self.producto_id} - ${self.monto}"
