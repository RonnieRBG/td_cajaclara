"""
Management command: verificar_esquema

Revisa que las tablas de la base conectada (por ejemplo Neon, la del equipo de datos)
tengan las columnas que usa el backend. No modifica nada: solo lee.

    python manage.py verificar_esquema
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from finanzas.metricas import VISTAS, vistas_existentes
from finanzas.models import Cliente, CuentaPorCobrar, DetalleVenta, GastoInsumo, Producto, Venta

MODELOS = (Cliente, Producto, Venta, DetalleVenta, CuentaPorCobrar, GastoInsumo)


class Command(BaseCommand):
    help = "Compara las tablas de la base conectada con los modelos de finanzas (solo lectura)."

    def handle(self, *args, **options):
        problemas = 0
        with connection.cursor() as cursor:
            tablas = set(connection.introspection.table_names(cursor))
            for modelo in MODELOS:
                tabla = modelo._meta.db_table
                if tabla not in tablas:
                    self.stdout.write(self.style.ERROR(f"✗ Falta la tabla '{tabla}'."))
                    problemas += 1
                    continue
                en_base = {c.name for c in connection.introspection.get_table_description(cursor, tabla)}
                esperadas = {campo.column for campo in modelo._meta.concrete_fields}
                faltan = sorted(esperadas - en_base)
                sobran = sorted(en_base - esperadas)
                if faltan:
                    self.stdout.write(self.style.ERROR(f"✗ {tabla}: faltan columnas {', '.join(faltan)}"))
                    problemas += 1
                else:
                    self.stdout.write(self.style.SUCCESS(f"✓ {tabla}: {', '.join(sorted(esperadas))}"))
                if sobran:
                    self.stdout.write(self.style.WARNING(f"  {tabla}: columnas que el backend no usa: {', '.join(sobran)}"))
        faltan_vistas = sorted({v.nombre for v in VISTAS.values()} - vistas_existentes())
        if faltan_vistas:
            self.stdout.write(self.style.WARNING(
                f"⚠ Faltan vistas de métricas: {', '.join(faltan_vistas)}. /api/finanzas/metricas/ no funcionará "
                "hasta crearlas (local: crear_vistas_metricas; Neon: las crea el equipo de datos)."
            ))
        else:
            self.stdout.write(self.style.SUCCESS("✓ Vistas de métricas del equipo de datos presentes."))
        if problemas:
            raise CommandError(f"{problemas} problema(s) entre la base y los modelos.")
        self.stdout.write(self.style.SUCCESS("El esquema de la base coincide con el backend."))
