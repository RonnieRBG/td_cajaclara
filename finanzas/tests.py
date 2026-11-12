"""
Pruebas de registro de ventas, pagos y gastos, y del flujo de caja.
Ejecutar con: python manage.py test finanzas
"""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Cliente, CuentaPorCobrar, Factura, GastoInsumo, Producto, TipoCompra


class BaseAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user("cajera", password="x"))
        TipoCompra.objects.create(tipo_compra="FISICA")
        TipoCompra.objects.create(tipo_compra="ONLINE")
        self.p1 = Producto.objects.create(no_parte="P1", producto="Aceite 1L", precio_venta=1000, costo_venta=600)
        self.p2 = Producto.objects.create(no_parte="P2", producto="Arroz 1kg", precio_venta=500, costo_venta=300)
        self.cliente = Cliente.objects.create(cliente_id="1", nombre="Almacén San Pedro")
        self.hoy = timezone.localdate()

    # Atajos
    def vender(self, **datos):
        datos.setdefault("items", [{"producto": "P1", "cantidad": 2}])
        return self.client.post("/api/finanzas/facturas/", datos, format="json")

    def vender_a_credito(self, dias=10, **datos):
        datos.update(por_cobrar=True, cliente="1", fecha_vencimiento=str(self.hoy + timedelta(days=dias)))
        return self.vender(**datos)

    def cuenta_de(self, respuesta):
        return respuesta.json()["cuenta_por_cobrar"]["id"]

    def pagar(self, cuenta_id, **datos):
        return self.client.post(f"/api/finanzas/cuentas-por-cobrar/{cuenta_id}/pagar/", datos, format="json")

    def momento(self, dia, hora=12):
        return timezone.make_aware(datetime.combine(dia, time(hora))).isoformat()


class RegistrarVentaTests(BaseAPITest):
    def test_venta_al_contado(self):
        r = self.vender(items=[
            {"producto": "P1", "cantidad": 2},
            {"producto": "P2", "cantidad": 1, "precio_unitario": "450"},
        ])
        self.assertEqual(r.status_code, 201, r.content)
        datos = r.json()
        self.assertTrue(datos["factura"].startswith("CC"))
        self.assertEqual(Decimal(datos["total_venta"]), Decimal("2450"))  # 2×1000 + 1×450
        self.assertEqual(datos["estado_pago"], "PAGADO")
        self.assertIsNone(datos["cuenta_por_cobrar"])
        self.assertEqual(len(datos["detalles"]), 2)
        # El costo se toma del catálogo; el precio, del catálogo o del enviado
        linea_p2 = next(d for d in datos["detalles"] if d["no_parte"] == "P2")
        self.assertEqual(Decimal(linea_p2["precio_unitario"]), Decimal("450"))
        self.assertEqual(Decimal(linea_p2["costo_unitario"]), Decimal("300"))
        # Aparece en el listado de líneas de venta y en el detalle
        self.assertEqual(self.client.get(f"/api/finanzas/ventas/?factura={datos['factura']}").json()["count"], 2)
        self.assertEqual(self.client.get(f"/api/finanzas/facturas/{datos['factura']}/").status_code, 200)

    def test_venta_a_credito_crea_su_cuenta(self):
        r = self.vender_a_credito()
        self.assertEqual(r.status_code, 201, r.content)
        datos = r.json()
        self.assertEqual(datos["estado_pago"], "PENDIENTE")
        self.assertEqual(Decimal(datos["cuenta_por_cobrar"]["monto"]), Decimal("2000"))
        self.assertEqual(datos["cuenta_por_cobrar"]["estado_actual"], "PENDIENTE")
        cliente = self.client.get("/api/finanzas/clientes/?search=San Pedro").json()["results"][0]
        self.assertEqual(Decimal(cliente["total_deuda"]), Decimal("2000"))
        self.assertEqual(cliente["total_facturas"], 1)

    def test_validaciones_de_venta(self):
        casos = {
            "sin productos": {"items": []},
            "producto inexistente": {"items": [{"producto": "NO-EXISTE", "cantidad": 1}]},
            "cantidad cero": {"items": [{"producto": "P1", "cantidad": 0}]},
            "precio negativo": {"items": [{"producto": "P1", "cantidad": 1, "precio_unitario": "-5"}]},
            "crédito sin cliente": {"por_cobrar": True, "fecha_vencimiento": str(self.hoy)},
            "crédito sin vencimiento": {"por_cobrar": True, "cliente": "1"},
            "contado con vencimiento": {"fecha_vencimiento": str(self.hoy)},
            "canal inválido": {"tipo_compra": "TELEFONO"},
        }
        for nombre, datos in casos.items():
            with self.subTest(nombre):
                self.assertEqual(self.vender(**datos).status_code, 400)
        r = self.vender(por_cobrar=True, cliente="1", fecha_vencimiento=str(self.hoy - timedelta(days=1)))
        self.assertEqual(r.status_code, 400)
        self.assertIn("anterior", r.json()["error"])
        self.assertEqual(Factura.objects.count(), 0)  # nada quedó a medio guardar

    def test_registrar_requiere_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.vender().status_code, 401)


