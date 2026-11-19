"""
Alertas de cobro (Tarea 29 del equipo de datos): cuentas vencidas o próximas a vencer.

Usa la MISMA lógica que la vista `vw_alertas_cobro` del equipo de datos
(Etapa_6_Alertas_y_Visualizacion/alertas_cobro_postgresql.sql): mismas prioridades,
mismos nombres de campo y el mismo mensaje sugerido.

La única diferencia es la fecha de corte: la vista usa una fecha fija (2022-09-01,
para el análisis histórico y Power BI) y la API usa la fecha de HOY, como indica la
"Sección B" de ese mismo script para la operación en vivo. Con ?fecha_corte=2022-09-01
la API entrega exactamente lo mismo que la vista.
"""

from datetime import timedelta

from django.db.models import Case, CharField, Count, IntegerField, Q, Sum, Value, When
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from .models import CuentaPorCobrar
from .views import FiltroInvalido, StandardResultsSetPagination, VALORES_VERDADEROS, _parsear_fecha

CRITICA = "1_CRITICA_VENCIDA"
ALTA = "2_ALTA_PROXIMA_7D"
MEDIA = "3_MEDIA_PROXIMA_15D"
BAJA = "4_BAJA_VIGENTE"
PRIORIDADES = {
    CRITICA: "Vencida",
    ALTA: "Vence en <= 7 días",
    MEDIA: "Vence en 8-15 días",
    BAJA: "Vigente > 15 días",
}
ALIAS_PRIORIDAD = {"CRITICA": CRITICA, "ALTA": ALTA, "MEDIA": MEDIA, "BAJA": BAJA}
DIAS_AVISO = 15


def cuentas_con_alerta(corte):
    """Cuentas abiertas (sin pagar) con su prioridad a la fecha de corte."""
    vencida = Q(estado=CuentaPorCobrar.VENCIDA) | Q(fecha_vencimiento__lt=corte)
    return (
        CuentaPorCobrar.objects.filter(
            estado__in=[CuentaPorCobrar.PENDIENTE, CuentaPorCobrar.VENCIDA], fecha_pago__isnull=True
        )
        .select_related("cliente", "venta")
        .annotate(
            prioridad_alerta=Case(
                When(vencida, then=Value(CRITICA)),
                When(fecha_vencimiento__lte=corte + timedelta(days=7), then=Value(ALTA)),
                When(fecha_vencimiento__lte=corte + timedelta(days=15), then=Value(MEDIA)),
                default=Value(BAJA),
                output_field=CharField(),
            ),
            orden_alerta=Case(When(vencida, then=Value(0)), default=Value(1), output_field=IntegerField()),
        )
    )


def armar_alerta(cuenta, corte):
    """Un registro con los mismos campos que vw_alertas_cobro."""
    dias_para_vencer = (cuenta.fecha_vencimiento - corte).days
    vencida = cuenta.prioridad_alerta == CRITICA
    cliente = cuenta.cliente
    if vencida:
        mensaje = (
            f"Recordatorio urgente: cliente {cliente.nombre} mantiene factura {cuenta.venta_id} "
            f"vencida hace {-dias_para_vencer} días por ${cuenta.monto}."
        )
    else:
        mensaje = (
            f"Aviso preventivo: factura {cuenta.venta_id} de {cliente.nombre} vence el "
            f"{cuenta.fecha_vencimiento:%Y-%m-%d} (en {dias_para_vencer} días) por ${cuenta.monto}."
        )
    return {
        "id_cuenta": cuenta.id_cuenta,
        "id_factura": cuenta.venta_id,
        "id_cliente": cliente.id_cliente,
        "cliente_nombre": cliente.nombre,
        "cliente_contacto": cliente.contacto,
        "fecha_emision": cuenta.venta.fecha,
        "fecha_vencimiento": cuenta.fecha_vencimiento,
        "estado": cuenta.estado,
        "monto": cuenta.monto,
        "dias_para_vencer": dias_para_vencer,
        "dias_atraso": max(-dias_para_vencer, 0),
        "tipo_alerta": "VENCIDA" if vencida else "POR_VENCER",
        "prioridad_alerta": cuenta.prioridad_alerta,
        "ventana_alerta": PRIORIDADES[cuenta.prioridad_alerta],
        "requiere_notificacion": cuenta.estado == CuentaPorCobrar.VENCIDA or dias_para_vencer <= DIAS_AVISO,
        "mensaje_sugerido": mensaje,
    }


