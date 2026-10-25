from django.contrib import admin
from .models import Categoria, Movimiento, CuentaPorCobrar

admin.site.register(Categoria)
admin.site.register(Movimiento)
admin.site.register(CuentaPorCobrar)