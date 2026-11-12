from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, CharField, DecimalField, ExpressionWrapper, F, Q, Value, When
from django.utils import timezone

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
    """En el MER: Producto (id_producto = no_parte)."""

    no_parte = models.CharField(max_length=50, primary_key=True)
    producto = models.CharField(max_length=200)
    categoria = models.CharField(max_length=100, blank=True, default="Otros / sin clasificar")
    unidad_negocio = models.CharField(max_length=100, blank=True, default="Supermercado")

    # Precio de catálogo: es el que se propone al registrar una venta nueva.
    # Cada línea de venta guarda su propio precio (ver DetalleVenta).
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
    """En el MER: Venta. Es la fuente única de fecha, cliente y tipo de compra."""

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
    # True = venta a crédito (el cliente paga después). El pago se registra
    # en su CuentaPorCobrar; este campo no cambia al pagar.
    por_cobrar = models.BooleanField(default=False)
    anulada = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"]),
        ]

    def __str__(self):
        return f"Factura #{self.factura}"

    @property
    def estado_pago(self):
        """PAGADO, PENDIENTE o ANULADO, igual que DetalleVentaQuerySet.con_estado_pago()."""
        if self.anulada:
            return "ANULADO"
        cuenta = getattr(self, "cuenta_por_cobrar", None)
        if self.por_cobrar and (cuenta is None or cuenta.estado == CuentaPorCobrar.PENDIENTE):
            return "PENDIENTE"
        return "PAGADO"


ESTADO_PAGO_CHOICES = [
    ("PAGADO", "Pagado"),
    ("PENDIENTE", "Pendiente"),
    ("ANULADO", "Anulado"),
]


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

    def con_estado_pago(self):
        """Agrega estado_pago (PAGADO / PENDIENTE / ANULADO) a partir de la factura
        y su cuenta por cobrar. Ya no se guarda en cada línea, así no se desincroniza."""
        return self.annotate(
            estado_pago=Case(
                When(factura__anulada=True, then=Value("ANULADO")),
                When(
                    Q(factura__por_cobrar=True)
                    & (
                        Q(factura__cuenta_por_cobrar__isnull=True)
                        | Q(factura__cuenta_por_cobrar__estado=CuentaPorCobrar.PENDIENTE)
                    ),
                    then=Value("PENDIENTE"),
                ),
                default=Value("PAGADO"),
                output_field=CharField(),
            )
        )


class DetalleVentaManager(models.Manager.from_queryset(DetalleVentaQuerySet)):
    def get_queryset(self):
        # Trae factura, su tipo de compra y el producto en la misma consulta (JOIN)
        return super().get_queryset().select_related("factura", "factura__tipo_compra", "no_parte")


class DetalleVenta(models.Model):
    """En el MER: Detalle_Venta. Una línea de una factura: qué producto, cuánto y a qué precio.
    La fecha, el tipo de compra y el estado de pago se leen desde la factura."""

    ESTADO_PAGO_CHOICES = ESTADO_PAGO_CHOICES

    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    no_parte = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="ventas",
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    # Precio y costo al momento de la venta (si el catálogo cambia, la venta no cambia).
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
        ordering = ["-factura__fecha"]

    def save(self, *args, **kwargs):
        # Si no se indica precio o costo, se usa el del catálogo del producto.
        if self.precio_unitario is None:
            self.precio_unitario = self.no_parte.precio_venta
        if self.costo_unitario is None:
            self.costo_unitario = self.no_parte.costo_venta
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


class CuentaPorCobrarQuerySet(models.QuerySet):
    def con_estado_actual(self, hoy=None):
        """Agrega estado_actual: PAGADA, VENCIDA (pendiente con fecha ya pasada) o PENDIENTE."""
        hoy = hoy or timezone.localdate()
        return self.annotate(
            estado_actual=Case(
                When(estado=CuentaPorCobrar.PAGADA, then=Value(CuentaPorCobrar.PAGADA)),
                When(fecha_vencimiento__lt=hoy, then=Value(CuentaPorCobrar.VENCIDA)),
                default=Value(CuentaPorCobrar.PENDIENTE),
                output_field=CharField(),
            )
        )


