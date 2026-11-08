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
from django.urls import path
from finanzas.views import (
    ApiCatalogView,
    ClienteListView,
    CuentaPorCobrarListView,
    DetalleVentaListView,
    ExportarExcelView,
    FacturaListView,
    GastoInsumoListView,
    OpcionesFiltrosView,
    ProductoListView,
    ResumenAgrupadoView,
    ResumenFinancieroView,
)

urlpatterns = [
    # Panel de administración
    path('admin/', admin.site.urls),

    # Catálogo de documentación de la API
    path('api/', ApiCatalogView.as_view(), name='api-catalog'),
    path('api/finanzas/', ApiCatalogView.as_view(), name='api-finanzas-catalog'),

    # Opciones de filtros para el Frontend (categorías, unidades, fechas min/max)
    path('api/finanzas/opciones-filtros/', OpcionesFiltrosView.as_view(), name='opciones-filtros'),

    # Analítica y KPIs
    path('api/finanzas/resumen-mensual/', ResumenFinancieroView.as_view(), name='resumen-mensual'),
    path('api/finanzas/resumen-agrupado/', ResumenAgrupadoView.as_view(), name='resumen-agrupado'),
    path('api/finanzas/exportar-excel/', ExportarExcelView.as_view(), name='exportar-excel'),

    # Entidades principales con paginación y búsqueda
    path('api/finanzas/clientes/', ClienteListView.as_view(), name='cliente-list'),
    path('api/finanzas/productos/', ProductoListView.as_view(), name='producto-list'),
    path('api/finanzas/facturas/', FacturaListView.as_view(), name='factura-list'),
    path('api/finanzas/ventas/', DetalleVentaListView.as_view(), name='detalleventa-list'),
    path('api/finanzas/cuentas-por-cobrar/', CuentaPorCobrarListView.as_view(), name='cuentaporcobrar-list'),
    path('api/finanzas/gastos/', GastoInsumoListView.as_view(), name='gastoinsumo-list'),
]
