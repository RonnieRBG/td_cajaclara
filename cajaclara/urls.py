"""
URL configuration for cajaclara project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from finanzas.views import (
    ApiCatalogView,
    CuentaPorCobrarListView,
    DetalleVentaListView,
    ExportarExcelView,
    OpcionesFiltrosView,
    ProductoListView,
    ResumenAgrupadoView,
    ResumenFinancieroView,
)
from finanzas.views_escritura import (
    AnularFacturaView,
    ClienteListCreateView,
    FacturaDetalleView,
    FacturaListCreateView,
    GastoListCreateView,
    PagarCuentaView,
    RevertirPagoView,
)

urlpatterns = [
    # Panel de administración
    path('admin/', admin.site.urls),

    # Login, renovación de token, logout y perfil (JWT)
    path('api/auth/', include('usuarios.urls')),

    # Catálogo de documentación de la API (público, no requiere login)
    path('api/', ApiCatalogView.as_view(), name='api-catalog'),
    path('api/finanzas/', ApiCatalogView.as_view(), name='api-finanzas-catalog'),

    # Opciones de filtros para el Frontend (categorías, unidades, fechas min/max)
    path('api/finanzas/opciones-filtros/', OpcionesFiltrosView.as_view(), name='opciones-filtros'),

    # Analítica y KPIs
    path('api/finanzas/resumen-mensual/', ResumenFinancieroView.as_view(), name='resumen-mensual'),
    path('api/finanzas/resumen-agrupado/', ResumenAgrupadoView.as_view(), name='resumen-agrupado'),
    path('api/finanzas/exportar-excel/', ExportarExcelView.as_view(), name='exportar-excel'),

    # Entidades principales con paginación y búsqueda
    # GET lista y POST registra (clientes, facturas y gastos)
    path('api/finanzas/clientes/', ClienteListCreateView.as_view(), name='cliente-list'),
    path('api/finanzas/productos/', ProductoListView.as_view(), name='producto-list'),
    path('api/finanzas/facturas/', FacturaListCreateView.as_view(), name='factura-list'),
    path('api/finanzas/facturas/<str:pk>/', FacturaDetalleView.as_view(), name='factura-detalle'),
    path('api/finanzas/facturas/<str:pk>/anular/', AnularFacturaView.as_view(), name='factura-anular'),
    path('api/finanzas/ventas/', DetalleVentaListView.as_view(), name='detalleventa-list'),
    path('api/finanzas/cuentas-por-cobrar/', CuentaPorCobrarListView.as_view(), name='cuentaporcobrar-list'),
    path('api/finanzas/cuentas-por-cobrar/<int:pk>/pagar/', PagarCuentaView.as_view(), name='cuenta-pagar'),
    path('api/finanzas/cuentas-por-cobrar/<int:pk>/revertir-pago/', RevertirPagoView.as_view(), name='cuenta-revertir-pago'),
    path('api/finanzas/gastos/', GastoListCreateView.as_view(), name='gastoinsumo-list'),
]
