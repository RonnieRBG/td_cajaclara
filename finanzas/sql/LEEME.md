# Vistas de métricas del equipo de datos

Estos dos archivos son una **copia sin cambios** de la rama `datos` (commit `fcef63e`):

- `datos/Etapas_4-5-6/Etapa_5_Analisis_y_Metricas/vistas_metricas_postgresql.sql`
- `datos/Etapas_4-5-6/Etapa_5_Analisis_y_Metricas/vistas_metricas_sqlite.sql`

**No se editan aquí.** Las vistas las define el equipo de datos; si las cambian, se vuelven a copiar.

- En **Neon** ya existen (las creó el equipo de datos y Power BI las usa). El backend solo las lee.
- En **local**, `python manage.py crear_vistas_metricas` las crea con estos archivos
  (`importar_csv` lo hace solo al terminar).

La API las expone en `/api/finanzas/metricas/...` (ver `finanzas/metricas.py`).
