"""
Caja Clara — Etapa 6: Validación de Alertas de Cobro y Vistas Analíticas (Tareas 29 y 30).

1. Aplica `alertas_cobro_sqlite.sql` (`vw_alertas_cobro`) sobre `cajaclara_local.db`.
2. Ejecuta la consulta parametrizada de alertas vencidas / próximas a vencer para Python.
3. Reconcilia los totales de `vw_alertas_cobro` con `vw_indicador_morosidad` y verifica
   que las 7 vistas analíticas de Etapa 5 estén presentes y operativas.
4. Exporta CSVs de respaldo y `validacion_etapa6.json`.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3

import pandas as pd

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "Etapa_4_Carga_y_Nube" / "cajaclara_local.db"
SQL_ALERTAS_PATH = BASE_DIR / "alertas_cobro_sqlite.sql"
RES_DIR = BASE_DIR / "resultados"

VISTAS_ETAPA5_ESPERADAS = [
    "vw_margen_producto_categoria",
    "vw_ventas_categoria_mes",
    "vw_flujo_caja_mensual",
    "vw_cuentas_por_cobrar_cliente",
    "vw_indicador_morosidad",
    "vw_ranking_productos",
    "vw_sustentabilidad_negocio",
]

QUERY_ALERTAS_PYTHON = """
SELECT
    cxc.id_cuenta,
    cxc.id_factura,
    c.id_cliente,
    c.nombre AS cliente_nombre,
    c.contacto AS cliente_contacto,
    cxc.fecha_vencimiento,
    cxc.estado,
    cxc.monto AS monto,
    CAST(julianday(cxc.fecha_vencimiento) - julianday(?) AS INTEGER) AS dias_para_vencer,
    CASE
        WHEN cxc.fecha_vencimiento < ? THEN 'VENCIDA'
        ELSE 'PROXIMA_A_VENCER'
    END AS tipo_alerta
FROM cuenta_por_cobrar cxc
JOIN cliente c ON c.id_cliente = cxc.id_cliente
WHERE cxc.estado IN ('PENDIENTE', 'VENCIDA')
  AND cxc.fecha_pago IS NULL
  AND julianday(cxc.fecha_vencimiento) <= julianday(?) + ?
ORDER BY
    CASE WHEN cxc.fecha_vencimiento < ? THEN 0 ELSE 1 END,
    cxc.fecha_vencimiento ASC,
    cxc.monto DESC;
"""


def obtener_alertas_cobro(
    conn: sqlite3.Connection,
    fecha_corte: str = "2022-09-01",
    dias_aviso: int = 15,
) -> pd.DataFrame:
    """Consulta reutilizable para backend Python/Django (vencidas + próximas a vencer)."""
    return pd.read_sql_query(
        QUERY_ALERTAS_PYTHON,
        conn,
        params=(fecha_corte, fecha_corte, fecha_corte, dias_aviso, fecha_corte),
    )


def ejecutar_validacion() -> dict:
    """Valida alertas (Tarea 29) y vistas SQL de métricas (Tarea 30)."""
    RES_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SQL_ALERTAS_PATH.read_text(encoding="utf-8"))
        conn.commit()

        vistas_existentes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'view';"
            ).fetchall()
        }
        faltantes = [v for v in [*VISTAS_ETAPA5_ESPERADAS, "vw_alertas_cobro"] if v not in vistas_existentes]
        assert not faltantes, f"Vistas faltantes en SQLite: {faltantes}"

        conteos_vistas = {
            vista: conn.execute(f"SELECT COUNT(*) FROM {vista};").fetchone()[0]
            for vista in [*VISTAS_ETAPA5_ESPERADAS, "vw_alertas_cobro"]
        }

        alertas_df = pd.read_sql_query(
            """
            SELECT *
            FROM vw_alertas_cobro
            ORDER BY prioridad_alerta ASC, fecha_vencimiento ASC, monto DESC;
            """,
            conn,
        )
        alertas_df.to_csv(RES_DIR / "t29_alertas_cobro.csv", index=False, encoding="utf-8-sig")

        resumen_df = pd.read_sql_query(
            """
            SELECT
                prioridad_alerta,
                ventana_alerta,
                COUNT(*) AS cuentas,
                SUM(monto) AS monto_total
            FROM vw_alertas_cobro
            GROUP BY prioridad_alerta, ventana_alerta
            ORDER BY prioridad_alerta;
            """,
            conn,
        )
        resumen_df.to_csv(RES_DIR / "t29_resumen_prioridades.csv", index=False, encoding="utf-8-sig")

        alertas_python_df = obtener_alertas_cobro(conn, fecha_corte="2022-09-01", dias_aviso=15)

        morosidad_corte = conn.execute(
            """
            SELECT cuentas_por_cobrar_abiertas, cuentas_vencidas, monto_por_cobrar, monto_vencido
            FROM vw_indicador_morosidad
            WHERE escenario = 'Corte Final Dataset (2022-09-01)';
            """
        ).fetchone()
        assert morosidad_corte is not None, "No existe escenario de corte en vw_indicador_morosidad"

        total_abiertas = int(len(alertas_df))
        total_vencidas = int((alertas_df["tipo_alerta"] == "VENCIDA").sum())
        total_monto_abierto = int(alertas_df["monto"].sum())
        total_monto_vencido = int(alertas_df.loc[alertas_df["tipo_alerta"] == "VENCIDA", "monto"].sum())

        assert (total_abiertas, total_vencidas, total_monto_abierto, total_monto_vencido) == tuple(morosidad_corte), (
            f"Descuadre entre vw_alertas_cobro {(total_abiertas, total_vencidas, total_monto_abierto, total_monto_vencido)} "
            f"y vw_indicador_morosidad {morosidad_corte}"
        )
        assert len(alertas_python_df) == total_abiertas, "Consulta Python debe capturar todas las alertas <= 15 días"

        payload = {
            "fecha_corte_referencia": "2022-09-01",
            "ventana_aviso_dias": 15,
            "vistas_verificadas": conteos_vistas,
            "reconciliacion_morosidad": {
                "cuentas_abiertas": total_abiertas,
                "cuentas_vencidas": total_vencidas,
                "cuentas_por_vencer_15d": total_abiertas - total_vencidas,
                "monto_abierto": total_monto_abierto,
                "monto_vencido": total_monto_vencido,
                "monto_por_vencer": total_monto_abierto - total_monto_vencido,
                "coincide_con_vw_indicador_morosidad": True,
            },
            "resumen_prioridades": resumen_df.to_dict(orient="records"),
            "alertas": alertas_df[
                [
                    "id_cuenta",
                    "id_factura",
                    "id_cliente",
                    "cliente_nombre",
                    "cliente_contacto",
                    "fecha_vencimiento",
                    "estado",
                    "monto",
                    "dias_para_vencer",
                    "dias_atraso",
                    "prioridad_alerta",
                ]
            ].to_dict(orient="records"),
        }
        (RES_DIR / "validacion_etapa6.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return payload
    finally:
        conn.close()


if __name__ == "__main__":
    resultado = ejecutar_validacion()
    print(json.dumps(resultado["reconciliacion_morosidad"], indent=2, ensure_ascii=False))
    print("Vistas verificadas:", resultado["vistas_verificadas"])
