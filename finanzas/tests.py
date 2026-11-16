"""
Pruebas de registro de ventas, pagos y gastos, del flujo de caja y del importador.
Ejecutar con: python manage.py test finanzas
"""

import csv
import tempfile
from datetime import date, timedelta
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Cliente, CuentaPorCobrar, DetalleVenta, GastoInsumo, Producto, Venta


class BaseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user("cajera", password="x"))
        self.p1 = Producto.objects.create(id_producto="P1", producto="Aceite 1L", categoria="Abarrotes", unidad_negocio="Supermercado")
        self.p2 = Producto.objects.create(id_producto="P2", producto="Arroz 1kg", categoria="Abarrotes", unidad_negocio="Supermercado")
        self.cliente = Cliente.objects.create(id_cliente=1, nombre="Almacén San Pedro", contacto="+56 9 1234 5678")
        self.hoy = timezone.localdate()

    # Atajos
    def vender(self, **datos):
        datos.setdefault("items", [{"id_producto": "P1", "cantidad": 2, "precio_venta": 1000, "costo_venta": 600}])
        datos.setdefault("id_cliente", 1)
        return self.client.post("/api/finanzas/facturas/", datos, format="json")

    def vender_a_credito(self, dias=10, **datos):
        datos.update(por_cobrar=True, fecha_vencimiento=str(self.hoy + timedelta(days=dias)))
        return self.vender(**datos)

    def cuenta_de(self, respuesta):
        return respuesta.json()["cuenta_por_cobrar"]["id_cuenta"]

    def pagar(self, id_cuenta, **datos):
        return self.client.post(f"/api/finanzas/cuentas-por-cobrar/{id_cuenta}/pagar/", datos, format="json")


class RegistrarVentaTests(BaseAPITest):
    def test_venta_al_contado(self):
        r = self.vender(items=[
            {"id_producto": "P1", "cantidad": 2, "precio_venta": 1000, "costo_venta": 600},
            {"id_producto": "P2", "cantidad": 1, "precio_venta": 450, "costo_venta": 300},
        ])
        self.assertEqual(r.status_code, 201, r.content)
        datos = r.json()
        self.assertTrue(datos["id_factura"].startswith("CC"))
        self.assertLessEqual(len(datos["id_factura"]), 30)
        self.assertEqual(datos["total_venta"], 2450)  # 2×1000 + 1×450, entero
        self.assertEqual(datos["tipo_compra"], "Física")
        self.assertEqual(datos["estado_pago"], "PAGADO")
        self.assertIsNone(datos["cuenta_por_cobrar"])
        self.assertEqual([d["id_detalle"] for d in datos["detalles"]], [1, 2])  # ID asignados por el backend
        self.assertEqual(self.client.get(f"/api/finanzas/ventas/?factura={datos['id_factura']}").json()["count"], 2)
        self.assertEqual(self.client.get(f"/api/finanzas/facturas/{datos['id_factura']}/").status_code, 200)

    def test_precio_y_costo_de_la_ultima_venta(self):
        self.vender(fecha=str(self.hoy - timedelta(days=5)), items=[
            {"id_producto": "P1", "cantidad": 1, "precio_venta": 900, "costo_venta": 500}])
        self.vender(fecha=str(self.hoy - timedelta(days=1)), items=[
            {"id_producto": "P1", "cantidad": 1, "precio_venta": 1100, "costo_venta": 650}])
        r = self.vender(items=[{"id_producto": "P1", "cantidad": 3}])
        self.assertEqual(r.status_code, 201, r.content)
        linea = r.json()["detalles"][0]
        self.assertEqual((linea["precio_venta"], linea["costo_venta"]), (1100, 650))
        # Un producto que nunca se vendió necesita precio y costo
        r = self.vender(items=[{"id_producto": "P2", "cantidad": 1}])
        self.assertEqual(r.status_code, 400)
        self.assertIn("nunca se ha vendido", r.json()["error"])

    def test_tipo_compra_acepta_varias_formas(self):
        for valor in ("En Línea", "en linea", "ONLINE"):
            with self.subTest(valor):
                r = self.vender(tipo_compra=valor)
                self.assertEqual(r.status_code, 201, r.content)
                self.assertEqual(r.json()["tipo_compra"], "En Línea")
        self.assertEqual(self.client.get("/api/finanzas/facturas/?tipo_compra=online").json()["count"], 3)

    def test_venta_a_credito_crea_su_cuenta(self):
        r = self.vender_a_credito()
        self.assertEqual(r.status_code, 201, r.content)
        datos = r.json()
        self.assertEqual(datos["estado_pago"], "PENDIENTE")
        self.assertEqual(datos["cuenta_por_cobrar"]["monto"], 2000)
        self.assertEqual(datos["cuenta_por_cobrar"]["estado"], "PENDIENTE")
        self.assertEqual(datos["cuenta_por_cobrar"]["id_cliente"], 1)
        cliente = self.client.get("/api/finanzas/clientes/?search=San Pedro").json()["results"][0]
        self.assertEqual(cliente["total_deuda"], 2000)
        self.assertEqual(cliente["total_facturas"], 1)

    def test_validaciones_de_venta(self):
        casos = {
            "sin productos": {"items": []},
            "sin cliente": {"id_cliente": None},
            "cliente inexistente": {"id_cliente": 999},
            "producto inexistente": {"items": [{"id_producto": "NO-EXISTE", "cantidad": 1}]},
            "cantidad cero": {"items": [{"id_producto": "P1", "cantidad": 0, "precio_venta": 1, "costo_venta": 1}]},
            "precio cero": {"items": [{"id_producto": "P1", "cantidad": 1, "precio_venta": 0, "costo_venta": 1}]},
            "crédito sin vencimiento": {"por_cobrar": True},
            "contado con vencimiento": {"fecha_vencimiento": str(self.hoy)},
            "canal inválido": {"tipo_compra": "TELEFONO"},
        }
        for nombre, datos in casos.items():
            with self.subTest(nombre):
                self.assertEqual(self.vender(**datos).status_code, 400)
        r = self.vender(por_cobrar=True, fecha_vencimiento=str(self.hoy - timedelta(days=1)))
        self.assertEqual(r.status_code, 400)
        self.assertIn("anterior", r.json()["error"])
        self.assertEqual(Venta.objects.count(), 0)  # nada quedó a medio guardar

    def test_registrar_requiere_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.vender().status_code, 401)

    def test_ids_siguen_la_numeracion_existente(self):
        venta = Venta.objects.create(id_factura="INV1", cliente=self.cliente, fecha=self.hoy, tipo_compra="Física")
        DetalleVenta.objects.create(id_detalle=500, venta=venta, producto=self.p1, cantidad=1, precio_venta=10, costo_venta=5)
        CuentaPorCobrar.objects.create(
            id_cuenta=70, venta=Venta.objects.create(id_factura="INV2", cliente=self.cliente, fecha=self.hoy,
                                                     tipo_compra="Física", por_cobrar=True),
            cliente=self.cliente, monto=10, fecha_vencimiento=self.hoy, estado="PENDIENTE",
        )
        r = self.vender_a_credito()
        self.assertEqual(r.json()["detalles"][0]["id_detalle"], 501)
        self.assertEqual(r.json()["cuenta_por_cobrar"]["id_cuenta"], 71)