class CuentaPorCobrar(models.Model):
    """En el MER: Cuenta_por_cobrar. Una por cada venta a crédito (relación 1 a 0..1).
    VENCIDA no se guarda: es una cuenta PENDIENTE cuya fecha de vencimiento ya pasó."""

    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"
    VENCIDA = "VENCIDA"  # solo calculado, nunca se guarda
    ESTADO_CHOICES = [
        (PENDIENTE, "Pendiente"),
        (PAGADA, "Pagada"),
    ]
    ESTADO_ACTUAL_CHOICES = [
        (PENDIENTE, "Pendiente"),
        (VENCIDA, "Vencida"),
        (PAGADA, "Pagada"),
    ]

    factura = models.OneToOneField(
        Factura,
        on_delete=models.CASCADE,
        related_name="cuenta_por_cobrar",
    )
    # Igual al cliente de la factura; se mantiene porque así está en el MER y en el CSV.
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
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=PENDIENTE)
    fecha_pago = models.DateField(blank=True, null=True)

    objects = CuentaPorCobrarQuerySet.as_manager()

    class Meta:
        verbose_name = "Cuenta por cobrar"
        verbose_name_plural = "Cuentas por cobrar"
        ordering = ["fecha_vencimiento"]
        indexes = [
            models.Index(fields=["estado", "fecha_vencimiento"]),
        ]
        constraints = [
            # Una cuenta pagada siempre tiene fecha de pago, y una pendiente no.
            models.CheckConstraint(
                condition=(Q(estado="PAGADA") & Q(fecha_pago__isnull=False))
                | (Q(estado="PENDIENTE") & Q(fecha_pago__isnull=True)),
                name="cuenta_fecha_pago_segun_estado",
            ),
        ]

    def __str__(self):
        return f"Cuenta #{self.pk} - Factura {self.factura_id} - ${self.monto}"

    def calcular_estado_actual(self):
        """PENDIENTE, VENCIDA o PAGADA, según el estado y la fecha de hoy.
        (En consultas usa CuentaPorCobrar.objects.con_estado_actual())."""
        if self.estado == self.PAGADA:
            return self.PAGADA
        if self.fecha_vencimiento and self.fecha_vencimiento < timezone.localdate():
            return self.VENCIDA
        return self.PENDIENTE


class GastoInsumo(models.Model):
    """En el MER: Gastos_insumo. Toda salida de dinero que no es una venta:
    compras de productos para revender (COMPRA) y otros gastos del negocio (OTRO)."""

    COMPRA = "COMPRA"
    OTRO = "OTRO"
    TIPO_CHOICES = [
        (COMPRA, "Compra"),
        (OTRO, "Otro gasto"),
    ]
    CATEGORIA_CHOICES = [
        ("INSUMOS", "Compra de insumos"),
        ("TRANSPORTE", "Transporte o flete"),
        ("SERVICIOS", "Servicios básicos"),
        ("ARRIENDO", "Arriendo"),
        ("MANTENIMIENTO", "Mantenimiento"),
        ("LIMPIEZA", "Insumos de limpieza"),
        ("OTROS", "Otros"),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default=COMPRA)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default="INSUMOS")
    # Solo las compras van ligadas a un producto; un arriendo o un flete no.
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="gastos",
    )
    proveedor = models.CharField(max_length=150, blank=True, default="")
    descripcion = models.CharField(max_length=255, blank=True, default="")
    fecha = models.DateField()
    monto = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(CERO)]
    )

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["fecha"]),
        ]
        constraints = [
            # Una compra siempre indica qué producto se compró.
            models.CheckConstraint(
                condition=~Q(tipo="COMPRA") | Q(producto__isnull=False),
                name="gasto_compra_requiere_producto",
            ),
        ]

    def __str__(self):
        return f"Gasto #{self.pk} - {self.get_tipo_display()} - ${self.monto}"
