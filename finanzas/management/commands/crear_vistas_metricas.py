"""
Management command: crear_vistas_metricas

Crea en la base LOCAL las vistas de métricas del equipo de datos (Etapa 5), usando
sus mismos scripts SQL (copiados en finanzas/sql/).

En Neon NO hace falta: ahí las vistas ya existen (las creó el equipo de datos) y el
comando no las toca. Solo las vuelve a crear si se pide con --recrear.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection, transaction

from finanzas.metricas import CARPETA_SQL, VISTAS, vistas_existentes


def _sentencias(sql):
    """Separa el script en sentencias, sin los comentarios."""
    lineas = [linea for linea in sql.splitlines() if not linea.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lineas).split(";") if s.strip()]


class Command(BaseCommand):
    help = "Crea las vistas de métricas del equipo de datos en la base local."

    def add_arguments(self, parser):
        parser.add_argument("--recrear", action="store_true", help="Borra y vuelve a crear las vistas.")

    def handle(self, *args, **options):
        nombres = {vista.nombre for vista in VISTAS.values()}
        if nombres <= vistas_existentes() and not options["recrear"]:
            self.stdout.write("Las vistas de métricas ya existen: no se modifican (usa --recrear para rehacerlas).")
            return

        motor = "postgresql" if connection.vendor == "postgresql" else "sqlite"
        if connection.vendor not in ("postgresql", "sqlite"):
            raise CommandError("Solo hay scripts de vistas para PostgreSQL y SQLite.")
        script = (CARPETA_SQL / f"vistas_metricas_{motor}.sql").read_text(encoding="utf-8")

        try:
            with transaction.atomic(), connection.cursor() as cursor:
                for sentencia in _sentencias(script):
                    if sentencia.upper().startswith("GRANT"):
                        # Los roles de Neon (cajaclara_lectura_bi, cajaclara_app_rw) pueden no existir en local.
                        try:
                            with transaction.atomic():
                                cursor.execute(sentencia)
                        except DatabaseError:
                            self.stdout.write("  (se omiten los permisos: los roles de Neon no existen aquí)")
                        continue
                    cursor.execute(sentencia)
        except DatabaseError as error:
            raise CommandError(
                f"No se pudieron crear las vistas: {error}\n"
                "Si estás conectado a Neon con cajaclara_app_rw, es lo esperado: ahí las crea el equipo de datos."
            )
        self.stdout.write(self.style.SUCCESS(f"Vistas de métricas creadas: {', '.join(sorted(nombres))}"))