class PagosTests(BaseAPITest):
    def test_pagar_y_revertir(self):
        r = self.vender_a_credito()
        cuenta_id, factura = self.cuenta_de(r), r.json()["factura"]

        pago = self.pagar(cuenta_id)
        self.assertEqual(pago.status_code, 200, pago.content)
        self.assertEqual(pago.json()["estado"], "PAGADA")
        self.assertEqual(pago.json()["fecha_pago"], str(self.hoy))
        self.assertEqual(self.client.get(f"/api/finanzas/facturas/{factura}/").json()["estado_pago"], "PAGADO")
        cliente = self.client.get("/api/finanzas/clientes/?search=San Pedro").json()["results"][0]
        self.assertEqual(Decimal(cliente["total_deuda"]), 0)

        self.assertEqual(self.pagar(cuenta_id).status_code, 400)  # no se paga dos veces

        revertir = self.client.post(f"/api/finanzas/cuentas-por-cobrar/{cuenta_id}/revertir-pago/")
        self.assertEqual(revertir.status_code, 200)
        self.assertEqual(revertir.json()["estado"], "PENDIENTE")
        self.assertIsNone(revertir.json()["fecha_pago"])
        self.assertEqual(
            self.client.post(f"/api/finanzas/cuentas-por-cobrar/{cuenta_id}/revertir-pago/").status_code, 400
        )

    def test_fechas_de_pago_invalidas(self):
        cuenta_id = self.cuenta_de(self.vender_a_credito())
        self.assertEqual(self.pagar(cuenta_id, fecha_pago=str(self.hoy + timedelta(days=1))).status_code, 400)
        self.assertEqual(self.pagar(cuenta_id, fecha_pago=str(self.hoy - timedelta(days=30))).status_code, 400)
        self.assertEqual(self.client.post("/api/finanzas/cuentas-por-cobrar/9999/pagar/").status_code, 404)


