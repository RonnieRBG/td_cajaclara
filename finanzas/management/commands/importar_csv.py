"""
Management command: importar_csv
Carga las 6 tablas del proyecto de supermercado desde la carpeta data/.
Orden: TipoCompra → Cliente → Producto → Factura → DetalleVenta → CuentaPorCobrar → GastoInsumo
"""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from finanzas.models import (
    Cliente,
    CuentaPorCobrar,
    DetalleVenta,
    Factura,
    GastoInsumo,
    Producto,
    TipoCompra,
)

DATA_DIR = Path(settings.BASE_DIR) / "data"
BATCH_SIZE = 5000

TIPO_COMPRA_MAP = {
    "Física": "FISICA",
    "Fisica": "FISICA",
    "En Línea": "ONLINE",
    "En Linea": "ONLINE",
    "En línea": "ONLINE",
}


class Command(BaseCommand):
    help = "Importa los CSV del proyecto de supermercado a la base de datos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Borra todos los datos antes de importar (fresh import).",
        )

    def handle(self, *args, **options):
        if not DATA_DIR.exists():
            raise CommandError(f"No se encontró la carpeta '{DATA_DIR}'. Crea la carpeta y coloca los CSV ahí.")

        archivos = {
            "cliente": DATA_DIR / "cliente.csv",
            "producto": DATA_DIR / "producto.csv",
            "venta": DATA_DIR / "venta.csv",
            "detalle_venta": DATA_DIR / "detalle_venta.csv",
            "cuenta_por_cobrar": DATA_DIR / "cuenta_por_cobrar.csv",
            "gastos_insumo": DATA_DIR / "gastos_insumo.csv",
        }

        faltantes = [nombre for nombre, ruta in archivos.items() if not ruta.exists()]
        if faltantes:
            raise CommandError(f"Faltan archivos CSV: {', '.join(faltantes)}")

        if options["limpiar"]:
            self.stdout.write(self.style.WARNING("Limpiando datos existentes..."))
            GastoInsumo.objects.all().delete()
            CuentaPorCobrar.objects.all().delete()
            DetalleVenta.objects.all().delete()
            Factura.objects.all().delete()
            Producto.objects.all().delete()
            Cliente.objects.all().delete()

        self.stdout.write("=" * 60)
        self.stdout.write("IMPORTACIÓN DE DATOS DEL SUPERMERCADO")
        self.stdout.write("=" * 60)

        with transaction.atomic():
            self._importar_tipos_compra()
            self._importar_clientes(archivos["cliente"])
            self._importar_productos(archivos["producto"])
            self._importar_ventas(archivos["venta"])
            self._importar_detalles(archivos["detalle_venta"])
            self._importar_cuentas(archivos["cuenta_por_cobrar"])
            self._importar_gastos(archivos["gastos_insumo"])

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Importación completada exitosamente."))
        self._mostrar_resumen()

    def _leer_csv(self, ruta):
        with open(ruta, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def _importar_tipos_compra(self):
        self.stdout.write("\n[1/7] Tipos de compra...")
        TipoCompra.objects.get_or_create(
            tipo_compra="FISICA", defaults={"descripcion": "Compra presencial en tienda"}
        )
        TipoCompra.objects.get_or_create(
            tipo_compra="ONLINE", defaults={"descripcion": "Compra en línea"}
        )
        self.stdout.write(self.style.SUCCESS("  → 2 tipos de compra listos."))

    def _importar_clientes(self, ruta):
        self.stdout.write("\n[2/7] Clientes...")
        filas = self._leer_csv(ruta)

        existentes = set(Cliente.objects.values_list("cliente_id", flat=True))
        nuevos = []
        for fila in filas:
            cid = str(fila["id_cliente"])
            if cid not in existentes:
                nuevos.append(
                    Cliente(
                        cliente_id=cid,
                        nombre=fila.get("nombre", ""),
                        contacto=fila.get("contacto", ""),
                    )
                )
                existentes.add(cid)

        if nuevos:
            Cliente.objects.bulk_create(nuevos, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevos)} clientes creados ({len(filas)} en CSV)."))

    def _importar_productos(self, ruta):
        self.stdout.write("\n[3/7] Productos...")
        filas = self._leer_csv(ruta)

        existentes = set(Producto.objects.values_list("no_parte", flat=True))
        nuevos = []
        for fila in filas:
            pid = fila["id_producto"]
            if pid not in existentes:
                nuevos.append(
                    Producto(
                        no_parte=pid,
                        producto=fila.get("producto", ""),
                        categoria=fila.get("categoria", "Otros / sin clasificar"),
                        unidad_negocio=fila.get("unidad_negocio", "Supermercado"),
                    )
                )
                existentes.add(pid)

        if nuevos:
            Producto.objects.bulk_create(nuevos, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevos)} productos creados ({len(filas)} en CSV)."))

    def _importar_ventas(self, ruta):
        self.stdout.write("\n[4/7] Facturas (ventas)...")
        filas = self._leer_csv(ruta)

        existentes = set(Factura.objects.values_list("factura", flat=True))
        nuevas = []
        for fila in filas:
            fid = fila["id_factura"]
            if fid in existentes:
                continue

            tipo_texto = fila.get("tipo_compra", "")
            tipo_key = TIPO_COMPRA_MAP.get(tipo_texto)

            fecha_str = fila.get("fecha", "")
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d") if fecha_str else None
            if fecha and settings.USE_TZ:
                fecha = timezone.make_aware(fecha)

            por_cobrar = fila.get("por_cobrar", "False").strip().lower() == "true"

            fecha_cobro_str = fila.get("fecha_cobro", "").strip()
            fecha_cobro = datetime.strptime(fecha_cobro_str, "%Y-%m-%d").date() if fecha_cobro_str else None

            nuevas.append(
                Factura(
                    factura=fid,
                    cliente_id=str(fila.get("id_cliente", "")),
                    fecha=fecha,
                    tipo_compra_id=tipo_key,
                    por_cobrar=por_cobrar,
                    fecha_cobro=fecha_cobro,
                )
            )
            existentes.add(fid)

        if nuevas:
            Factura.objects.bulk_create(nuevas, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevas)} facturas creadas ({len(filas)} en CSV)."))

    def _importar_detalles(self, ruta):
        self.stdout.write("\n[5/7] Detalles de venta...")
        filas = self._leer_csv(ruta)

        # Precargar fechas, tipo_compra y por_cobrar de las facturas para asignar a cada detalle
        facturas_info = dict(
            Factura.objects.values_list("factura", "fecha")
        )
        facturas_tipo = dict(
            Factura.objects.values_list("factura", "tipo_compra_id")
        )
        facturas_por_cobrar = dict(
            Factura.objects.values_list("factura", "por_cobrar")
        )

        existentes = set(DetalleVenta.objects.values_list("id", flat=True))
        nuevos = []
        for fila in filas:
            did = str(fila["id_detalle"])
            if did in existentes:
                continue

            factura_id = fila["id_factura"]
            precio = Decimal(fila.get("precio_venta", "0"))
            costo = Decimal(fila.get("costo_venta", "0"))
            es_pendiente = facturas_por_cobrar.get(factura_id, False)

            # Determinar tipo de compra desde la factura
            factura_obj_tipo = facturas_tipo.get(factura_id)

            nuevos.append(
                DetalleVenta(
                    id=did,
                    factura_id=factura_id,
                    no_parte_id=fila["id_producto"],
                    tipo_compra_id=factura_obj_tipo,
                    cantidad=int(fila.get("cantidad", 1)),
                    precio_unitario=precio,
                    costo_unitario=costo,
                    fecha=facturas_info.get(factura_id),
                    estado_pago="PENDIENTE" if es_pendiente else "PAGADO",
                )
            )
            existentes.add(did)

        if nuevos:
            DetalleVenta.objects.bulk_create(nuevos, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevos)} detalles creados ({len(filas)} en CSV)."))

    def _importar_cuentas(self, ruta):
        self.stdout.write("\n[6/7] Cuentas por cobrar...")
        filas = self._leer_csv(ruta)

        nuevas = []
        for fila in filas:
            fecha_str = fila.get("fecha_vencimiento", "").strip()
            fecha_venc = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None
            cid = int(fila["id_cuenta"]) if fila.get("id_cuenta") else None

            nuevas.append(
                CuentaPorCobrar(
                    id=cid,
                    factura_id=fila["id_factura"],
                    cliente_id=str(fila.get("id_cliente", "")),
                    monto=Decimal(fila.get("monto", "0")),
                    fecha_vencimiento=fecha_venc,
                )
            )

        if nuevas:
            CuentaPorCobrar.objects.bulk_create(nuevas, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevas)} cuentas creadas ({len(filas)} en CSV)."))

    def _importar_gastos(self, ruta):
        self.stdout.write("\n[7/7] Gastos de insumo...")
        filas = self._leer_csv(ruta)

        nuevos = []
        for fila in filas:
            fecha_str = fila.get("Fecha", "").strip()
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None
            gid = int(fila["id_gasto"]) if fila.get("id_gasto") else None

            nuevos.append(
                GastoInsumo(
                    id=gid,
                    producto_id=fila["id_producto"],
                    fecha=fecha,
                    monto=Decimal(fila.get("Monto", "0")),
                )
            )

        if nuevos:
            GastoInsumo.objects.bulk_create(nuevos, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevos)} gastos creados ({len(filas)} en CSV)."))

    def _mostrar_resumen(self):
        self.stdout.write("\n📊 RESUMEN DE LA BASE DE DATOS:")
        self.stdout.write(f"   Tipos de compra: {TipoCompra.objects.count()}")
        self.stdout.write(f"   Clientes:        {Cliente.objects.count():,}")
        self.stdout.write(f"   Productos:       {Producto.objects.count():,}")
        self.stdout.write(f"   Facturas:        {Factura.objects.count():,}")
        self.stdout.write(f"   Detalles venta:  {DetalleVenta.objects.count():,}")
        self.stdout.write(f"   Cuentas cobrar:  {CuentaPorCobrar.objects.count():,}")
        self.stdout.write(f"   Gastos insumo:   {GastoInsumo.objects.count():,}")