class PagosTests(BaseAPITest):
    def test_pagar_y_revertir(self):
        r = self.vender_a_credito()
        id_cuenta, factura = self.cuenta_de(r), r.json()["id_factura"]

        pago = self.pagar(id_cuenta)
        self.assertEqual(pago.status_code, 200, pago.content)
        self.assertEqual(pago.json()["estado"], "PAGADA")
        self.assertEqual(pago.json()["fecha_pago"], str(self.hoy))
        self.assertEqual(self.client.get(f"/api/finanzas/facturas/{factura}/").json()["estado_pago"], "PAGADO")
        cliente = self.client.get("/api/finanzas/clientes/?search=San Pedro").json()["results"][0]
        self.assertEqual(cliente["total_deuda"], 0)

        self.assertEqual(self.pagar(id_cuenta).status_code, 400)  # no se paga dos veces

        revertir = self.client.post(f"/api/finanzas/cuentas-por-cobrar/{id_cuenta}/revertir-pago/")
        self.assertEqual(revertir.status_code, 200)
        self.assertEqual(revertir.json()["estado"], "PENDIENTE")
        self.assertIsNone(revertir.json()["fecha_pago"])
        self.assertEqual(
            self.client.post(f"/api/finanzas/cuentas-por-cobrar/{id_cuenta}/revertir-pago/").status_code, 400
        )

    def test_revertir_una_cuenta_ya_vencida_la_deja_vencida(self):
        r = self.vender_a_credito(fecha=str(self.hoy - timedelta(days=20)), dias=-10)
        id_cuenta = self.cuenta_de(r)
        self.pagar(id_cuenta, fecha_pago=str(self.hoy - timedelta(days=15)))
        revertir = self.client.post(f"/api/finanzas/cuentas-por-cobrar/{id_cuenta}/revertir-pago/")
        self.assertEqual(revertir.json()["estado"], "VENCIDA")

    def test_fechas_de_pago_invalidas(self):
        id_cuenta = self.cuenta_de(self.vender_a_credito())
        self.assertEqual(self.pagar(id_cuenta, fecha_pago=str(self.hoy + timedelta(days=1))).status_code, 400)
        self.assertEqual(self.pagar(id_cuenta, fecha_pago=str(self.hoy - timedelta(days=30))).status_code, 400)
        self.assertEqual(self.client.post("/api/finanzas/cuentas-por-cobrar/9999/pagar/").status_code, 404)

    def test_estados_de_cuentas(self):
        """VENCIDA puede venir guardada (como la deja el equipo de datos) o calcularse
        desde una PENDIENTE cuya fecha ya pasó."""
        def cuenta(id_cuenta, estado, vence, fecha_pago=None):
            venta = Venta.objects.create(id_factura=f"INV{id_cuenta}", cliente=self.cliente,
                                         fecha=self.hoy - timedelta(days=60), tipo_compra="Física", por_cobrar=True)
            CuentaPorCobrar.objects.create(id_cuenta=id_cuenta, venta=venta, cliente=self.cliente, monto=100,
                                           fecha_vencimiento=vence, estado=estado, fecha_pago=fecha_pago)

        cuenta(1, "VENCIDA", self.hoy - timedelta(days=5))
        cuenta(2, "PENDIENTE", self.hoy - timedelta(days=1))  # vencida por fecha
        cuenta(3, "PENDIENTE", self.hoy + timedelta(days=5))
        cuenta(4, "PAGADA", self.hoy - timedelta(days=30), fecha_pago=self.hoy - timedelta(days=40))
        r = self.client.get("/api/finanzas/cuentas-por-cobrar/").json()
        self.assertEqual({c["id_cuenta"]: c["estado_actual"] for c in r["results"]},
                         {1: "VENCIDA", 2: "VENCIDA", 3: "PENDIENTE", 4: "PAGADA"})
        self.assertEqual(r["resumen"]["monto_total_por_cobrar"], 300)
        self.assertEqual(r["resumen"]["por_estado"]["VENCIDA"]["cantidad"], 2)
        self.assertEqual(self.client.get("/api/finanzas/cuentas-por-cobrar/?estado=vencida").json()["count"], 2)
        self.assertEqual(next(c for c in r["results"] if c["id_cuenta"] == 1)["dias_atraso"], 5)


