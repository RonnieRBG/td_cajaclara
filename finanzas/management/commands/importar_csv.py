"""
Management command: importar_csv
Carga las 6 tablas del proyecto de supermercado desde la carpeta data/.
Orden: TipoCompra → Cliente → Producto → Factura → DetalleVenta → CuentaPorCobrar → GastoInsumo
"""

import csv
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction
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

# Carpeta por defecto de los CSV. Si no existe, se usan los de la rama `datos`
# (Etapa 3), que son los mismos archivos. También se puede indicar con --carpeta.
CARPETAS_CANDIDATAS = [
    Path(settings.BASE_DIR) / "data",
    Path(settings.BASE_DIR) / "datos" / "Etapas_1-2-3" / "Etapa_3 Elaboracion de tablas",
]
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
            "--carpeta",
            help="Carpeta con los 6 CSV. Por defecto data/ o, si no existe, la de la Etapa 3 en datos/.",
        )
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Borra todos los datos antes de importar (fresh import).",
        )
        parser.add_argument(
            "--fechas-originales",
            action="store_true",
            help=(
                "Importa las fechas tal como vienen en los CSV (2010-2022). Por defecto se "
                "desplazan para que la última venta quede en la semana actual."
            ),
        )

    def handle(self, *args, **options):
        carpeta = self._carpeta_datos(options.get("carpeta"))
        self.stdout.write(f"Leyendo CSV desde: {carpeta}")

        archivos = {
            "cliente": carpeta / "cliente.csv",
            "producto": carpeta / "producto.csv",
            "venta": carpeta / "venta.csv",
            "detalle_venta": carpeta / "detalle_venta.csv",
            "cuenta_por_cobrar": carpeta / "cuenta_por_cobrar.csv",
            "gastos_insumo": carpeta / "gastos_insumo.csv",
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

        self.desfase = self._calcular_desfase(archivos, options["fechas_originales"])
        precios = self._precios_por_producto(archivos["venta"], archivos["detalle_venta"])

        with transaction.atomic():
            self._importar_tipos_compra()
            self._importar_clientes(archivos["cliente"])
            self._importar_productos(archivos["producto"], precios)
            self._importar_ventas(archivos["venta"])
            self._importar_detalles(archivos["detalle_venta"])
            self._importar_cuentas(archivos["cuenta_por_cobrar"])
            self._importar_gastos(archivos["gastos_insumo"])
            self._reiniciar_secuencias()

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Importación completada exitosamente."))
        self._mostrar_resumen()

    def _carpeta_datos(self, carpeta):
        if carpeta:
            ruta = Path(carpeta)
            if not ruta.is_dir():
                raise CommandError(f"No se encontró la carpeta '{ruta}'.")
            return ruta
        for ruta in CARPETAS_CANDIDATAS:
            if ruta.is_dir():
                return ruta
        raise CommandError(
            "No se encontró la carpeta de datos. Crea 'data/' con los 6 CSV o indica otra con --carpeta."
        )

    def _reiniciar_secuencias(self):
        """Los CSV traen sus propios IDs. En PostgreSQL hay que avanzar el contador
        de IDs para que los registros nuevos que cree la API no choquen con ellos."""
        sql = connection.ops.sequence_reset_sql(no_style(), [DetalleVenta, CuentaPorCobrar, GastoInsumo])
        if sql:
            with connection.cursor() as cursor:
                for sentencia in sql:
                    cursor.execute(sentencia)

    def _leer_csv(self, ruta):
        with open(ruta, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    # ------------------------------------------------------------------
    # Fechas
    # ------------------------------------------------------------------
    def _calcular_desfase(self, archivos, fechas_originales):
        """Los CSV terminan en noviembre de 2022. Para que el dashboard y las
        cuentas por cobrar tengan sentido "hoy", se suma a todas las fechas un
        mismo desfase: la última venta queda en los últimos 7 días.
        El desfase es un múltiplo de 7 días, así cada venta conserva su día de la semana
        y las distancias entre fechas (plazos de cobro, etc.) no cambian."""
        if fechas_originales:
            self.stdout.write("\nFechas: se mantienen las originales de los CSV.")
            return timedelta(0)

        fechas = [
            fila["fecha"] for fila in self._leer_csv(archivos["venta"]) if fila.get("fecha", "").strip()
        ]
        fechas += [
            fila["Fecha"] for fila in self._leer_csv(archivos["gastos_insumo"]) if fila.get("Fecha", "").strip()
        ]
        if not fechas:
            return timedelta(0)

        ultima = datetime.strptime(max(fechas).strip(), "%Y-%m-%d").date()
        ayer = timezone.localdate() - timedelta(days=1)
        semanas = (ayer - ultima).days // 7
        if semanas <= 0:
            return timedelta(0)

        desfase = timedelta(weeks=semanas)
        self.stdout.write(
            f"\nFechas: se desplazan {desfase.days:,} días "
            f"(última venta {ultima:%d/%m/%Y} → {ultima + desfase:%d/%m/%Y}). "
            "Usa --fechas-originales para no desplazarlas."
        )
        return desfase

    def _fecha(self, texto):
        """Convierte 'AAAA-MM-DD' a date aplicando el desfase. Vacío → None."""
        texto = (texto or "").strip()
        if not texto:
            return None
        return datetime.strptime(texto, "%Y-%m-%d").date() + self.desfase

    # ------------------------------------------------------------------
    # Precios de catálogo
    # ------------------------------------------------------------------
    def _precios_por_producto(self, ruta_ventas, ruta_detalles):
        """producto.csv no trae precio. Se toma el precio y el costo de la venta
        más reciente de cada producto, para que el catálogo no quede en $0."""
        fecha_factura = {
            fila["id_factura"]: fila.get("fecha", "") for fila in self._leer_csv(ruta_ventas)
        }
        precios = {}
        for fila in self._leer_csv(ruta_detalles):
            producto = fila["id_producto"]
            fecha = fecha_factura.get(fila["id_factura"], "")
            if producto not in precios or fecha >= precios[producto][0]:
                precios[producto] = (
                    fecha,
                    Decimal(fila.get("precio_venta") or "0"),
                    Decimal(fila.get("costo_venta") or "0"),
                )
        return {producto: (precio, costo) for producto, (_, precio, costo) in precios.items()}

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

    def _importar_productos(self, ruta, precios):
        self.stdout.write("\n[3/7] Productos...")
        filas = self._leer_csv(ruta)

        existentes = set(Producto.objects.values_list("no_parte", flat=True))
        nuevos = []
        sin_precio = 0
        for fila in filas:
            pid = fila["id_producto"]
            if pid not in existentes:
                precio, costo = precios.get(pid, (Decimal("0"), Decimal("0")))
                sin_precio += pid not in precios
                nuevos.append(
                    Producto(
                        no_parte=pid,
                        producto=fila.get("producto", ""),
                        categoria=fila.get("categoria", "Otros / sin clasificar"),
                        unidad_negocio=fila.get("unidad_negocio", "Supermercado"),
                        precio_venta=precio,
                        costo_venta=costo,
                    )
                )
                existentes.add(pid)

        if nuevos:
            Producto.objects.bulk_create(nuevos, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevos)} productos creados ({len(filas)} en CSV)."))
        if sin_precio:
            self.stdout.write(self.style.WARNING(f"  → {sin_precio} productos sin ventas: quedan con precio 0."))

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

            dia = self._fecha(fila.get("fecha"))
            fecha = datetime.combine(dia, datetime.min.time()) if dia else None
            if fecha and settings.USE_TZ:
                fecha = timezone.make_aware(fecha)

            # fecha_cobro del CSV no se guarda en la factura: es la misma
            # fecha_vencimiento de su cuenta por cobrar.
            por_cobrar = fila.get("por_cobrar", "False").strip().lower() == "true"

            nuevas.append(
                Factura(
                    factura=fid,
                    cliente_id=str(fila.get("id_cliente", "")),
                    fecha=fecha,
                    tipo_compra_id=tipo_key,
                    por_cobrar=por_cobrar,
                )
            )
            existentes.add(fid)

        if nuevas:
            Factura.objects.bulk_create(nuevas, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevas)} facturas creadas ({len(filas)} en CSV)."))

    def _importar_detalles(self, ruta):
        self.stdout.write("\n[5/7] Detalles de venta...")
        filas = self._leer_csv(ruta)

        # La fecha, el tipo de compra y el estado de pago se leen desde la factura;
        # cada línea solo guarda producto, cantidad, precio y costo.
        existentes = set(DetalleVenta.objects.values_list("id", flat=True))
        nuevos = []
        for fila in filas:
            did = int(fila["id_detalle"])
            if did in existentes:
                continue

            factura_id = fila["id_factura"]
            precio = Decimal(fila.get("precio_venta", "0"))
            costo = Decimal(fila.get("costo_venta", "0"))

            nuevos.append(
                DetalleVenta(
                    id=did,
                    factura_id=factura_id,
                    no_parte_id=fila["id_producto"],
                    cantidad=int(fila.get("cantidad", 1)),
                    precio_unitario=precio,
                    costo_unitario=costo,
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
            fecha_venc = self._fecha(fila.get("fecha_vencimiento"))
            cid = int(fila["id_cuenta"]) if fila.get("id_cuenta") else None

            nuevas.append(
                CuentaPorCobrar(
                    id=cid,
                    factura_id=fila["id_factura"],
                    cliente_id=str(fila.get("id_cliente", "")),
                    monto=Decimal(fila.get("monto", "0")),
                    fecha_vencimiento=fecha_venc,
                    # El CSV no informa pagos: todas parten pendientes.
                    estado=CuentaPorCobrar.PENDIENTE,
                )
            )

        if nuevas:
            CuentaPorCobrar.objects.bulk_create(nuevas, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f"  → {len(nuevas)} cuentas creadas ({len(filas)} en CSV)."))

    def _importar_gastos(self, ruta):
        self.stdout.write("\n[7/7] Gastos (compras de insumos)...")
        filas = self._leer_csv(ruta)

        nuevos = []
        for fila in filas:
            fecha = self._fecha(fila.get("Fecha"))
            gid = int(fila["id_gasto"]) if fila.get("id_gasto") else None

            nuevos.append(
                GastoInsumo(
                    id=gid,
                    # Todos los gastos del CSV son compras de productos.
                    tipo=GastoInsumo.COMPRA,
                    categoria="INSUMOS",
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

