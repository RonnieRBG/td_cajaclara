"""
Caja Clara — Etapa 5: Análisis y Métricas (Tareas 22 a 28).

Ejecuta las vistas SQL analíticas sobre la base relacional de Etapa 4 (`cajaclara_local.db`),
exporta tablas de resultados en CSV y genera gráficos ejecutivos de respaldo.
"""

from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import tempfile

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "mpl_cajaclara"))

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "Etapa_4_Carga_y_Nube" / "cajaclara_local.db"
VISTAS_SQL_PATH = BASE_DIR / "vistas_metricas_sqlite.sql"
RES_DIR = BASE_DIR / "resultados"
GRAF_DIR = BASE_DIR / "graficos"


def fmt_moneda(val: float, _pos: int = 0) -> str:
    """Formatea valores numéricos en pesos chilenos abreviados para ejes."""
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:,.1f}M".replace(",", ".")
    if abs(val) >= 1_000:
        return f"${val / 1_000:,.0f}k".replace(",", ".")
    return f"${val:,.0f}".replace(",", ".")


def aplicar_vistas(conn: sqlite3.Connection) -> None:
    """Crea o reemplaza las 7 vistas analíticas de Etapa 5 en SQLite."""
    conn.executescript(VISTAS_SQL_PATH.read_text(encoding="utf-8"))
    conn.commit()


