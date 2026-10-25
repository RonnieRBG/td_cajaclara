from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    TIPO_CHOICES = [
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categorias')
    nombre = models.CharField(max_length=50) # Ej: Ventas, Proveedores, Insumos
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)

    class Meta:
        unique_together = ('usuario', 'nombre', 'tipo')

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

class Movimiento(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movimientos')
    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT)
    transaccion_id = models.CharField(max_length=50, blank=True, null=True)
    monto = models.DecimalField(max_digits=12, decimal_places=0) # CLP, sin decimales
    fecha = models.DateField()
    descripcion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Movimiento {self.transaccion_id or self.id}: ${self.monto} ({self.fecha})"

class CuentaPorCobrar(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
        ('VENCIDA', 'Vencida'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cuentas_por_cobrar')
    deudor = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=12, decimal_places=0) # CLP
    fecha_emision = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    notas_contacto = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Deudor: {self.deudor} - ${self.monto} [{self.estado}]"