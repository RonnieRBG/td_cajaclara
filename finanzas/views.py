from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.utils.timezone import now
from .models import Movimiento, Categoria

class ResumenFinancieroView(APIView):
   
    # permission_classes = [IsAuthenticated] 

    def get(self, request):
       
        from django.contrib.auth.models import User
        usuario = User.objects.first() 
        
        if not usuario:
            return Response({"error": "No hay usuarios en la base de datos para probar."}, status=400)

        
        hoy = now().date()
        mes_actual = hoy.month
        anio_actual = hoy.year

    
        movimientos_mes = Movimiento.objects.filter(
            usuario=usuario,
            fecha__year=anio_actual,
            fecha__month=mes_actual
        )

        
        total_ingresos = movimientos_mes.filter(
            categoria__tipo='INGRESO'
        ).aggregate(total=Sum('monto'))['total'] or 0

       
        total_gastos = movimientos_mes.filter(
            categoria__tipo='GASTO'
        ).aggregate(total=Sum('monto'))['total'] or 0

        
        saldo_mes = total_ingresos - total_gastos

        return Response({
            "mes": mes_actual,
            "anio": anio_actual,
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "flujo_caja": saldo_mes
        })