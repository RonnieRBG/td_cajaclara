"""
Management command: importar_csv

Carga en una base LOCAL (SQLite o PostgreSQL de desarrollo) los 6 CSV del equipo de datos:
cliente, producto, venta, detalle_venta, cuenta_por_cobrar y gastos_insumo.

En Neon NO hace falta: ahí el equipo de datos ya cargó las tablas con su ETL (Etapa 4).

Acepta los dos formatos que ha usado el equipo de datos:
- Etapa 4 (datos_procesados/): cuenta_por_cobrar trae estado y fecha_pago; gastos_insumo
  trae las columnas en minúscula (fecha, monto).
- Etapa 3: cuenta_por_cobrar sin estado ni fecha_pago (se calcula PENDIENTE o VENCIDA);
  gastos_insumo con Fecha y Monto.
"""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from finanzas.models import Cliente, CuentaPorCobrar, DetalleVenta, GastoInsumo, Producto, Venta

# Carpetas donde se buscan los CSV (la primera que exista). También se puede indicar con --carpeta.
CARPETAS_CANDIDATAS = [
    Path(settings.BASE_DIR) / "data",
    Path(settings.BASE_DIR) / "datos" / "Etapas_4-5-6" / "Etapa_4_Carga_y_Nube" / "datos_procesados",
    Path(settings.BASE_DIR) / "datos" / "Etapas_1-2-3" / "Etapa_3 Elaboracion de tablas",
]
BATCH_SIZE = 5000
VERDADEROS = ("true", "1", "t", "si", "sí")


