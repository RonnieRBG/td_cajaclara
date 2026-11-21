"""
Asignación de ID nuevos.

En el esquema del equipo de datos, id_cliente, id_detalle, id_cuenta e id_gasto son
INTEGER PRIMARY KEY sin secuencia: la base de datos no los genera sola. El backend
asigna el siguiente número (el mayor + 1).

Si dos personas guardan al mismo tiempo pueden calcular el mismo número; la base de
datos rechaza el segundo (llave duplicada) y `con_reintentos` vuelve a intentar con
el número siguiente.
"""

import uuid

from django.db import IntegrityError, transaction
from django.db.models import Max

INTENTOS = 5


class SinIdDisponible(Exception):
    pass


def siguiente_id(modelo):
    return (modelo.objects.aggregate(maximo=Max("pk"))["maximo"] or 0) + 1


def con_reintentos(funcion):
    """Ejecuta `funcion()` dentro de un savepoint; si choca por llave duplicada, reintenta."""
    for _ in range(INTENTOS):
        try:
            with transaction.atomic():
                return funcion()
        except IntegrityError:
            continue
    raise SinIdDisponible("No se pudo asignar un número nuevo. Intenta de nuevo.")


def nuevo_id_factura(fecha, tipo_compra):
    """Mismo estilo que las facturas del CSV (INV7811414-20100105-F)"""
    from .models import Venta

    canal = "L" if tipo_compra == Venta.EN_LINEA else "F"
    return f"CC{uuid.uuid4().hex[:8].upper()}-{fecha:%Y%m%d}-{canal}"
