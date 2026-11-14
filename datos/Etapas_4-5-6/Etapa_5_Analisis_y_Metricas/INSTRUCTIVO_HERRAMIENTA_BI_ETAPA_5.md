# Instructivo de Selección de Herramienta y Prototipo BI — Etapa 5 (Análisis y Métricas)

> **Propósito:** Justificar la elección de la herramienta de análisis/visualización antes de construir las métricas de negocio (Tareas 22 a 28) y entregar la guía paso a paso (sin programación) para replicar todo el análisis en un prototipo de producción conectado a **Neon PostgreSQL**.

---

## 1. Elección de la Herramienta de Análisis y BI (Antes de las Métricas)

Con la base relacional ya definida en **Neon (PostgreSQL)** en la Etapa 4 (~248 mil filas en 6 tablas), se evaluaron 4 herramientas para ejecutar la Etapa 5 y preparar el panel de la Etapa 6:

| Criterio | **Power BI Desktop + Vistas SQL** ✅ Elegido | **Looker Studio** | **Tableau Public** | **Microsoft Excel** |
| :--- | :--- | :--- | :--- | :--- |
| **Costo para prototipo** | **Gratis ($0)** en Windows | **Gratis ($0)** en navegador | **Gratis ($0)** | Requiere licencia Microsoft 365 |
| **Conexión a Neon PostgreSQL** | Conector nativo incluido (**Npgsql** con SSL, sin drivers aparte) | Conector nativo PostgreSQL | ❌ No conecta directo a PostgreSQL (solo archivos locales / Sheets) | Requiere driver ODBC/Npgsql manual |
| **Impacto sobre capa gratuita de Neon** | **Mínimo (Modo Import):** descarga el snapshot a memoria (VertiPaq) y filtra local sin gastar CU-horas por cada clic | **Alto (Live Query):** cada filtro envía consultas SQL en vivo a Neon, consumiendo las 100 CU-horas/mes | N/A (sin conexión directa) | Manual |
| **Privacidad de datos (Tarea 38)** | **Privado:** el archivo `.pbix` vive en el equipo/repositorio privado | Privado por enlace Google Workspace | ❌ **Público:** obliga a publicar el tablero en internet para guardar | Privado |
| **Modelado relacional y métricas (Tareas 22–28)** | Modelo de 6 tablas + medidas **DAX** reutilizables y formato CLP nativo | Modelado limitado (requiere vistas SQL previas para joins complejos) | Bueno, pero sin SQL live gratuito | Lento al cruzar 100k+ filas con `BUSCARV`/PowerPivot |

### ¿Por qué elegimos **Power BI Desktop** apoyado en **Vistas SQL de PostgreSQL**?
1. **Cero costo y cero fricción en Windows:** El equipo ya trabaja en entorno Windows/Excel (`Tareas.xlsx`), y Power BI Desktop incluye el conector PostgreSQL de fábrica sin instalar drivers externos.
2. **Protege la cuota gratuita de Neon:** Usando **Modo Importar** (en memoria VertiPaq), las 248 mil filas ocupan menos de **5 MB** comprimidos en `.pbix`, logrando filtros instantáneos sin despertar ni consumir el cómputo de Neon en cada interacción.
3. **Privacidad y rigor financiero:** Permite mantener los datos protegidos en privado (a diferencia de Tableau Public) y aplicar medidas **DAX** exactas en Pesos Chilenos (`$#,##0`) sin decimales.
4. **Arquitectura híbrida preparada para Etapa 6 (`Tarea 30`):** Las 7 métricas principales también quedan materializadas como **Vistas SQL** en PostgreSQL (`vistas_metricas_postgresql.sql`). Así, Power BI consume métricas estandarizadas *y* el backend Python/Django o un enlace web futuro en Looker Studio pueden consultar exactamente los mismos cálculos sin duplicar lógica.

---

## 2. Paso a Paso: Conectar Power BI Desktop a la Nube (Neon)