class AnularTests(BaseAPITest):
    def test_anular_venta_al_contado(self):
        factura = self.vender().json()["factura"]
        r = self.client.post(f"/api/finanzas/facturas/{factura}/anular/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["estado_pago"], "ANULADO")
        resumen = self.client.get("/api/finanzas/resumen-mensual/").json()
        self.assertEqual(resumen["total_ingresos"], 0)
        self.assertEqual(resumen["flujo_caja"]["entradas"]["total"], 0)
        self.assertEqual(self.client.post(f"/api/finanzas/facturas/{factura}/anular/").status_code, 400)

    def test_anular_venta_a_credito(self):
        factura = self.vender_a_credito().json()["factura"]
        self.assertEqual(self.client.post(f"/api/finanzas/facturas/{factura}/anular/").status_code, 200)
        self.assertFalse(CuentaPorCobrar.objects.filter(factura_id=factura).exists())  # la deuda desaparece

    def test_no_se_anula_una_venta_pagada(self):
        r = self.vender_a_credito()
        self.pagar(self.cuenta_de(r))
        anular = self.client.post(f"/api/finanzas/facturas/{r.json()['factura']}/anular/")
        self.assertEqual(anular.status_code, 400)
        self.assertIn("revierte el pago", anular.json()["error"])


class GastosYClientesTests(BaseAPITest):
    def test_registrar_gastos(self):
        compra = self.client.post(
            "/api/finanzas/gastos/", {"tipo": "COMPRA", "producto": "P1", "monto": 24000, "proveedor": "Distribuidora"},
            format="json",
        )
        self.assertEqual(compra.status_code, 201, compra.content)
        self.assertEqual(compra.json()["categoria"], "INSUMOS")
        self.assertEqual(compra.json()["fecha"], str(self.hoy))

        otro = self.client.post("/api/finanzas/gastos/", {"tipo": "OTRO", "monto": 350000}, format="json")
        self.assertEqual(otro.status_code, 201, otro.content)
        self.assertEqual(otro.json()["categoria"], "OTROS")
        self.assertIsNone(otro.json()["producto"])

        for datos in (
            {"tipo": "COMPRA", "monto": 100},  # compra sin producto
            {"tipo": "OTRO", "producto": "P1", "monto": 100},  # otro gasto con producto
            {"tipo": "OTRO", "monto": 0},  # monto cero
            {"tipo": "OTRO", "categoria": "VIAJES", "monto": 100},  # categoría inexistente
        ):
            with self.subTest(datos):
                self.assertEqual(self.client.post("/api/finanzas/gastos/", datos, format="json").status_code, 400)
        self.assertEqual(GastoInsumo.objects.count(), 2)

    def test_registrar_cliente(self):
        r = self.client.post("/api/finanzas/clientes/", {"nombre": "Kiosco Don Luis", "contacto": "+56 9 1111"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["cliente_id"], "2")  # sigue la numeración
        self.assertEqual(self.client.post("/api/finanzas/clientes/", {}, format="json").status_code, 400)


class FlujoDeCajaTests(BaseAPITest):
    """Caso controlado, con montos que se pueden revisar a mano:

    Día D:   venta al contado (física)  2×1000 + 1×450 = 2.450
             venta a crédito (online)   1×1000         = 1.000  (no entra a caja ese día)
             compra de mercadería                         700
    Día D+3: el cliente paga la venta a crédito         1.000  (entra a caja)
             arriendo                                     300
    """

    def setUp(self):
        super().setUp()
        self.d = self.hoy - timedelta(days=10)
        self.vender(fecha=self.momento(self.d), items=[
            {"producto": "P1", "cantidad": 2}, {"producto": "P2", "cantidad": 1, "precio_unitario": "450"},
        ])
        credito = self.vender(
            fecha=self.momento(self.d), tipo_compra="ONLINE", items=[{"producto": "P1", "cantidad": 1}],
            por_cobrar=True, cliente="1", fecha_vencimiento=str(self.d + timedelta(days=30)),
        )
        self.pagar(self.cuenta_de(credito), fecha_pago=str(self.d + timedelta(days=3)))
        GastoInsumo.objects.create(tipo="COMPRA", producto=self.p1, fecha=self.d, monto=700)
        GastoInsumo.objects.create(tipo="OTRO", categoria="ARRIENDO", fecha=self.d + timedelta(days=3), monto=300)

    def resumen(self, desde, hasta, extra=""):
        return self.client.get(f"/api/finanzas/resumen-mensual/?fecha_inicio={desde}&fecha_fin={hasta}{extra}").json()

    def test_flujo_de_los_cuatro_dias(self):
        r = self.resumen(self.d, self.d + timedelta(days=3))
        self.assertEqual(r["flujo_caja"], {
            "entradas": {"ventas_contado": 2450.0, "cobros": 1000.0, "total": 3450.0},
            "salidas": {"compras": 700.0, "otros_gastos": 300.0, "total": 1000.0},
            "saldo": 2450.0,
        })
        # Las ventas del período incluyen la de crédito; la utilidad usa el costo de lo vendido
        self.assertEqual(r["total_ingresos"], 3450.0)
        self.assertEqual(r["total_costos"], 2100.0)  # 3×600 + 1×300
        self.assertEqual(r["utilidad_bruta"], 1350.0)
        self.assertEqual(r["total_unidades"], 4)

    def test_la_venta_a_credito_entra_a_caja_el_dia_del_pago(self):
        r = self.resumen(self.d, self.d)
        self.assertEqual(r["flujo_caja"]["entradas"], {"ventas_contado": 2450.0, "cobros": 0.0, "total": 2450.0})
        self.assertEqual(r["flujo_caja"]["saldo"], 1750.0)  # 2450 - 700

    def test_filtro_de_canal(self):
        r = self.resumen(self.d, self.d + timedelta(days=3), "&tipo_compra=ONLINE")
        self.assertEqual(r["flujo_caja"]["entradas"]["total"], 1000.0)  # solo el cobro online
        self.assertEqual(r["flujo_caja"]["salidas"]["total"], 1000.0)  # los gastos no tienen canal

    def test_agrupado_por_dia(self):
        r = self.client.get(
            f"/api/finanzas/resumen-agrupado/?fecha_inicio={self.d}&fecha_fin={self.d + timedelta(days=3)}&agrupacion=diaria"
        ).json()
        dias = [p["flujo_caja"] for p in r["periodos"]]
        self.assertEqual([d["entradas"]["total"] for d in dias], [2450.0, 0.0, 0.0, 1000.0])
        self.assertEqual([d["salidas"]["total"] for d in dias], [700.0, 0.0, 0.0, 300.0])
        self.assertEqual(r["totales"]["flujo_caja"]["saldo"], 2450.0)


class AgrupacionSemanalTests(BaseAPITest):
    """Ventas en días conocidos de octubre de 2026 (jueves 1 = primer día del mes)."""

    def setUp(self):
        super().setUp()
        from datetime import date
        self.dias = [date(2026, 10, d) for d in (1, 7, 8, 22, 31)]
        for dia in self.dias:
            self.vender(fecha=self.momento(dia), items=[{"producto": "P1", "cantidad": 1}])  # 1.000 c/u
        GastoInsumo.objects.create(tipo="OTRO", categoria="ARRIENDO", fecha=date(2026, 10, 5), monto=300)

    def agrupado(self, agrupacion):
        r = self.client.get(
            f"/api/finanzas/resumen-agrupado/?fecha_inicio=2026-10-01&fecha_fin=2026-10-31&agrupacion={agrupacion}"
        )
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_semanas_del_mes_como_el_diseno(self):
        r = self.agrupado("semanas_mes")
        self.assertEqual([p["rango"] for p in r["periodos"]], ["01 - 07 Oct", "08 - 14 Oct", "15 - 21 Oct", "22 - 31 Oct"])
        self.assertEqual([p["periodo"] for p in r["periodos"]][0], "Sem 1 Oct 2026")
        self.assertEqual([p["total_transacciones"] for p in r["periodos"]], [2, 1, 0, 2])
        self.assertEqual([p["flujo_caja"]["entradas"]["total"] for p in r["periodos"]], [2000.0, 1000.0, 0.0, 2000.0])
        self.assertEqual([p["flujo_caja"]["salidas"]["total"] for p in r["periodos"]], [300.0, 0.0, 0.0, 0.0])

    def test_semanal_de_lunes_a_domingo(self):
        r = self.agrupado("semanal")
        # 1 oct 2026 es jueves: la primera semana va del 1 al 4 (domingo)
        self.assertEqual(r["periodos"][0]["fecha_inicio"], "01/10/2026")
        self.assertEqual(r["periodos"][0]["fecha_fin"], "04/10/2026")
        self.assertEqual(r["periodos"][1]["fecha_inicio"], "05/10/2026")  # lunes
        self.assertEqual(r["periodos"][0]["periodo"], "Sem 40 2026")
        self.assertEqual(sum(p["total_transacciones"] for p in r["periodos"]), 5)

    def test_las_semanas_suman_lo_mismo_que_el_mes(self):
        mes = self.agrupado("mensual")["totales"]
        for agrupacion in ("semanal", "semanas_mes", "diaria"):
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
        self.vender(fecha=self.momento(self.d), items=[{"producto": "P2", "cantidad": 5}])  # 5 × 500
        self.vender(fecha=self.momento(self.d), tipo_compra="ONLINE", items=[{"producto": "P1", "cantidad": 3}])  # 3 × 1000
        antigua = self.vender(fecha=self.momento(self.d - timedelta(days=60)), items=[{"producto": "P1", "cantidad": 4}])
        anulada = self.vender(fecha=self.momento(self.d), items=[{"producto": "P1", "cantidad": 100}])
        self.client.post(f"/api/finanzas/facturas/{anulada.json()['factura']}/anular/")
        self.antigua = antigua

    def productos(self, extra=""):
        r = self.client.get(f"/api/finanzas/productos/?{extra}")
        self.assertEqual(r.status_code, 200, r.content)
        return {p["no_parte"]: p for p in r.json()["results"]}, [p["no_parte"] for p in r.json()["results"]]

    def test_totales_de_todo_el_historial(self):
        datos, _ = self.productos()
        self.assertEqual(datos["P1"]["total_vendido"], 7)  # 3 + 4; la anulada no cuenta
        self.assertEqual(Decimal(datos["P1"]["total_ingresos"]), Decimal("7000"))
        self.assertEqual(datos["P2"]["total_vendido"], 5)

    def test_orden_por_mas_vendidos(self):
        _, orden = self.productos("ordering=-total_vendido")
        self.assertEqual(orden, ["P1", "P2"])
        _, orden = self.productos("ordering=-total_vendido&fecha_inicio=" + str(self.d))
        self.assertEqual(orden, ["P2", "P1"])  # en el período: P2 = 5, P1 = 3

    def test_filtro_por_canal_y_orden_por_ingresos(self):
        datos, orden = self.productos(f"ordering=-total_ingresos&tipo_compra=ONLINE&fecha_inicio={self.d}")
        self.assertEqual(orden[0], "P1")
        self.assertEqual(datos["P1"]["total_vendido"], 3)
        self.assertEqual(datos["P2"]["total_vendido"], 0)

    def test_parametros_invalidos(self):
        self.assertEqual(self.client.get("/api/finanzas/productos/?ordering=-ventas").status_code, 400)
        self.assertEqual(self.client.get("/api/finanzas/productos/?fecha_inicio=ayer").status_code, 400)
