"""Pruebas del login con JWT. Ejecutar con: python manage.py test usuarios"""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

RUTAS_PROTEGIDAS = [
    "/api/finanzas/opciones-filtros/",
    "/api/finanzas/resumen-mensual/",
    "/api/finanzas/resumen-agrupado/?fecha_inicio=01/01/2026",
    "/api/finanzas/exportar-excel/",
    "/api/finanzas/clientes/",
    "/api/finanzas/productos/",
    "/api/finanzas/facturas/",
    "/api/finanzas/ventas/",
    "/api/finanzas/cuentas-por-cobrar/",
    "/api/finanzas/gastos/",
    "/api/auth/perfil/",
]


class AutenticacionTests(TestCase):
    def setUp(self):
        cache.clear()  # reinicia el contador de intentos de login entre pruebas
        self.client = APIClient()
        self.usuario = get_user_model().objects.create_user(
            username="cajera", password="ClaveSegura.2026", first_name="Ana", last_name="Pérez"
        )

    def login(self, username="cajera", password="ClaveSegura.2026"):
        return self.client.post("/api/auth/login/", {"username": username, "password": password}, format="json")

    def test_sin_token_la_api_responde_401(self):
        for ruta in RUTAS_PROTEGIDAS:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 401)

    def test_catalogo_es_publico(self):
        respuesta = self.client.get("/api/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("autenticacion", respuesta.json())

    def test_login_correcto_entrega_tokens_y_usuario(self):
        respuesta = self.login()
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertIn("access", datos)
        self.assertIn("refresh", datos)
        self.assertEqual(datos["usuario"]["username"], "cajera")
        self.assertEqual(datos["usuario"]["nombre"], "Ana Pérez")
        self.assertFalse(datos["usuario"]["es_admin"])

    def test_login_con_clave_incorrecta(self):
        respuesta = self.login(password="otra")
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()["detail"], "Usuario o contraseña incorrectos.")

    def test_usuario_inactivo_no_entra(self):
        self.usuario.is_active = False
        self.usuario.save()
        self.assertEqual(self.login().status_code, 401)

    def test_con_token_se_puede_consultar(self):
        access = self.login().json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        for ruta in RUTAS_PROTEGIDAS:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/perfil/").json()["username"], "cajera")

    def test_token_invalido_responde_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token-inventado")
        self.assertEqual(self.client.get("/api/finanzas/resumen-mensual/").status_code, 401)

    def test_refresh_entrega_tokens_nuevos_y_el_anterior_deja_de_servir(self):
        refresh = self.login().json()["refresh"]
        respuesta = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("access", respuesta.json())
        self.assertNotEqual(respuesta.json()["refresh"], refresh)
        repetido = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(repetido.status_code, 401)

    def test_logout_invalida_el_refresh(self):
        refresh = self.login().json()["refresh"]
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code, 200)
        despues = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(despues.status_code, 401)

    def test_demasiados_intentos_de_login_se_bloquean(self):
        for _ in range(10):
            self.login(password="mala")
        self.assertEqual(self.login().status_code, 429)