def ejecutar_analisis() -> dict:
    """Ejecuta las consultas de Tareas 22-28, exporta CSVs y construye gráficos."""
    RES_DIR.mkdir(parents=True, exist_ok=True)
    GRAF_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        aplicar_vistas(conn)

        # ── Tarea 22: Margen por categoría y período (cobertura completa 2010-2020) ──
        margen_cat = pd.read_sql_query(
            """
            SELECT
                categoria,
                SUM(num_facturas) AS facturas,
                SUM(unidades) AS unidades,
                SUM(ventas) AS ventas,
                SUM(costo) AS costo,
                SUM(margen) AS margen,
                ROUND(CAST(SUM(margen) AS REAL) / NULLIF(SUM(ventas), 0) * 100, 2) AS margen_pct
            FROM vw_margen_producto_categoria
            WHERE cobertura = 'completa'
            GROUP BY categoria
            ORDER BY margen DESC;
            """,
            conn,
        )
        margen_cat.to_csv(RES_DIR / "t22_margen_por_categoria_completa.csv", index=False, encoding="utf-8-sig")

        margen_prod_anual = pd.read_sql_query(
            """
            SELECT anio, categoria, id_producto, producto, unidades, ventas, costo, margen, margen_pct
            FROM (
                SELECT
                    anio, categoria, id_producto, producto,
                    SUM(unidades) AS unidades,
                    SUM(ventas) AS ventas,
                    SUM(costo) AS costo,
                    SUM(margen) AS margen,
                    ROUND(CAST(SUM(margen) AS REAL) / NULLIF(SUM(ventas), 0) * 100, 2) AS margen_pct
                FROM vw_margen_producto_categoria
                WHERE cobertura = 'completa'
                GROUP BY anio, categoria, id_producto, producto
            )
            ORDER BY anio DESC, margen DESC;
            """,
            conn,
        )
        margen_prod_anual.to_csv(RES_DIR / "t22_margen_producto_anual_completa.csv", index=False, encoding="utf-8-sig")

        # ── Tarea 23: Ventas por categoría y mes ──────────────────────────────────────
        ventas_cat_mes = pd.read_sql_query(
            "SELECT * FROM vw_ventas_categoria_mes ORDER BY periodo, ventas DESC;",
            conn,
        )
        ventas_cat_mes.to_csv(RES_DIR / "t23_ventas_categoria_mes.csv", index=False, encoding="utf-8-sig")

        # ── Tarea 24: Flujo de caja mensual ──────────────────────────────────────────
        flujo_caja = pd.read_sql_query(
            "SELECT * FROM vw_flujo_caja_mensual ORDER BY periodo;",
            conn,
        )
        flujo_caja.to_csv(RES_DIR / "t24_flujo_caja_mensual.csv", index=False, encoding="utf-8-sig")

        flujo_anual = (
            flujo_caja[flujo_caja["cobertura"] == "completa"]
            .groupby("anio", as_index=False)[
                [
                    "ventas_facturadas",
                    "ingresos_contado",
                    "ventas_fiadas",
                    "cobros_fiado_recibidos",
                    "ingresos_efectivamente_cobrados",
                    "gastos_insumo",
                    "flujo_caja_neto",
                ]
            ]
            .sum()
        )
        flujo_anual.to_csv(RES_DIR / "t24_flujo_caja_anual_completa.csv", index=False, encoding="utf-8-sig")

        # ── Tarea 25: Cuentas por cobrar por cliente ─────────────────────────────────
        cxc_clientes = pd.read_sql_query(
            "SELECT * FROM vw_cuentas_por_cobrar_cliente ORDER BY monto_adeudado_actual DESC, monto_total_fiado DESC;",
            conn,
        )
        cxc_clientes.to_csv(RES_DIR / "t25_cuentas_por_cobrar_por_cliente.csv", index=False, encoding="utf-8-sig")

        cxc_abiertas_detalle = pd.read_sql_query(
            """
            SELECT
                cxc.id_cuenta,
                cxc.id_factura,
                c.id_cliente,
                c.nombre AS cliente,
                c.contacto,
                v.fecha AS fecha_venta,
                cxc.fecha_vencimiento,
                cxc.monto,
                cxc.estado,
                CASE
                    WHEN cxc.estado = 'VENCIDA'
                        THEN CAST(julianday('2022-09-01') - julianday(cxc.fecha_vencimiento) AS INTEGER)
                    ELSE 0
                END AS dias_atraso
            FROM cuenta_por_cobrar cxc
            JOIN cliente c ON c.id_cliente = cxc.id_cliente
            JOIN venta v ON v.id_factura = cxc.id_factura
            WHERE cxc.estado IN ('PENDIENTE', 'VENCIDA')
            ORDER BY dias_atraso DESC, cxc.fecha_vencimiento ASC;
            """,
            conn,
        )
        cxc_abiertas_detalle.to_csv(RES_DIR / "t25_detalle_cartera_abierta_2022_09.csv", index=False, encoding="utf-8-sig")

        cxc_abiertas_2020 = pd.read_sql_query(
            """
            SELECT
                cxc.id_cuenta,
                cxc.id_factura,
                c.id_cliente,
                c.nombre AS cliente,
                c.contacto,
                v.fecha AS fecha_venta,
                cxc.fecha_vencimiento,
                cxc.monto,
                CASE
                    WHEN cxc.fecha_vencimiento <= '2020-12-31' THEN 'VENCIDA'
                    ELSE 'PENDIENTE'
                END AS estado_al_corte_2020,
                CASE
                    WHEN cxc.fecha_vencimiento <= '2020-12-31'
                        THEN CAST(julianday('2020-12-31') - julianday(cxc.fecha_vencimiento) AS INTEGER)
                    ELSE 0
                END AS dias_atraso_al_2020_12_31
            FROM cuenta_por_cobrar cxc
            JOIN cliente c ON c.id_cliente = cxc.id_cliente
            JOIN venta v ON v.id_factura = cxc.id_factura
            WHERE v.fecha <= '2020-12-31'
              AND (cxc.fecha_pago IS NULL OR cxc.fecha_pago > '2020-12-31')
            ORDER BY dias_atraso_al_2020_12_31 DESC, cxc.fecha_vencimiento ASC;
            """,
            conn,
        )
        cxc_abiertas_2020.to_csv(RES_DIR / "t25_detalle_cartera_abierta_2020_12.csv", index=False, encoding="utf-8-sig")

        # ── Tarea 26: Indicador de morosidad ─────────────────────────────────────────
        morosidad = pd.read_sql_query("SELECT * FROM vw_indicador_morosidad;", conn)
        morosidad.to_csv(RES_DIR / "t26_indicador_morosidad.csv", index=False, encoding="utf-8-sig")

        # ── Tarea 27: Productos estrella y de baja venta ─────────────────────────────
        ranking = pd.read_sql_query("SELECT * FROM vw_ranking_productos ORDER BY rank_ventas;", conn)
        ranking.to_csv(RES_DIR / "t27_ranking_productos_completa.csv", index=False, encoding="utf-8-sig")

        cuadrantes = (
            ranking.groupby("clasificacion_desempeno", as_index=False)
            .agg(
                productos=("id_producto", "count"),
                unidades=("unidades_vendidas", "sum"),
                ventas=("ventas", "sum"),
                margen=("margen", "sum"),
            )
            .assign(
                pct_ventas=lambda d: (d["ventas"] / d["ventas"].sum() * 100).round(2),
                pct_margen=lambda d: (d["margen"] / d["margen"].sum() * 100).round(2),
            )
            .sort_values("ventas", ascending=False)
        )
        cuadrantes.to_csv(RES_DIR / "t27_resumen_cuadrantes_productos.csv", index=False, encoding="utf-8-sig")

        # ── Tarea 28: Sustentabilidad del negocio ────────────────────────────────────
        sustentabilidad = pd.read_sql_query("SELECT * FROM vw_sustentabilidad_negocio;", conn)
        sustentabilidad.to_csv(RES_DIR / "t28_sustentabilidad_anual.csv", index=False, encoding="utf-8-sig")

        # ── Generación de gráficos ejecutivos ────────────────────────────────────────
        plt.rcParams["axes.spines.top"] = False
        plt.rcParams["axes.spines.right"] = False

        # Gráfico 1: Ventas vs Margen por Categoría (Cobertura Completa 2010-2020)
        fig, ax = plt.subplots(figsize=(11, 6))
        df_plot = margen_cat.sort_values("ventas", ascending=True)
        y = np.arange(len(df_plot))
        ax.barh(y + 0.18, df_plot["ventas"], height=0.36, label="Ventas", color="#1f77b4")
        ax.barh(y - 0.18, df_plot["margen"], height=0.36, label="Margen Bruto", color="#2ca02c")
        ax.set_yticks(y)
        ax.set_yticklabels(df_plot["categoria"])
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(fmt_moneda))
        for idx, (_, row) in enumerate(df_plot.iterrows()):
            ax.text(
                row["margen"] + 800_000,
                idx - 0.23,
                f"{row['margen_pct']:.1f}%",
                fontsize=8.5,
                color="#1b6e1b",
                va="center",
            )
        ax.set_title("Ventas y Margen Bruto por Categoría (Cobertura Completa 2010–2020)", fontsize=13, fontweight="bold")
        ax.set_xlabel("Monto ($)")
        ax.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(GRAF_DIR / "01_margen_y_ventas_categoria.png", dpi=150)
        plt.close()

        # Gráfico 2: Flujo de Caja Anual y Comparativa Mensual 2020 (Facturado vs Cobrado vs Gastos)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))
        ax1.bar(flujo_anual["anio"] - 0.2, flujo_anual["ventas_facturadas"], width=0.38, label="Vendido (Facturado)", color="#4c78a8")
        ax1.bar(flujo_anual["anio"] + 0.2, flujo_anual["ingresos_efectivamente_cobrados"], width=0.38, label="Efectivamente Cobrado", color="#54a24b")
        ax1.plot(flujo_anual["anio"], flujo_anual["gastos_insumo"], color="#e45756", marker="o", linewidth=2, label="Gastos Insumo")
        ax1.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_moneda))
        ax1.set_xticks(flujo_anual["anio"])
        ax1.tick_params(axis="x", rotation=45)
        ax1.set_title("Anual 2010–2020: Facturado vs Cobrado y Gastos", fontweight="bold")
        ax1.legend(fontsize=8.5)

        fc_2020 = flujo_caja[flujo_caja["anio"] == 2020].sort_values("mes")
        ax2.plot(fc_2020["mes"], fc_2020["ventas_facturadas"], marker="s", label="Facturado Mes", color="#4c78a8")
        ax2.plot(fc_2020["mes"], fc_2020["ingresos_efectivamente_cobrados"], marker="o", label="Cobrado Real Mes", color="#54a24b")
        ax2.bar(fc_2020["mes"], fc_2020["flujo_caja_neto"], alpha=0.25, color="#2ca02c", label="Flujo Caja Neto")
        ax2.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_moneda))
        ax2.set_xticks(range(1, 13))
        ax2.set_title("Detalle Mensual 2020: Desfase Ventas vs Cobro Real", fontweight="bold")
        ax2.set_xlabel("Mes (2020)")
        ax2.legend(fontsize=8.5)
        plt.tight_layout()
        plt.savefig(GRAF_DIR / "02_flujo_caja_mensual.png", dpi=150)
        plt.close()

        # Gráfico 3: Morosidad por Escenario y Distribución de Días de Atraso
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
        esc_labels = [
            "Corte Final\n(2022-09-01)",
            "Cierre Completo\n(2020-12-31)",
            "Histórico Pagos\ncon Atraso",
        ]
        x = np.arange(len(esc_labels))
        ax1.bar(x - 0.18, morosidad["morosidad_monto_pct"], width=0.34, label="% Sobre Monto", color="#e45756")
        ax1.bar(x + 0.18, morosidad["morosidad_cuentas_pct"], width=0.34, label="% Sobre Cuentas", color="#f58518")
        for idx, r in morosidad.iterrows():
            ax1.text(idx - 0.18, r["morosidad_monto_pct"] + 1.5, f"{r['morosidad_monto_pct']:.1f}%", ha="center", fontsize=9)
            ax1.text(idx + 0.18, r["morosidad_cuentas_pct"] + 1.5, f"{r['morosidad_cuentas_pct']:.1f}%", ha="center", fontsize=9)
        ax1.set_xticks(x)
        ax1.set_xticklabels(esc_labels)
        ax1.set_ylim(0, 100)
        ax1.set_ylabel("Morosidad (%)")
        ax1.set_title("Indicador de Morosidad por Escenario", fontweight="bold")
        ax1.legend()

        atrasos_hist = pd.read_sql_query(
            """
            SELECT CAST(julianday(fecha_pago) - julianday(fecha_vencimiento) AS INTEGER) AS dias_atraso
            FROM cuenta_por_cobrar
            WHERE estado = 'PAGADA' AND fecha_pago > fecha_vencimiento;
            """,
            conn,
        )
        ax2.hist(atrasos_hist["dias_atraso"], bins=20, color="#f58518", edgecolor="white")
        ax2.set_title(f"Distribución Días de Atraso (n={len(atrasos_hist):,} pagos tardíos)".replace(",", "."), fontweight="bold")
        ax2.set_xlabel("Días de atraso respecto al vencimiento")
        ax2.set_ylabel("Cantidad de cuentas")
        plt.tight_layout()
        plt.savefig(GRAF_DIR / "03_morosidad_y_cartera_clientes.png", dpi=150)
        plt.close()

        # Gráfico 4: Matriz de Productos (Estrella vs Baja Venta) y Sustentabilidad Anual
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.5))
        colores = {
            "Estrella": "#2ca02c",
            "Alto volumen / Bajo margen": "#1f77b4",
            "Nicho rentable": "#9467bd",
            "Baja venta": "#bdbdbd",
        }
        for clase, grp in ranking.groupby("clasificacion_desempeno"):
            ax1.scatter(
                grp["ventas"],
                grp["margen"],
                s=14,
                alpha=0.55,
                label=f"{clase} ({len(grp):,})".replace(",", "."),
                color=colores.get(clase, "#333"),
            )
        ax1.set_xscale("log")
        ax1.set_yscale("log")
        ax1.set_title("Segmentación de Productos (Ventas vs Margen, escala log)", fontweight="bold")
        ax1.set_xlabel("Ventas totales del producto (log)")
        ax1.set_ylabel("Margen bruto total (log)")
        ax1.legend(fontsize=8)

        sust_comp = sustentabilidad[sustentabilidad["cobertura"] == "completa"]
        ax2.bar(sust_comp["anio"], sust_comp["margen_bruto"], label="Margen Bruto", color="#2ca02c", alpha=0.85)
        ax2.bar(sust_comp["anio"], sust_comp["monto_fiado"], width=0.45, label="Monto Vendido Fiado", color="#f58518", alpha=0.9)
        ax2.plot(sust_comp["anio"], sust_comp["gastos_insumo"], color="#e45756", marker="o", linewidth=2, label="Gastos Insumo")
        ax2.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_moneda))
        ax2.set_xticks(sust_comp["anio"])
        ax2.tick_params(axis="x", rotation=45)
        ax2.set_title("Sustentabilidad 2010–2020: Margen vs Gastos vs Fiado", fontweight="bold")
        ax2.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(GRAF_DIR / "04_ranking_productos_y_sustentabilidad.png", dpi=150)
        plt.close()

        # Resumen numérico exacto para trazabilidad
        sust_tot_comp = sustentabilidad[sustentabilidad["cobertura"] == "completa"].sum(numeric_only=True)
        sust_tot_all = sustentabilidad.sum(numeric_only=True)
        top_estrellas = ranking[ranking["alerta_escala_etapa2"] == 0].head(10)[
            ["id_producto", "producto", "categoria", "unidades_vendidas", "ventas", "margen", "margen_pct"]
        ]
        baja_venta = (
            ranking[(ranking["clasificacion_desempeno"] == "Baja venta") & (ranking["alerta_escala_etapa2"] == 0)]
            .sort_values(["ventas", "margen"], ascending=[True, True])
            .head(10)[["id_producto", "producto", "categoria", "unidades_vendidas", "ventas", "margen", "margen_pct"]]
        )
        reajuste = (
            ranking[(ranking["clasificacion_desempeno"] == "Alto volumen / Bajo margen") & (ranking["alerta_escala_etapa2"] == 0)]
            .sort_values("ventas", ascending=False)
            .head(10)[["id_producto", "producto", "categoria", "unidades_vendidas", "ventas", "margen", "margen_pct"]]
        )

        resumen = {
            "margen_por_categoria_completa": margen_cat.to_dict(orient="records"),
            "flujo_anual_completa": flujo_anual.to_dict(orient="records"),
            "morosidad": morosidad.to_dict(orient="records"),
            "cartera_abierta_2022_09": cxc_abiertas_detalle.to_dict(orient="records"),
            "cartera_abierta_2020_12_resumen": {
                "cuentas": int(len(cxc_abiertas_2020)),
                "monto_total": int(cxc_abiertas_2020["monto"].sum()),
                "vencidas_cuentas": int((cxc_abiertas_2020["estado_al_corte_2020"] == "VENCIDA").sum()),
                "vencidas_monto": int(cxc_abiertas_2020.loc[cxc_abiertas_2020["estado_al_corte_2020"] == "VENCIDA", "monto"].sum()),
                "pendientes_cuentas": int((cxc_abiertas_2020["estado_al_corte_2020"] == "PENDIENTE").sum()),
                "pendientes_monto": int(cxc_abiertas_2020.loc[cxc_abiertas_2020["estado_al_corte_2020"] == "PENDIENTE", "monto"].sum()),
                "promedio_dias_atraso_vencidas": round(float(cxc_abiertas_2020.loc[cxc_abiertas_2020["estado_al_corte_2020"] == "VENCIDA", "dias_atraso_al_2020_12_31"].mean()), 1),
            },
            "cuadrantes_productos": cuadrantes.to_dict(orient="records"),
            "top_10_estrella_sin_artefacto": top_estrellas.to_dict(orient="records"),
            "top_10_baja_venta": baja_venta.to_dict(orient="records"),
            "top_10_reajuste_precio": reajuste.to_dict(orient="records"),
            "sustentabilidad_completa_2010_2020": {
                "ventas": int(sust_tot_comp["ventas"]),
                "costo": int(sust_tot_comp["costo"]),
                "margen_bruto": int(sust_tot_comp["margen_bruto"]),
                "gastos_insumo": int(sust_tot_comp["gastos_insumo"]),
                "utilidad_neta_operativa": int(sust_tot_comp["utilidad_neta_operativa"]),
                "monto_fiado": int(sust_tot_comp["monto_fiado"]),
                "ratio_margen_sobre_gastos": round(float(sust_tot_comp["margen_bruto"] / sust_tot_comp["gastos_insumo"]), 2),
                "fiado_sobre_margen_pct": round(float(sust_tot_comp["monto_fiado"] / sust_tot_comp["margen_bruto"] * 100), 2),
            },
            "sustentabilidad_total_2010_2022": {
                "ventas": int(sust_tot_all["ventas"]),
                "margen_bruto": int(sust_tot_all["margen_bruto"]),
                "gastos_insumo": int(sust_tot_all["gastos_insumo"]),
                "utilidad_neta_operativa": int(sust_tot_all["utilidad_neta_operativa"]),
                "monto_fiado": int(sust_tot_all["monto_fiado"]),
            },
            "top_5_clientes_historico_fiado": cxc_clientes.sort_values("monto_total_fiado", ascending=False).head(5)[
                ["id_cliente", "nombre", "total_cuentas_fiadas", "monto_total_fiado", "promedio_dias_atraso_historico"]
            ].to_dict(orient="records"),
        }
        (RES_DIR / "resumen_metricas_etapa5.json").write_text(
            json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return resumen
    finally:
        conn.close()


if __name__ == "__main__":
    res = ejecutar_analisis()
    print(json.dumps(res, indent=2, ensure_ascii=False))