1. Descarga e instala **Power BI Desktop** (gratis desde Microsoft Store o [powerbi.microsoft.com](https://powerbi.microsoft.com/es-es/downloads/)).
2. Abre Power BI Desktop → **Inicio → Obtener datos → Más... → Base de datos → Base de datos PostgreSQL → Conectar**.
3. Completa los datos de tu proyecto Neon (usando el usuario **de solo lectura** creado en la Tarea 21):
   - **Servidor:** `ep-xxxx.aws.neon.tech` *(solo el host, sin `postgresql://` ni `:5432`)*
   - **Base de datos:** `neondb`
   - **Modo de conectividad de datos:** selecciona **Importar** *(recomendado para velocidad y ahorro de cuota Neon)*.
4. En la ventana de credenciales, selecciona pestaña **Base de datos**:
   - **Nombre de usuario:** `cajaclara_lectura_bi`
   - **Contraseña:** *(la clave segura asignada en `roles_y_permisos_postgresql.sql`)*
   - Nivel de aplicación: `ep-xxxx.aws.neon.tech` → **Conectar** *(si pregunta por cifrado SSL, acepta conexión cifrada)*.
5. En el **Navegador**, marca las **6 tablas base** (`cliente`, `producto`, `venta`, `detalle_venta`, `cuenta_por_cobrar`, `gastos_insumo`) **y opcionalmente las 7 vistas** (`vw_margen_producto_categoria`, `vw_ventas_categoria_mes`, `vw_flujo_caja_mensual`, `vw_cuentas_por_cobrar_cliente`, `vw_indicador_morosidad`, `vw_ranking_productos`, `vw_sustentabilidad_negocio`) → clic en **Cargar**.

> 💡 **Modo alternativo offline (sin nube todavía):** Si quieres probar localmente antes de subir a Neon, en **Obtener datos → Texto o CSV** carga los 6 archivos de `datos/Etapas_4-5-6/Etapa_4_Carga_y_Nube/datos_procesados/`.

---

## 3. Configuración del Modelo Relacional y Tabla Calendario

En la vista **Modelo** (ícono izquierdo inferior), verifica que existan exactamente estas relaciones:

| Desde (Lado `1`) | Hacia (Lado `*` o `1`) | Cardinalidad | Dirección de filtro |
| :--- | :--- | :---: | :--- |
| `cliente[id_cliente]` | `venta[id_cliente]` | `1 : *` | Única (`cliente → venta`) |
| `cliente[id_cliente]` | `cuenta_por_cobrar[id_cliente]` | `1 : *` | Única (o inactiva si filtras por `venta`) |
| `venta[id_factura]` | `detalle_venta[id_factura]` | `1 : *` | Única (`venta → detalle_venta`) |
| `venta[id_factura]` | `cuenta_por_cobrar[id_factura]` | `1 : 1` *(0..1)* | Única (`venta → cuenta_por_cobrar`) |
| `producto[id_producto]` | `detalle_venta[id_producto]` | `1 : *` | Única (`producto → detalle_venta`) |
| `producto[id_producto]` | `gastos_insumo[id_producto]` | `1 : *` | Única (`producto → gastos_insumo`) |

### Crear Tabla `Calendario` y Columna de Cobertura
En **Modelado → Nueva tabla**, pega esta fórmula DAX para unificar las fechas de ventas, cobros y gastos:
```dax
Calendario = 
ADDCOLUMNS(
    CALENDAR(DATE(2010, 1, 1), DATE(2022, 12, 31)),
    "Año", YEAR([Date]),
    "Mes Num", MONTH([Date]),
    "Mes", FORMAT([Date], "mmm", "es-CL"),
    "Periodo", FORMAT([Date], "YYYY-MM"),
    "Cobertura", IF([Date] <= DATE(2020, 12, 31), "completa", "parcial")
)
```
* Conecta `Calendario[Date]` → `venta[fecha]` (`1 : *`, **activa**).
* Conecta `Calendario[Date]` → `cuenta_por_cobrar[fecha_pago]` (`1 : *`, **inactiva**, se activa con `USERELATIONSHIP` para flujo de caja).
* Conecta `Calendario[Date]` → `gastos_insumo[fecha]` (`1 : *`, **inactiva**, se activa con `USERELATIONSHIP` para flujo de caja y gastos).
* Marca `Calendario` como **Tabla de fechas** (clic derecho → *Marcar como tabla de fechas* → `Date`).

> ⚠️ **Regla clave de análisis:** En todos los gráficos de tendencia anual, flujo de caja y sustentabilidad, agrega un **filtro de página o informe** con `Calendario[Cobertura] = "completa"` (2010–2020), ya que 2021–2022 tiene muestreo parcial en el origen.

---

## 4. Medidas DAX Listas para Copiar (Tareas 22 a 28)

Crea una tabla vacía (**Inicio → Introducir datos** *(o `Especificar datos` en versiones anteriores)* → nombrar `_Medidas` → **Cargar**) y agrega **una por una** estas medidas usando **Nueva medida** (con formato **Moneda**, `0` decimales, o **Porcentaje**, `1` decimal). Luego oculta `Columna 1` para que `_Medidas` quede como carpeta de cálculo:

```dax
// ── Tareas 22 y 23: Ventas, Costos y Margen ───────────────────────────────────
Ventas Facturadas = 
SUMX(detalle_venta, detalle_venta[cantidad] * detalle_venta[precio_venta])

Costo Ventas = 
SUMX(detalle_venta, detalle_venta[cantidad] * detalle_venta[costo_venta])

Margen Bruto = 
[Ventas Facturadas] - [Costo Ventas]

Margen % = 
DIVIDE([Margen Bruto], [Ventas Facturadas], 0)

Unidades Vendidas = 
SUM(detalle_venta[cantidad])

// ── Tarea 24: Flujo de Caja Mensual (Efectivamente Cobrado - Gastos) ──────────
Ingresos Contado = 
CALCULATE([Ventas Facturadas], venta[por_cobrar] = FALSE())

Cobros Fiado Recibidos = 
CALCULATE(
    SUM(cuenta_por_cobrar[monto]),
    cuenta_por_cobrar[estado] = "PAGADA",
    USERELATIONSHIP(Calendario[Date], cuenta_por_cobrar[fecha_pago])
)

Ingresos Efectivamente Cobrados = 
[Ingresos Contado] + [Cobros Fiado Recibidos]

Gastos Insumo = 
CALCULATE(
    SUM(gastos_insumo[monto]),
    USERELATIONSHIP(Calendario[Date], gastos_insumo[fecha])
)

Flujo de Caja Neto = 
[Ingresos Efectivamente Cobrados] - [Gastos Insumo]

// ── Tareas 25 y 26: Cuentas por Cobrar y Morosidad ────────────────────────────
Total Fiado Emitido = 
SUM(cuenta_por_cobrar[monto])

Cartera Abierta Actual = 
CALCULATE(
    SUM(cuenta_por_cobrar[monto]),
    cuenta_por_cobrar[estado] IN {"PENDIENTE", "VENCIDA"}
)

Cartera Vencida Actual = 
CALCULATE(
    SUM(cuenta_por_cobrar[monto]),
    cuenta_por_cobrar[estado] = "VENCIDA"
)

Morosidad Activa % = 
DIVIDE([Cartera Vencida Actual], [Cartera Abierta Actual], 0)

// ── Tarea 28: Sustentabilidad del Negocio ─────────────────────────────────────
Utilidad Neta Operativa = 
[Margen Bruto] - [Gastos Insumo]

Ratio Cobertura Gastos = 
DIVIDE([Margen Bruto], [Gastos Insumo], 0)

Ratio Fiado sobre Margen % = 
DIVIDE([Total Fiado Emitido], [Margen Bruto], 0)
```

---

## 5. Estructura del Prototipo de Panel (Puente hacia Etapa 6)

Organiza tu archivo `CajaClara_Analisis_Etapa5.pbix` en **4 páginas** (que luego sirven directamente como base del panel final de la Etapa 6):

1. **Página 1 — Resumen Ejecutivo y Sustentabilidad (Tareas 22, 23, 28):**
   - Tarjetas KPI: `Ventas Facturadas`, `Margen Bruto`, `Margen %`, `Gastos Insumo`, `Utilidad Neta Operativa`, `Ratio Cobertura Gastos`.
   - Gráfico de barras horizontales: `Ventas Facturadas` y `Margen Bruto` por `producto[categoria]`.
   - Gráfico combinado anual (`2010–2020`, `Cobertura = completa`): Columnas `Margen Bruto` vs `Total Fiado Emitido` + Línea `Gastos Insumo`.
2. **Página 2 — Flujo de Caja Mensual (Tarea 24):**
   - Segmentador por `Calendario[Año]` y `Calendario[Cobertura]`.
   - Gráfico de líneas comparando `Ventas Facturadas` vs `Ingresos Efectivamente Cobrados` por `Calendario[Periodo]`.
   - Gráfico de columnas: `Flujo de Caja Neto` mensual.
3. **Página 3 — Productos Estrella y Baja Venta (Tarea 27):**
   - Conecta directamente la vista `vw_ranking_productos` para mostrar un **gráfico de dispersión** (`ventas` vs `margen`, color por `clasificacion_desempeno`) y dos tablas: **Top 10 Estrella** y **Top 10 Baja Venta / Reajuste de Precio** (filtrando `alerta_escala_etapa2 = FALSE`).
4. **Página 4 — Cuentas por Cobrar y Morosidad (Tareas 25 y 26):**
   - Tarjetas KPI desde `vw_indicador_morosidad`: `Morosidad Activa %`, `Cartera Abierta Actual`, `Cartera Vencida Actual`.
   - Tabla operativa desde `vw_cuentas_por_cobrar_cliente` filtrada a `cuentas_abiertas > 0` (para saber **a quién, cuánto y cuándo cobrar**, ordenado por `max_dias_atraso_actual DESC`).