class Command(BaseCommand):
    help = "Importa los CSV del equipo de datos a la base de datos local."

    def add_arguments(self, parser):
        parser.add_argument("--carpeta", help="Carpeta con los 6 CSV. Por defecto data/.")
        parser.add_argument(
            "--limpiar", action="store_true", help="Borra todos los datos antes de importar (solo base local)."
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

        nombres = ["cliente", "producto", "venta", "detalle_venta", "cuenta_por_cobrar", "gastos_insumo"]
        archivos = {nombre: carpeta / f"{nombre}.csv" for nombre in nombres}
        faltantes = [nombre for nombre, ruta in archivos.items() if not ruta.exists()]
        if faltantes:
            raise CommandError(f"Faltan archivos CSV: {', '.join(faltantes)}")
        csvs = {nombre: self._leer_csv(ruta) for nombre, ruta in archivos.items()}

        self.desfase = self._calcular_desfase(csvs, options["fechas_originales"])

        with transaction.atomic():
            if options["limpiar"]:
                self.stdout.write(self.style.WARNING("Limpiando datos existentes..."))
                for modelo in (GastoInsumo, CuentaPorCobrar, DetalleVenta, Venta, Producto, Cliente):
                    modelo.objects.all().delete()
            self._importar_clientes(csvs["cliente"])
            self._importar_productos(csvs["producto"])
            self._importar_ventas(csvs["venta"])
            self._importar_detalles(csvs["detalle_venta"])
            self._importar_cuentas(csvs["cuenta_por_cobrar"])
            self._importar_gastos(csvs["gastos_insumo"])

        self.stdout.write(self.style.SUCCESS("\n✅ Importación completada."))
        self._mostrar_resumen()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _carpeta_datos(self, carpeta):
        if carpeta:
            ruta = Path(carpeta)
            if not ruta.is_dir():
                raise CommandError(f"No se encontró la carpeta '{ruta}'.")
            return ruta
        for ruta in CARPETAS_CANDIDATAS:
            if ruta.is_dir():
                return ruta
        raise CommandError("No se encontró la carpeta de datos. Crea 'data/' con los 6 CSV o usa --carpeta.")

    def _leer_csv(self, ruta):
        """Lee el CSV con los nombres de columna en minúscula (Fecha → fecha, Monto → monto)."""
        with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
            return [
                {(k or "").strip().lower(): (v or "").strip() for k, v in fila.items()}
                for fila in csv.DictReader(f)
            ]

    def _calcular_desfase(self, csvs, fechas_originales):
        """Los CSV terminan en 2022. Para que el dashboard y las cuentas por cobrar tengan
        sentido "hoy", se suma a todas las fechas un mismo desfase: la última venta queda en
        los últimos 7 días. El desfase es un múltiplo de 7 días, así cada venta conserva su
        día de la semana y las distancias entre fechas (plazos de cobro, etc.) no cambian."""
        if fechas_originales:
            self.stdout.write("Fechas: se mantienen las originales de los CSV.")
            return timedelta(0)
        fechas = [f["fecha"] for f in csvs["venta"] if f.get("fecha")]
        fechas += [f["fecha"] for f in csvs["gastos_insumo"] if f.get("fecha")]
        if not fechas:
            return timedelta(0)
        ultima = date.fromisoformat(max(fechas))
        semanas = (timezone.localdate() - timedelta(days=1) - ultima).days // 7
        if semanas <= 0:
            return timedelta(0)
        desfase = timedelta(weeks=semanas)
        self.stdout.write(
            f"Fechas: se desplazan {desfase.days:,} días (última venta {ultima:%d/%m/%Y} → "
            f"{ultima + desfase:%d/%m/%Y}). Usa --fechas-originales para no desplazarlas."
        )
        return desfase

    def _fecha(self, texto):
        """'AAAA-MM-DD' → date con el desfase aplicado. Vacío → None."""
        if not texto:
            return None
        return datetime.strptime(texto[:10], "%Y-%m-%d").date() + self.desfase

    def _crear(self, modelo, objetos, total_csv, nombre):
        """Inserta solo las filas cuyo ID aún no existe (se puede volver a correr sin duplicar)."""
        existentes = set(modelo.objects.values_list("pk", flat=True))
        nuevos = [o for o in objetos if o.pk not in existentes]
        modelo.objects.bulk_create(nuevos, batch_size=BATCH_SIZE)
        self.stdout.write(f"  {nombre:<18} {len(nuevos):>9,} nuevas ({total_csv:,} en el CSV)")

    # ------------------------------------------------------------------
    # Tablas
    # ------------------------------------------------------------------
    def _importar_clientes(self, filas):
        self._crear(
            Cliente,
            [Cliente(id_cliente=int(f["id_cliente"]), nombre=f["nombre"], contacto=f["contacto"]) for f in filas],
            len(filas),
            "cliente",
        )

    def _importar_productos(self, filas):
        self._crear(
            Producto,
            [
                Producto(
                    id_producto=f["id_producto"],
                    categoria=f["categoria"],
                    producto=f["producto"],
                    unidad_negocio=f["unidad_negocio"],
                )
                for f in filas
            ],
            len(filas),
            "producto",
        )

    def _importar_ventas(self, filas):
        tipos = {"física": Venta.FISICA, "fisica": Venta.FISICA, "en línea": Venta.EN_LINEA, "en linea": Venta.EN_LINEA}
        objetos = []
        for f in filas:
            tipo = tipos.get(f["tipo_compra"].lower())
            if tipo is None:
                raise CommandError(f"Venta {f['id_factura']}: tipo_compra desconocido '{f['tipo_compra']}'.")
            objetos.append(
                Venta(
                    id_factura=f["id_factura"],
                    cliente_id=int(f["id_cliente"]),
                    fecha=self._fecha(f["fecha"]),
                    tipo_compra=tipo,
                    por_cobrar=f.get("por_cobrar", "").lower() in VERDADEROS,
                )
            )
        self._crear(Venta, objetos, len(filas), "venta")

    def _importar_detalles(self, filas):
        self._crear(
            DetalleVenta,
            [
                DetalleVenta(
                    id_detalle=int(f["id_detalle"]),
                    venta_id=f["id_factura"],
                    producto_id=f["id_producto"],
                    cantidad=int(f["cantidad"]),
                    precio_venta=int(f["precio_venta"]),
                    costo_venta=int(f["costo_venta"]),
                )
                for f in filas
            ],
            len(filas),
            "detalle_venta",
        )

    def _importar_cuentas(self, filas):
        hoy = timezone.localdate()
        objetos = []
        for f in filas:
            vencimiento = self._fecha(f["fecha_vencimiento"])
            estado = f.get("estado", "").upper()
            fecha_pago = self._fecha(f.get("fecha_pago"))
            if not estado:  # formato Etapa 3: sin estado ni pagos
                estado = CuentaPorCobrar.VENCIDA if vencimiento < hoy else CuentaPorCobrar.PENDIENTE
                fecha_pago = None
            objetos.append(
                CuentaPorCobrar(
                    id_cuenta=int(f["id_cuenta"]),
                    venta_id=f["id_factura"],
                    cliente_id=int(f["id_cliente"]),
                    monto=int(f["monto"]),
                    fecha_vencimiento=vencimiento,
                    estado=estado,
                    fecha_pago=fecha_pago,
                )
            )
        self._crear(CuentaPorCobrar, objetos, len(filas), "cuenta_por_cobrar")

    def _importar_gastos(self, filas):
        self._crear(
            GastoInsumo,
            [
                GastoInsumo(
                    id_gasto=int(f["id_gasto"]),
                    producto_id=f["id_producto"],
                    fecha=self._fecha(f["fecha"]),
                    monto=int(f["monto"]),
                )
                for f in filas
            ],
            len(filas),
            "gastos_insumo",
        )

    def _mostrar_resumen(self):
        self.stdout.write("\n📊 Filas en la base de datos:")
        for modelo in (Cliente, Producto, Venta, DetalleVenta, CuentaPorCobrar, GastoInsumo):
            self.stdout.write(f"   {modelo._meta.db_table:<18} {modelo.objects.count():>9,}")