class AlertasCobroView(generics.GenericAPIView):
    """
    GET /api/finanzas/alertas-cobro/
    Cuentas por cobrar vencidas o que vencen pronto, ordenadas por urgencia
    (vencidas primero, luego por fecha de vencimiento y monto).

    Parámetros opcionales:
      - dias_aviso: cuántos días hacia adelante avisar (por defecto 15).
      - prioridad: CRITICA, ALTA, MEDIA o BAJA (o el código completo, ej. 1_CRITICA_VENCIDA).
      - cliente: id_cliente.
      - todas: true = incluye también las vigentes que vencen después de la ventana.
      - fecha_corte: calcula a esa fecha en vez de hoy (ej. 2022-09-01 para comparar con Power BI).
      - page, page_size: paginación.
    El bloque "resumen" trae cantidad y monto por prioridad.
    """

    pagination_class = StandardResultsSetPagination

    def _parametros(self):
        params = self.request.query_params
        try:
            corte = _parsear_fecha(params["fecha_corte"], "fecha_corte") if params.get("fecha_corte") else None
        except FiltroInvalido as error:
            raise ValidationError({"error": str(error)})
        dias = (params.get("dias_aviso") or str(DIAS_AVISO)).strip()
        if not dias.isdigit() or int(dias) > 365:
            raise ValidationError({"error": "'dias_aviso' debe ser un número entre 0 y 365."})
        return corte or timezone.localdate(), int(dias)

    def get_queryset(self):
        params = self.request.query_params
        self.corte, self.dias_aviso = self._parametros()
        qs = cuentas_con_alerta(self.corte)

        if (params.get("todas") or "").strip().lower() not in VALORES_VERDADEROS:
            qs = qs.filter(
                Q(prioridad_alerta=CRITICA)
                | Q(fecha_vencimiento__lte=self.corte + timedelta(days=self.dias_aviso))
            )

        prioridad = (params.get("prioridad") or "").strip().upper()
        if prioridad:
            prioridad = ALIAS_PRIORIDAD.get(prioridad, prioridad)
            if prioridad not in PRIORIDADES:
                raise ValidationError({"error": f"'prioridad' inválida. Usa: {', '.join(ALIAS_PRIORIDAD)}."})
            qs = qs.filter(prioridad_alerta=prioridad)

        cliente = (params.get("cliente") or "").strip()
        if cliente:
            if not cliente.isdigit():
                raise ValidationError({"error": "'cliente' debe ser un id_cliente numérico."})
            qs = qs.filter(cliente_id=int(cliente))

        return qs.order_by("orden_alerta", "fecha_vencimiento", "-monto", "id_cuenta")

    def get(self, request):
        qs = self.get_queryset()
        pagina = self.paginate_queryset(qs)
        respuesta = self.get_paginated_response([armar_alerta(cuenta, self.corte) for cuenta in pagina])

        por_prioridad = {
            codigo: {"nombre": nombre, "cantidad": 0, "monto": 0} for codigo, nombre in PRIORIDADES.items()
        }
        for fila in qs.order_by().values("prioridad_alerta").annotate(cantidad=Count("pk"), total=Sum("monto")):
            por_prioridad[fila["prioridad_alerta"]].update(cantidad=fila["cantidad"], monto=fila["total"] or 0)
        respuesta.data["resumen"] = {
            "fecha_corte": self.corte,
            "dias_aviso": self.dias_aviso,
            "total_alertas": sum(p["cantidad"] for p in por_prioridad.values()),
            "monto_total": sum(p["monto"] for p in por_prioridad.values()),
            "por_prioridad": por_prioridad,
        }
        return respuesta