class GastosYClientesTests(BaseAPITest):
    def test_registrar_gastos(self):
        r = self.client.post("/api/finanzas/gastos/", {"id_producto": "P1", "monto": 24000}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json(), {
            "id_gasto": 1, "id_producto": "P1", "producto_nombre": "Aceite 1L", "categoria": "Abarrotes",
            "fecha": str(self.hoy), "monto": 24000,
        })
        for datos in (
            {"monto": 100},  # sin producto (en el esquema de datos todo gasto es de un producto)
            {"id_producto": "NO", "monto": 100},
            {"id_producto": "P1", "monto": 0},
        ):
            with self.subTest(datos):
                self.assertEqual(self.client.post("/api/finanzas/gastos/", datos, format="json").status_code, 400)
        self.assertEqual(GastoInsumo.objects.count(), 1)
        resumen = self.client.get("/api/finanzas/gastos/?categoria=abarrotes").json()["resumen"]
        self.assertEqual(resumen, {"total_registros_gasto": 1, "monto_total_gastos": 24000})

    def test_registrar_cliente(self):
        r = self.client.post("/api/finanzas/clientes/", {"nombre": "Kiosco Don Luis", "contacto": "+56 9 1111"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["id_cliente"], 2)  # sigue la numeración
        self.assertEqual(self.client.post("/api/finanzas/clientes/", {"nombre": "Otro"}, format="json").status_code, 400)
        repetido = self.client.post("/api/finanzas/clientes/", {"nombre": "Otro", "contacto": "+56 9 1111"}, format="json")
        self.assertEqual(repetido.status_code, 400)  # contacto es único


class FlujoDeCajaTests(BaseAPITest):
    """Caso controlado, con montos que se pueden revisar a mano:

    Día D:   venta al contado (física)  2×1000 + 1×450 = 2.450
             venta a crédito (en línea) 1×1000         = 1.000  (no entra a caja ese día)
             gasto en insumos                             700
    Día D+3: el cliente paga la venta a crédito         1.000  (entra a caja)
             gasto en insumos                             300
    """

    def setUp(self):
        super().setUp()
        self.d = self.hoy - timedelta(days=10)
        self.vender(fecha=str(self.d), items=[
            {"id_producto": "P1", "cantidad": 2, "precio_venta": 1000, "costo_venta": 600},
            {"id_producto": "P2", "cantidad": 1, "precio_venta": 450, "costo_venta": 300},
        ])
        credito = self.vender(
            fecha=str(self.d), tipo_compra="En Línea", items=[{"id_producto": "P1", "cantidad": 1}],
            por_cobrar=True, fecha_vencimiento=str(self.d + timedelta(days=30)),
        )
        self.pagar(self.cuenta_de(credito), fecha_pago=str(self.d + timedelta(days=3)))
        GastoInsumo.objects.create(id_gasto=1, producto=self.p1, fecha=self.d, monto=700)
        GastoInsumo.objects.create(id_gasto=2, producto=self.p2, fecha=self.d + timedelta(days=3), monto=300)

    def resumen(self, desde, hasta, extra=""):
        return self.client.get(f"/api/finanzas/resumen-mensual/?fecha_inicio={desde}&fecha_fin={hasta}{extra}").json()

    def test_flujo_de_los_cuatro_dias(self):
        r = self.resumen(self.d, self.d + timedelta(days=3))
        self.assertEqual(r["flujo_caja"], {
            "entradas": {"ventas_contado": 2450, "cobros": 1000, "total": 3450},
            "salidas": {"gastos_insumo": 1000, "total": 1000},
            "saldo": 2450,
        })
        # Las ventas del período incluyen la de crédito; la utilidad usa el costo de lo vendido
        self.assertEqual(r["total_ingresos"], 3450)
        self.assertEqual(r["total_costos"], 2100)  # 3×600 + 1×300
        self.assertEqual(r["utilidad_bruta"], 1350)
        self.assertEqual(r["total_unidades"], 4)

    def test_la_venta_a_credito_entra_a_caja_el_dia_del_pago(self):
        r = self.resumen(self.d, self.d)
        self.assertEqual(r["flujo_caja"]["entradas"], {"ventas_contado": 2450, "cobros": 0, "total": 2450})
        self.assertEqual(r["flujo_caja"]["saldo"], 1750)  # 2450 - 700

    def test_filtro_de_canal(self):
        r = self.resumen(self.d, self.d + timedelta(days=3), "&tipo_compra=En Línea")
        self.assertEqual(r["filtro_tipo_compra"], "En Línea")
        self.assertEqual(r["flujo_caja"]["entradas"]["total"], 1000)  # solo el cobro en línea
        self.assertEqual(r["flujo_caja"]["salidas"]["total"], 1000)  # los gastos no tienen canal

    def test_agrupado_por_dia(self):
        r = self.client.get(
            f"/api/finanzas/resumen-agrupado/?fecha_inicio={self.d}&fecha_fin={self.d + timedelta(days=3)}&agrupacion=diaria"
        ).json()
        dias = [p["flujo_caja"] for p in r["periodos"]]
        self.assertEqual([d["entradas"]["total"] for d in dias], [2450, 0, 0, 1000])
        self.assertEqual([d["salidas"]["total"] for d in dias], [700, 0, 0, 300])
        self.assertEqual(r["totales"]["flujo_caja"]["saldo"], 2450)

    def test_exportar_excel(self):
        r = self.client.get(f"/api/finanzas/exportar-excel/?fecha_inicio={self.d}&fecha_fin={self.d}")
        self.assertEqual(r.status_code, 200)
        self.assertIn("spreadsheetml", r["Content-Type"])


class AgrupacionSemanalTests(BaseAPITest):
    """Ventas en días conocidos de octubre de 2026 (jueves 1 = primer día del mes)."""

    def setUp(self):
        super().setUp()
        for dia in (1, 7, 8, 22, 31):
            self.vender(fecha=f"2026-10-{dia:02d}", items=[
                {"id_producto": "P1", "cantidad": 1, "precio_venta": 1000, "costo_venta": 600}])
        GastoInsumo.objects.create(id_gasto=1, producto=self.p1, fecha=date(2026, 10, 5), monto=300)

    def agrupado(self, agrupacion):
        r = self.client.get(
            f"/api/finanzas/resumen-agrupado/?fecha_inicio=2026-10-01&fecha_fin=2026-10-31&agrupacion={agrupacion}"
        )
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_semanas_del_mes_como_el_diseno(self):
        r = self.agrupado("semanas_mes")
        self.assertEqual([p["rango"] for p in r["periodos"]], ["01 - 07 Oct", "08 - 14 Oct", "15 - 21 Oct", "22 - 31 Oct"])
        self.assertEqual(r["periodos"][0]["periodo"], "Sem 1 Oct 2026")
        self.assertEqual([p["total_transacciones"] for p in r["periodos"]], [2, 1, 0, 2])
        self.assertEqual([p["flujo_caja"]["entradas"]["total"] for p in r["periodos"]], [2000, 1000, 0, 2000])
        self.assertEqual([p["flujo_caja"]["salidas"]["total"] for p in r["periodos"]], [300, 0, 0, 0])

    def test_semanal_de_lunes_a_domingo(self):
        r = self.agrupado("semanal")
        self.assertEqual(r["periodos"][0]["fecha_inicio"], "01/10/2026")
        self.assertEqual(r["periodos"][0]["fecha_fin"], "04/10/2026")
        self.assertEqual(r["periodos"][1]["fecha_inicio"], "05/10/2026")  # lunes
        self.assertEqual(r["periodos"][0]["periodo"], "Sem 40 2026")
        self.assertEqual(sum(p["total_transacciones"] for p in r["periodos"]), 5)

    def test_las_semanas_suman_lo_mismo_que_el_mes(self):
        mes = self.agrupado("mensual")["totales"]
        for agrupacion in ("semanal", "semanas_mes", "diaria", "trimestral", "anual"):
            with self.subTest(agrupacion):
                r = self.agrupado(agrupacion)
                self.assertEqual(sum(p["total_ingresos"] for p in r["periodos"]), mes["total_ingresos"])
                self.assertEqual(sum(p["flujo_caja"]["saldo"] for p in r["periodos"]), mes["flujo_caja"]["saldo"])

    def test_agrupacion_invalida(self):
        r = self.client.get("/api/finanzas/resumen-agrupado/?fecha_inicio=2026-10-01&agrupacion=quincenal")
        self.assertEqual(r.status_code, 400)


class ProductosMasVendidosTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.d = self.hoy - timedelta(days=5)
        precio = {"precio_venta": 500, "costo_venta": 300}
        self.vender(fecha=str(self.d), items=[{"id_producto": "P2", "cantidad": 5, **precio}])  # 5 × 500
        self.vender(fecha=str(self.d), tipo_compra="En Línea", items=[
            {"id_producto": "P1", "cantidad": 3, "precio_venta": 1000, "costo_venta": 600}])  # 3 × 1000
        self.vender(fecha=str(self.d - timedelta(days=60)), items=[
            {"id_producto": "P1", "cantidad": 4, "precio_venta": 1000, "costo_venta": 600}])

    def productos(self, extra=""):
        r = self.client.get(f"/api/finanzas/productos/?{extra}")
        self.assertEqual(r.status_code, 200, r.content)
        return {p["id_producto"]: p for p in r.json()["results"]}, [p["id_producto"] for p in r.json()["results"]]

    def test_totales_de_todo_el_historial(self):
        datos, _ = self.productos()
        self.assertEqual(datos["P1"]["total_vendido"], 7)
        self.assertEqual(datos["P1"]["total_ingresos"], 7000)
        self.assertEqual(datos["P2"]["total_vendido"], 5)

    def test_orden_por_mas_vendidos(self):
        _, orden = self.productos("ordering=-total_vendido")
        self.assertEqual(orden, ["P1", "P2"])
        _, orden = self.productos("ordering=-total_vendido&fecha_inicio=" + str(self.d))
        self.assertEqual(orden, ["P2", "P1"])  # en el período: P2 = 5, P1 = 3

    def test_filtro_por_canal_y_orden_por_ingresos(self):
        datos, orden = self.productos(f"ordering=-total_ingresos&tipo_compra=En Línea&fecha_inicio={self.d}")
        self.assertEqual(orden[0], "P1")
        self.assertEqual(datos["P1"]["total_vendido"], 3)
        self.assertEqual(datos["P2"]["total_vendido"], 0)

    def test_parametros_invalidos(self):
        self.assertEqual(self.client.get("/api/finanzas/productos/?ordering=-ventas").status_code, 400)
        self.assertEqual(self.client.get("/api/finanzas/productos/?fecha_inicio=ayer").status_code, 400)
        self.assertEqual(self.client.get("/api/finanzas/productos/?tipo_compra=telefono").status_code, 400)


class EsquemaDelEquipoDeDatosTests(TestCase):
    """Las tablas y columnas deben llamarse igual que en schema_postgresql.sql de la rama datos."""

    ESQUEMA = {
        "cliente": {"id_cliente", "nombre", "contacto"},
        "producto": {"id_producto", "categoria", "producto", "unidad_negocio"},
        "venta": {"id_factura", "id_cliente", "fecha", "tipo_compra", "por_cobrar"},
        "detalle_venta": {"id_detalle", "id_factura", "id_producto", "cantidad", "precio_venta", "costo_venta"},
        "cuenta_por_cobrar": {"id_cuenta", "id_factura", "id_cliente", "monto", "fecha_vencimiento", "estado", "fecha_pago"},
        "gastos_insumo": {"id_gasto", "id_producto", "fecha", "monto"},
    }

    def test_tablas_y_columnas(self):
        with connection.cursor() as cursor:
            for tabla, columnas in self.ESQUEMA.items():
                with self.subTest(tabla):
                    en_base = {c.name for c in connection.introspection.get_table_description(cursor, tabla)}
                    self.assertEqual(en_base, columnas)

    def test_verificar_esquema(self):
        salida = StringIO()
        call_command("verificar_esquema", stdout=salida)
        self.assertIn("coincide", salida.getvalue())


class ImportarCsvTests(TestCase):
    def escribir(self, carpeta, nombre, filas):
        with open(Path(carpeta) / f"{nombre}.csv", "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(filas)

    def preparar(self, carpeta, etapa4=True):
        self.escribir(carpeta, "cliente", [["id_cliente", "nombre", "contacto"], [1, "Ana", "+56 9 1"]])
        self.escribir(carpeta, "producto", [["id_producto", "categoria", "producto", "unidad_negocio"],
                                            ["P1", "Abarrotes", "Arroz", "Supermercado"]])
        self.escribir(carpeta, "venta", [["id_factura", "id_cliente", "fecha", "tipo_compra", "por_cobrar"],
                                         ["F1", 1, "2022-08-01", "Física", "False"],
                                         ["F2", 1, "2022-08-02", "En Línea", "True"],
                                         ["F3", 1, "2022-08-03", "Física", "True"]])
        self.escribir(carpeta, "detalle_venta", [["id_detalle", "id_factura", "id_producto", "cantidad", "precio_venta", "costo_venta"],
                                                 [1, "F1", "P1", 2, 100, 60], [2, "F2", "P1", 1, 100, 60], [3, "F3", "P1", 1, 100, 60]])
        if etapa4:
            self.escribir(carpeta, "cuenta_por_cobrar", [
                ["id_cuenta", "id_factura", "id_cliente", "monto", "fecha_vencimiento", "estado", "fecha_pago"],
                [1, "F2", 1, 100, "2022-08-20", "PAGADA", "2022-08-10"],
                [2, "F3", 1, 100, "2022-08-25", "VENCIDA", ""]])
            self.escribir(carpeta, "gastos_insumo", [["id_gasto", "id_producto", "fecha", "monto"], [1, "P1", "2022-08-01", 50]])
        else:
            self.escribir(carpeta, "cuenta_por_cobrar", [
                ["id_cuenta", "id_factura", "id_cliente", "monto", "fecha_vencimiento"],
                [1, "F2", 1, 100, "2022-08-02"], [2, "F3", 1, 100, "2022-09-30"]])
            self.escribir(carpeta, "gastos_insumo", [["id_gasto", "id_producto", "Fecha", "Monto"], [1, "P1", "2022-08-01", 50]])

    def test_formato_etapa_4(self):
        with tempfile.TemporaryDirectory() as carpeta:
            self.preparar(carpeta)
            call_command("importar_csv", carpeta=carpeta, fechas_originales=True, stdout=StringIO())
            call_command("importar_csv", carpeta=carpeta, fechas_originales=True, stdout=StringIO())  # sin duplicar
        self.assertEqual(Venta.objects.count(), 3)
        self.assertEqual(Venta.objects.get(pk="F2").tipo_compra, "En Línea")
        pagada = CuentaPorCobrar.objects.get(pk=1)
        self.assertEqual((pagada.estado, pagada.fecha_pago), ("PAGADA", date(2022, 8, 10)))
        self.assertEqual(CuentaPorCobrar.objects.get(pk=2).estado, "VENCIDA")
        self.assertEqual(GastoInsumo.objects.get().monto, 50)

    def test_formato_etapa_3_y_desfase_de_fechas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            self.preparar(carpeta, etapa4=False)
            call_command("importar_csv", carpeta=carpeta, stdout=StringIO())
        ultima = Venta.objects.order_by("-fecha").first().fecha
        self.assertLess((timezone.localdate() - ultima).days, 8)  # la última venta queda en la última semana
        self.assertEqual(GastoInsumo.objects.get().fecha.weekday(), date(2022, 8, 1).weekday())
        self.assertEqual(CuentaPorCobrar.objects.get(pk=1).estado, "VENCIDA")
        self.assertEqual(CuentaPorCobrar.objects.get(pk=2).estado, "PENDIENTE")
        self.assertIsNone(CuentaPorCobrar.objects.get(pk=1).fecha_pago)


class AlertasCobroTests(BaseAPITest):
    """Misma lógica que vw_alertas_cobro del equipo de datos, a la fecha de hoy."""

    def setUp(self):
        super().setUp()

        def cuenta(id_cuenta, estado, dias, monto, fecha_pago=None):
            venta = Venta.objects.create(id_factura=f"INV{id_cuenta}", cliente=self.cliente,
                                         fecha=self.hoy - timedelta(days=90), tipo_compra="Física", por_cobrar=True)
            CuentaPorCobrar.objects.create(id_cuenta=id_cuenta, venta=venta, cliente=self.cliente, monto=monto,
                                           fecha_vencimiento=self.hoy + timedelta(days=dias), estado=estado,
                                           fecha_pago=fecha_pago)

        cuenta(1, "VENCIDA", -20, 500)
        cuenta(2, "PENDIENTE", -3, 300)   # pendiente con fecha pasada: también es crítica
        cuenta(3, "PENDIENTE", 0, 100)    # vence hoy
        cuenta(4, "PENDIENTE", 7, 200)
        cuenta(5, "PENDIENTE", 12, 50)
        cuenta(6, "PENDIENTE", 40, 900)   # vigente: fuera de la ventana de 15 días
        cuenta(7, "PAGADA", -50, 999, fecha_pago=self.hoy - timedelta(days=60))

    def alertas(self, extra=""):
        r = self.client.get(f"/api/finanzas/alertas-cobro/?{extra}")
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_prioridades_y_orden(self):
        r = self.alertas()
        self.assertEqual([a["id_cuenta"] for a in r["results"]], [1, 2, 3, 4, 5])  # vencidas primero, por fecha
        self.assertEqual(
            [a["prioridad_alerta"] for a in r["results"]],
            ["1_CRITICA_VENCIDA", "1_CRITICA_VENCIDA", "2_ALTA_PROXIMA_7D", "2_ALTA_PROXIMA_7D", "3_MEDIA_PROXIMA_15D"],
        )
        self.assertEqual(r["resumen"]["por_prioridad"]["1_CRITICA_VENCIDA"], {"nombre": "Vencida", "cantidad": 2, "monto": 800})
        self.assertEqual(r["resumen"]["total_alertas"], 5)
        self.assertEqual(r["resumen"]["monto_total"], 1150)

    def test_campos_como_la_vista_de_datos(self):
        vencida, _, hoy, *_ = self.alertas()["results"]
        self.assertEqual((vencida["tipo_alerta"], vencida["dias_atraso"], vencida["dias_para_vencer"]), ("VENCIDA", 20, -20))
        self.assertEqual(
            vencida["mensaje_sugerido"],
            "Recordatorio urgente: cliente Almacén San Pedro mantiene factura INV1 vencida hace 20 días por $500.",
        )
        self.assertEqual((hoy["tipo_alerta"], hoy["dias_atraso"], hoy["ventana_alerta"]), ("POR_VENCER", 0, "Vence en <= 7 días"))
        self.assertEqual(
            hoy["mensaje_sugerido"],
            f"Aviso preventivo: factura INV3 de Almacén San Pedro vence el {self.hoy} (en 0 días) por $100.",
        )
        self.assertTrue(hoy["requiere_notificacion"])

    def test_filtros(self):
        self.assertEqual([a["id_cuenta"] for a in self.alertas("prioridad=alta")["results"]], [3, 4])
        self.assertEqual([a["id_cuenta"] for a in self.alertas("dias_aviso=5")["results"]], [1, 2, 3])
        todas = self.alertas("todas=true")
        self.assertEqual(todas["count"], 6)  # incluye la vigente; la pagada nunca
        self.assertFalse(todas["results"][-1]["requiere_notificacion"])
        self.assertEqual(self.alertas("cliente=999")["count"], 0)
        # A otra fecha de corte (así se compara con Power BI, que usa una fecha fija)
        antes = self.alertas(f"fecha_corte={self.hoy - timedelta(days=10)}")
        self.assertEqual(antes["resumen"]["por_prioridad"]["1_CRITICA_VENCIDA"]["cantidad"], 1)  # a esa fecha solo la cuenta 1 estaba vencida
        for malo in ("prioridad=urgente", "dias_aviso=x", "fecha_corte=ayer", "cliente=abc"):
            with self.subTest(malo):
                self.assertEqual(self.client.get(f"/api/finanzas/alertas-cobro/?{malo}").status_code, 400)

    def test_pagar_quita_la_alerta(self):
        self.pagar(2)
        self.assertNotIn(2, [a["id_cuenta"] for a in self.alertas()["results"]])


class MetricasTests(BaseAPITest):
    """La API lee las vistas SQL del equipo de datos (finanzas/sql/)."""

    def setUp(self):
        super().setUp()
        p3 = Producto.objects.create(id_producto="P3", producto="Jabón", categoria="Aseo del hogar", unidad_negocio="Supermercado")

        def venta(id_factura, fecha, por_cobrar, lineas):
            v = Venta.objects.create(id_factura=id_factura, cliente=self.cliente, fecha=fecha,
                                     tipo_compra="Física", por_cobrar=por_cobrar)
            for producto, cantidad, precio, costo in lineas:
                DetalleVenta.objects.create(id_detalle=DetalleVenta.objects.count() + 1, venta=v, producto=producto,
                                            cantidad=cantidad, precio_venta=precio, costo_venta=costo)
            return v

        venta("A", date(2019, 5, 10), False, [(self.p1, 2, 1000, 600), (p3, 1, 500, 400)])   # 2.500 / margen 900
        fiada = venta("B", date(2019, 5, 20), True, [(self.p2, 4, 500, 300)])                  # 2.000 / margen 800
        venta("C", date(2022, 3, 1), False, [(self.p1, 1, 1000, 600)])                         # período "parcial"
        CuentaPorCobrar.objects.create(id_cuenta=1, venta=fiada, cliente=self.cliente, monto=2000,
                                       fecha_vencimiento=date(2019, 6, 20), estado="PAGADA", fecha_pago=date(2019, 6, 25))
        GastoInsumo.objects.create(id_gasto=1, producto=self.p1, fecha=date(2019, 5, 15), monto=700)

    def metrica(self, nombre, extra="", estado=200):
        r = self.client.get(f"/api/finanzas/metricas/{nombre}/?{extra}")
        self.assertEqual(r.status_code, estado, r.content)
        return r.json()

    def test_sin_vistas_responde_503(self):
        self.assertIn("crear_vistas_metricas", self.metrica("morosidad", estado=503)["error"])
        self.assertFalse(self.client.get("/api/finanzas/metricas/").json()["metricas"]["morosidad"]["disponible"])

    def test_metricas_leen_las_vistas(self):
        call_command("crear_vistas_metricas", stdout=StringIO())
        call_command("crear_vistas_metricas", stdout=StringIO())  # si ya existen, no las toca

        flujo = self.metrica("flujo-caja-mensual", "periodo=2019-05")["results"][0]
        self.assertEqual(
            (flujo["ventas_facturadas"], flujo["ingresos_contado"], flujo["ventas_fiadas"], flujo["gastos_insumo"], flujo["flujo_caja_neto"]),
            (4500, 2500, 2000, 700, 1800),
        )
        # El flujo de caja de la API da lo mismo que la vista del equipo de datos
        resumen = self.client.get("/api/finanzas/resumen-mensual/?fecha_inicio=2019-05-01&fecha_fin=2019-05-31").json()
        self.assertEqual(resumen["flujo_caja"]["saldo"], flujo["flujo_caja_neto"])
        junio = self.metrica("flujo-caja-mensual", "periodo=2019-06")["results"][0]
        self.assertEqual(junio["cobros_fiado_recibidos"], 2000)

        categorias = self.metrica("ventas-categoria-mes", "anio=2019&ordering=-ventas")
        self.assertEqual([(c["categoria"], c["ventas"], c["margen"]) for c in categorias["results"]],
                         [("Abarrotes", 4000, 1600), ("Aseo del hogar", 500, 100)])

        margen = self.metrica("margen-productos", "id_producto=P1&cobertura=completa")["results"]
        self.assertEqual((margen[0]["ventas"], margen[0]["margen"], margen[0]["margen_pct"]), (2000, 800, 40))
        self.assertEqual(self.metrica("margen-productos", "search=jab")["count"], 1)

        ranking = self.metrica("ranking-productos")
        self.assertEqual([p["id_producto"] for p in ranking["results"]], ["P1", "P2", "P3"])  # sin la venta de 2022
        self.assertIs(ranking["results"][0]["alerta_escala_etapa2"], False)
        self.assertEqual(self.metrica("ranking-productos", "clasificacion_desempeno=Baja venta&sin_alerta_escala=true")["count"], 1)

        cliente = self.metrica("cuentas-por-cobrar-cliente", "id_cliente=1")["results"][0]
        self.assertEqual((cliente["monto_total_fiado"], cliente["monto_pagado"], cliente["promedio_dias_atraso_historico"]), (2000, 2000, 5))
        self.assertEqual(self.metrica("cuentas-por-cobrar-cliente", "con_deuda=true")["count"], 0)

        self.assertEqual(len(self.metrica("morosidad")["results"]), 3)
        anual = {a["anio"]: a for a in self.metrica("sustentabilidad")["results"]}
        self.assertEqual((anual[2019]["margen_bruto"], anual[2019]["gastos_insumo"], anual[2019]["utilidad_neta_operativa"]), (1700, 700, 1000))
        self.assertEqual(anual[2022]["cobertura"], "parcial")

        catalogo = self.client.get("/api/finanzas/metricas/").json()["metricas"]
        self.assertTrue(all(m["disponible"] for m in catalogo.values()))

    def test_parametros_invalidos(self):
        call_command("crear_vistas_metricas", stdout=StringIO())
        self.metrica("no-existe", estado=404)
        self.metrica("ranking-productos", "ordering=ventas;drop", estado=400)
        self.metrica("ventas-categoria-mes", "anio=dosmil", estado=400)
        # Los valores van como parámetros: una comilla no rompe la consulta
        self.assertEqual(self.metrica("ventas-categoria-mes", "categoria=x' OR '1'='1")["count"], 0)


class OperacionesTests(BaseAPITest):
    """Ventas y gastos en una sola lista, para la pantalla 'Compras y ventas'."""

    def setUp(self):
        super().setUp()
        Cliente.objects.create(id_cliente=2, nombre="Kiosco Don Luis", contacto="+56 9 2")
        self.vender(fecha="2026-10-05", items=[{"id_producto": "P1", "cantidad": 2, "precio_venta": 1000, "costo_venta": 600}])
        self.fiada = self.vender(
            fecha="2026-10-10", id_cliente=2, tipo_compra="En Línea", por_cobrar=True, fecha_vencimiento="2026-10-30",
            items=[{"id_producto": "P2", "cantidad": 3, "precio_venta": 500, "costo_venta": 300},
                   {"id_producto": "P1", "cantidad": 1, "precio_venta": 1000, "costo_venta": 600}],
        ).json()
        self.vender(fecha="2026-09-20", items=[{"id_producto": "P2", "cantidad": 1, "precio_venta": 500, "costo_venta": 300}])
        GastoInsumo.objects.create(id_gasto=1, producto=self.p1, fecha=date(2026, 10, 10), monto=700)
        GastoInsumo.objects.create(id_gasto=2, producto=self.p2, fecha=date(2026, 10, 20), monto=300)

    def operaciones(self, extra=""):
        r = self.client.get(f"/api/finanzas/operaciones/?{extra}")
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_lista_unificada_del_mes(self):
        r = self.operaciones("mes=2026-10")
        self.assertEqual([(o["tipo"], o["fecha"], o["monto"]) for o in r["results"]], [
            ("GASTO", "2026-10-20", 300),
            ("VENTA", "2026-10-10", 2500),  # a igual fecha, primero la venta
            ("GASTO", "2026-10-10", 700),
            ("VENTA", "2026-10-05", 2000),
        ])
        self.assertEqual(r["resumen"], {
            "ventas": {"cantidad": 2, "monto": 4500},
            "gastos": {"cantidad": 2, "monto": 1000},
            "ventas_pendientes": {"cantidad": 1, "monto": 2500},
        })
        venta = r["results"][1]
        self.assertEqual(venta, {
            "tipo": "VENTA", "id": self.fiada["id_factura"], "fecha": "2026-10-10", "detalle": "Kiosco Don Luis",
            "monto": 2500, "items_count": 2, "tipo_compra": "En Línea", "por_cobrar": True,
            "estado_pago": "PENDIENTE", "fecha_vencimiento": "2026-10-30", "id_cliente": 2, "id_producto": None,
        })
        gasto = r["results"][0]
        self.assertEqual((gasto["id"], gasto["detalle"], gasto["id_producto"], gasto["estado_pago"], gasto["tipo_compra"]),
                         ("2", "Arroz 1kg", "P2", "PAGADO", None))

    def test_filtros(self):
        self.assertEqual(self.operaciones()["count"], 5)
        self.assertEqual(self.operaciones("tipo=ventas")["count"], 3)
        self.assertEqual(self.operaciones("tipo=gasto&mes=2026-10")["resumen"]["ventas"]["cantidad"], 0)
        pendientes = self.operaciones("estado=pendiente")
        self.assertEqual([o["id"] for o in pendientes["results"]], [self.fiada["id_factura"]])
        self.pagar(self.fiada["cuenta_por_cobrar"]["id_cuenta"], fecha_pago="2026-10-15")
        self.assertEqual(self.operaciones("estado=pendiente")["count"], 0)
        self.assertEqual(self.operaciones("tipo_compra=En Línea")["count"], 1)  # los gastos no tienen canal
        self.assertEqual(self.operaciones("search=don luis")["count"], 1)
        self.assertEqual(self.operaciones("search=aceite")["count"], 3)  # 2 ventas con aceite + 1 gasto
        self.assertEqual(self.operaciones("fecha_inicio=2026-10-06&fecha_fin=2026-10-10")["count"], 2)
        self.assertEqual([o["monto"] for o in self.operaciones("ordering=-monto&page_size=2")["results"]], [2500, 2000])
        self.assertEqual(self.operaciones("mes=2026-12")["count"], 0)
        for malo in ("tipo=otro", "mes=octubre", "estado=x", "ordering=cliente", "tipo_compra=fax"):
            with self.subTest(malo):
                self.assertEqual(self.client.get(f"/api/finanzas/operaciones/?{malo}").status_code, 400)

    def test_resumen_por_canal_y_ordenes_nuevos(self):
        r = self.client.get("/api/finanzas/resumen-mensual/?fecha_inicio=2026-10-01&fecha_fin=2026-10-31").json()
        self.assertEqual(r["por_tipo_compra"], {
            "Física": {"nombre": "Física", "facturas": 1, "transacciones": 1, "ingresos": 2000},
            "En Línea": {"nombre": "En Línea", "facturas": 1, "transacciones": 2, "ingresos": 2500},
        })
        self.assertEqual(r["total_facturas"], 2)
        mayor = self.client.get("/api/finanzas/facturas/?ordering=-total_venta&page_size=1").json()["results"][0]
        self.assertEqual(mayor["total_venta"], 2500)
        deudores = self.client.get("/api/finanzas/clientes/?ordering=-total_deuda").json()["results"]
        self.assertEqual([(c["id_cliente"], c["total_deuda"]) for c in deudores], [(2, 2500), (1, 0)])
        self.assertEqual(self.client.get("/api/finanzas/clientes/?ordering=contacto").status_code, 400)
        self.assertEqual(self.client.get("/api/finanzas/facturas/?ordering=cliente").status_code, 400)

    def test_listas_livianas_para_formularios(self):
        clientes = self.client.get("/api/finanzas/opciones/clientes/?search=kiosco").json()["results"]
        self.assertEqual(clientes, [{"id_cliente": 2, "nombre": "Kiosco Don Luis", "contacto": "+56 9 2"}])
        Producto.objects.create(id_producto="P9", producto="Azúcar", categoria="Abarrotes", unidad_negocio="Supermercado")
        productos = self.client.get("/api/finanzas/opciones/productos/").json()["results"]
        self.assertEqual(productos, [
            {"id_producto": "P1", "producto": "Aceite 1L", "categoria": "Abarrotes",
             "ultimo_precio_venta": 1000, "ultimo_costo_venta": 600},
            {"id_producto": "P2", "producto": "Arroz 1kg", "categoria": "Abarrotes",
             "ultimo_precio_venta": 500, "ultimo_costo_venta": 300},
            {"id_producto": "P9", "producto": "Azúcar", "categoria": "Abarrotes",
             "ultimo_precio_venta": None, "ultimo_costo_venta": None},  # nunca se ha vendido
        ])
        self.assertEqual(len(self.client.get("/api/finanzas/opciones/productos/?limit=1").json()["results"]), 1)
        self.assertEqual(self.client.get("/api/finanzas/opciones/productos/?limit=500").status_code, 400)
