"""
Métricas del equipo de datos (Etapa 5): la API lee SUS vistas SQL, sin recalcular.

Así la app y el tablero de Power BI muestran exactamente los mismos números.
Las vistas las define el equipo de datos (vistas_metricas_postgresql.sql). En Neon
ya existen; en local se crean con `python manage.py crear_vistas_metricas`.

Ojo: estas vistas son de ANÁLISIS HISTÓRICO y usan las fechas de corte fijas que
definió el equipo de datos (2022-09-01 para la cartera y 2020-12-31 para la
"cobertura completa"). Para lo operativo del día a día (cobros de hoy) se usa
/cuentas-por-cobrar/ y /alertas-cobro/, que calculan con la fecha de hoy.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView

from .views import StandardResultsSetPagination

CARPETA_SQL = Path(__file__).resolve().parent / "sql"

MENSAJE_SIN_VISTAS = (
    "Faltan las vistas de métricas en la base de datos. En local: "
    "'python manage.py crear_vistas_metricas'. En Neon las crea el equipo de datos "
    "(vistas_metricas_postgresql.sql)."
)


@dataclass
class Vista:
    """Una vista del equipo de datos y lo que la API permite hacer con ella."""

    nombre: str
    descripcion: str
    columnas: tuple
    filtros: tuple = ()
    enteros: tuple = ()
    buscar: tuple = ()
    orden: tuple = ()
    booleanos: tuple = ()
    paginada: bool = True
    extra: dict = field(default_factory=dict)


VISTAS = {
    "margen-productos": Vista(
        nombre="vw_margen_producto_categoria",
        descripcion="Tarea 22: margen por producto, categoría y mes.",
        columnas=("anio", "mes", "periodo", "cobertura", "id_producto", "producto", "categoria",
                  "num_facturas", "unidades", "ventas", "costo", "margen", "margen_pct"),
        filtros=("anio", "mes", "periodo", "cobertura", "id_producto", "categoria"),
        enteros=("anio", "mes"),
        buscar=("producto", "id_producto"),
        orden=("-periodo", "-margen"),
    ),
    "ventas-categoria-mes": Vista(
        nombre="vw_ventas_categoria_mes",
        descripcion="Tarea 23: ventas por categoría y mes.",
        columnas=("anio", "mes", "periodo", "cobertura", "categoria", "facturas", "unidades", "ventas", "margen"),
        filtros=("anio", "mes", "periodo", "cobertura", "categoria"),
        enteros=("anio", "mes"),
        orden=("-periodo", "-ventas"),
    ),
    "flujo-caja-mensual": Vista(
        nombre="vw_flujo_caja_mensual",
        descripcion="Tarea 24: flujo de caja mensual (lo cobrado menos los gastos).",
        columnas=("periodo", "anio", "mes", "cobertura", "ventas_facturadas", "ingresos_contado", "ventas_fiadas",
                  "cobros_fiado_recibidos", "ingresos_efectivamente_cobrados", "gastos_insumo", "flujo_caja_neto"),
        filtros=("anio", "mes", "periodo", "cobertura"),
        enteros=("anio", "mes"),
        orden=("-periodo",),
    ),
    "cuentas-por-cobrar-cliente": Vista(
        nombre="vw_cuentas_por_cobrar_cliente",
        descripcion="Tarea 25: cuánto debe cada cliente y su historial de atrasos (corte 2022-09-01).",
        columnas=("id_cliente", "nombre", "contacto", "total_cuentas_fiadas", "monto_total_fiado", "monto_pagado",
                  "monto_adeudado_actual", "monto_vencido_actual", "cuentas_abiertas", "cuentas_vencidas",
                  "proxima_fecha_cobro", "max_dias_atraso_actual", "promedio_dias_atraso_historico"),
        filtros=("id_cliente",),
        enteros=("id_cliente",),
        buscar=("nombre", "contacto"),
        orden=("-monto_adeudado_actual", "id_cliente"),
        extra={"con_deuda": "cuentas_abiertas > 0"},
    ),
    "morosidad": Vista(
        nombre="vw_indicador_morosidad",
        descripcion="Tarea 26: indicador de morosidad en tres escenarios.",
        columnas=("escenario", "cuentas_por_cobrar_abiertas", "cuentas_vencidas", "monto_por_cobrar",
                  "monto_vencido", "morosidad_monto_pct", "morosidad_cuentas_pct"),
        paginada=False,
    ),
    "ranking-productos": Vista(
        nombre="vw_ranking_productos",
        descripcion="Tarea 27: productos estrella y de baja venta (2010-2020).",
        columnas=("id_producto", "producto", "categoria", "num_facturas", "unidades_vendidas", "ventas", "costo",
                  "margen", "margen_pct", "alerta_escala_etapa2", "rank_ventas", "rank_margen",
                  "clasificacion_desempeno"),
        filtros=("id_producto", "categoria", "clasificacion_desempeno"),
        buscar=("producto", "id_producto"),
        orden=("rank_ventas", "id_producto"),
        booleanos=("alerta_escala_etapa2",),
        extra={"sin_alerta_escala": "alerta_escala_etapa2 = {falso}"},
    ),
    "sustentabilidad": Vista(
        nombre="vw_sustentabilidad_negocio",
        descripcion="Tarea 28: sustentabilidad anual (margen contra gastos y contra lo fiado).",
        columnas=("anio", "cobertura", "ventas", "costo", "margen_bruto", "gastos_insumo",
                  "utilidad_neta_operativa", "monto_fiado", "ratio_margen_sobre_gastos", "pct_ventas_fiadas",
                  "fiado_sobre_margen_pct"),
        filtros=("anio", "cobertura"),
        enteros=("anio",),
        orden=("anio",),
        paginada=False,
    ),
}

VERDADEROS = ("true", "1", "si", "sí")


class ParametroInvalido(Exception):
    pass


def vistas_existentes():
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor, include_views=True))


def _valor(v):
    """NUMERIC de PostgreSQL llega como Decimal: se entrega como número."""
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    return v


class ConsultaVista:
    """Consulta de solo lectura sobre una vista. Se comporta como una lista
    (count + slicing), así la paginación estándar de la API funciona igual."""

    def __init__(self, vista, params):
        self.vista = vista
        condiciones, self.valores = [], []

        for columna in vista.filtros:
            valor = (params.get(columna) or "").strip()
            if not valor:
                continue
            if columna in vista.enteros:
                if not valor.lstrip("-").isdigit():
                    raise ParametroInvalido(f"'{columna}' debe ser un número entero.")
                valor = int(valor)
            condiciones.append(f"{columna} = %s")
            self.valores.append(valor)

        buscar = (params.get("search") or "").strip()
        if buscar and vista.buscar:
            condiciones.append("(" + " OR ".join(f"LOWER({c}) LIKE %s" for c in vista.buscar) + ")")
            self.valores += [f"%{buscar.lower()}%"] * len(vista.buscar)

        falso = "FALSE" if connection.vendor == "postgresql" else "0"
        for parametro, condicion in vista.extra.items():
            if (params.get(parametro) or "").strip().lower() in VERDADEROS:
                condiciones.append(condicion.format(falso=falso))

        self.where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
        self.order_by = self._orden(params.get("ordering"))

    def _orden(self, ordering):
        campos = [c.strip() for c in ordering.split(",") if c.strip()] if ordering else list(self.vista.orden)
        partes = []
        for campo in campos:
            columna = campo.lstrip("-")
            if columna not in self.vista.columnas:
                raise ParametroInvalido(
                    f"'ordering' inválido. Usa: {', '.join(self.vista.columnas)} (con '-' para mayor a menor)."
                )
            partes.append(f"{columna} {'DESC' if campo.startswith('-') else 'ASC'}")
        return (" ORDER BY " + ", ".join(partes)) if partes else ""

    def _filas(self, sql, valores):
        with connection.cursor() as cursor:
            cursor.execute(sql, valores)
            nombres = [c[0] for c in cursor.description]
            filas = []
            for fila in cursor.fetchall():
                dato = {n: _valor(v) for n, v in zip(nombres, fila)}
                for columna in self.vista.booleanos:
                    if dato.get(columna) is not None:
                        dato[columna] = bool(dato[columna])
                filas.append(dato)
            return filas

    def count(self):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {self.vista.nombre}{self.where}", self.valores)
            return cursor.fetchone()[0]

    __len__ = count

    def todas(self):
        return self._filas(f"SELECT * FROM {self.vista.nombre}{self.where}{self.order_by}", self.valores)

    def __getitem__(self, rango):
        inicio, fin = rango.start or 0, rango.stop
        return self._filas(
            f"SELECT * FROM {self.vista.nombre}{self.where}{self.order_by} LIMIT %s OFFSET %s",
            self.valores + [fin - inicio, inicio],
        )


class MetricaView(APIView):
    """
    GET /api/finanzas/metricas/<nombre>/
    Devuelve las filas de una vista del equipo de datos, con los mismos nombres de columna.
    Parámetros: los filtros de cada vista (ver GET /api/finanzas/metricas/), `search`,
    `ordering` y, en las paginadas, `page` y `page_size`.
    """

    def get(self, request, nombre):
        vista = VISTAS.get(nombre)
        if vista is None:
            return Response({"error": f"Métrica desconocida. Usa: {', '.join(VISTAS)}."}, status=404)
        if vista.nombre not in vistas_existentes():
            return Response({"error": MENSAJE_SIN_VISTAS}, status=503)
        try:
            consulta = ConsultaVista(vista, request.query_params)
        except ParametroInvalido as error:
            return Response({"error": str(error)}, status=400)

        if not vista.paginada:
            return Response({"vista": vista.nombre, "results": consulta.todas()})
        paginador = StandardResultsSetPagination()
        pagina = paginador.paginate_queryset(consulta, request, view=self)
        return paginador.get_paginated_response(pagina)


class MetricasCatalogoView(APIView):
    """GET /api/finanzas/metricas/ → lista de métricas disponibles, con sus filtros y columnas."""

    def get(self, request):
        base = request.build_absolute_uri(request.path).rstrip("/")
        existentes = vistas_existentes()
        return Response({
            "descripcion": "Vistas de análisis del equipo de datos (Etapa 5). Son las mismas que usa Power BI.",
            "metricas": {
                nombre: {
                    "url": f"{base}/{nombre}/",
                    "vista": vista.nombre,
                    "disponible": vista.nombre in existentes,
                    "descripcion": vista.descripcion,
                    "paginada": vista.paginada,
                    "filtros": list(vista.filtros) + list(vista.extra) + (["search"] if vista.buscar else []),
                    "columnas": list(vista.columnas),
                }
                for nombre, vista in VISTAS.items()
            },
        })
