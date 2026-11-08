ad# 📘 Documentación Técnica de API y Desacoplamiento (Caja Clara)

Este documento contiene las especificaciones para que el **Equipo de Base de Datos** y el **Equipo de Frontend** puedan conectar y desplegar sus partes de manera 100% independiente sin tocar el código backend.

---

## 🗄️ PARTE 1: Guía para el Equipo de Base de Datos

El backend en Django ha sido configurado para ser **completamente agnóstico** al motor de base de datos relacional.

### 1. Variables de Entorno soportadas

Por defecto, el backend corre en desarrollo local con SQLite (`db.sqlite3`). Para conectar cualquier motor de base de datos de producción (PostgreSQL, MySQL, Google Cloud SQL, etc.), simplemente define las siguientes variables de entorno:

| Variable      | Descripción                               | Ejemplo (PostgreSQL)                       | Ejemplo (MySQL)            |
| :------------ | :---------------------------------------- | :----------------------------------------- | :------------------------- |
| `DB_ENGINE`   | Driver del motor de base de datos         | `django.db.backends.postgresql`            | `django.db.backends.mysql` |
| `DB_NAME`     | Nombre de la base de datos                | `cajaclara_db`                             | `cajaclara_db`             |
| `DB_USER`     | Usuario con permisos de lectura/escritura | `postgres` o `admin`                       | `root` o `app_user`        |
| `DB_PASSWORD` | Contraseña del usuario                    | `tu_password_segura`                       | `tu_password_segura`       |
| `DB_HOST`     | Host o IP del servidor de base de datos   | `localhost` o `10.x.x.x` o Cloud SQL Proxy | `127.0.0.1`                |
| `DB_PORT`     | Puerto de conexión                        | `5432`                                     | `3306`                     |

_Ejemplo en PowerShell para desarrollo/pruebas:_

```powershell
$env:DB_ENGINE="django.db.backends.postgresql"
$env:DB_NAME="cajaclara"
$env:DB_USER="postgres"
$env:DB_PASSWORD="secretpassword"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="5432"
```

### 2. Aplicar el esquema y tablas (Migraciones)

Una vez configuradas las variables de conexión hacia la base de datos de destino, ejecuta:

```bash
python manage.py migrate
```

Esto creará automáticamente todas las tablas relacionales, llaves foráneas e índices optimizados (`fecha`, `estado_pago`, etc.).

### 3. Cargar el dataset inicial (Seeding / Ingesta)

Para poblar la base de datos con los 6 archivos CSV del supermercado:

```bash
python manage.py importar_csv
```

_Si se requiere vaciar la base de datos antes de importar de nuevo, usar:_

```bash
python manage.py importar_csv --limpiar
```

---

## 🎨 PARTE 2: Guía para el Equipo de Frontend

- **URL Base en desarrollo:** `http://localhost:8000`
- **CORS:** Habilitado para todos los orígenes (`CORS_ALLOW_ALL_ORIGINS = True`). No habrá bloqueos de CORS en React, Vue, Angular o Next.js.
- **Formato de fechas:** Acepta tanto `DD/MM/AAAA` como `AAAA-MM-DD`.
- **Paginación estándar:** Todos los listados devuelven la estructura:
  ```json
  {
    "count": 100067,
    "next": "http://localhost:8000/api/finanzas/facturas/?page=2",
    "previous": null,
    "results": [ ... ]
  }
  ```
  Puedes cambiar el tamaño de página usando `?page_size=20` (por defecto: 50, máximo: 500).

---

### Catálogo de Endpoints

#### 1. Metadatos y Dropdowns para la UI

- **Ruta:** `GET /api/finanzas/opciones-filtros/`
- **Descripción:** Retorna todas las categorías, unidades de negocio, tipos de compra y el rango mínimo/máximo de fechas en la BD para que inicialices tus `<select>` y selectores de fecha dinámicamente.
- **Respuesta de ejemplo:**

```json
{
  "categorias": ["Abarrotes", "Carnes", "Lácteos", "Limpieza", ...],
  "unidades_negocio": ["Supermercado"],
  "tipos_compra": [
    {"codigo": "FISICA", "nombre": "Física"},
    {"codigo": "ONLINE", "nombre": "En línea"}
  ],
  "estados_pago": [
    {"codigo": "PAGADO", "nombre": "Pagado"},
    {"codigo": "PENDIENTE", "nombre": "Pendiente"},
    {"codigo": "ANULADO", "nombre": "Anulado"}
  ],
  "rango_fechas_disponible": {
    "min": "2010-01-05",
    "max": "2022-11-18",
    "min_display": "05/01/2010",
    "max_display": "18/11/2022"
  }
}
```

---

#### 2. Resumen de KPIs Financieros

- **Ruta:** `GET /api/finanzas/resumen-mensual/`
- **Query Params opcionales:**
  - `fecha_inicio`: Ej. `01/01/2010` o `2010-01-01`
  - `fecha_fin`: Ej. `31/12/2012` o `2012-12-31`
  - `tipo_compra`: `FISICA` u `ONLINE`
- **Respuesta de ejemplo:**

```json
{
  "rango_aplicado": {
    "fecha_inicio": "01/01/2010",
    "fecha_fin": "31/12/2012",
    "periodo_tipo": "personalizado"
  },
  "filtro_tipo_compra": "TODOS",
  "total_transacciones": 15870,
  "total_ingresos": 80226136.0,
  "total_costos": 61255452.0,
  "flujo_caja_neto": 18970684.0,
  "margen_porcentaje": 23.65,
  "por_estado_pago": {
    "PAGADO": {
      "nombre": "Pagado",
      "transacciones": 13537,
      "ingresos": 69219397.0
    },
    "PENDIENTE": {
      "nombre": "Pendiente",
      "transacciones": 2333,
      "ingresos": 11006739.0
    },
    "ANULADO": { "nombre": "Anulado", "transacciones": 0, "ingresos": 0.0 }
  }
}
```

---

#### 3. Serie Temporal para Gráficos

- **Ruta:** `GET /api/finanzas/resumen-agrupado/`
- **Query Params opcionales:**
  - `agrupacion`: `diaria`, `mensual`, `trimestral`, `anual` (default: `mensual`)
  - `fecha_inicio`, `fecha_fin`, `tipo_compra`
- **Respuesta de ejemplo:**

```json
{
  "agrupacion": "mensual",
  "totales": {
    "transacciones": 15870,
    "ingresos": 80226136.0,
    "costos": 61255452.0,
    "utilidad": 18970684.0,
    "margen_porcentaje": 23.65
  },
  "periodos": [
    {
      "periodo": "Ene 2010",
      "fecha_inicio": "01/01/2010",
      "fecha_fin": "31/01/2010",
      "transacciones": 420,
      "ingresos": 2150400.0,
      "costos": 1640000.0,
      "utilidad": 510400.0,
      "margen_porcentaje": 23.74
    }
  ]
}
```

---

#### 4. Exportación Excel

- **Ruta:** `GET /api/finanzas/exportar-excel/`
- **Query Params:** Mismos que resumen (`fecha_inicio`, `fecha_fin`, `tipo_compra`).
- **Respuesta:** Archivo binario `.xlsx` con encabezados formateados y celdas contables automáticas.

---

#### 5. Listado de Clientes

- **Ruta:** `GET /api/finanzas/clientes/`
- **Query Params opcionales:**
  - `search`: Búsqueda textual por nombre, ID o teléfono.
  - `page`, `page_size`: Paginación.
- **Respuesta de ejemplo:**

```json
{
  "count": 2000,
  "next": "http://localhost:8000/api/finanzas/clientes/?page=2",
  "previous": null,
  "results": [
    {
      "cliente_id": "1",
      "nombre": "José Paredes Soto",
      "contacto": "+56 9 4949 4897",
      "total_facturas": 54,
      "total_deuda": "125000.00"
    }
  ]
}
```

---

#### 6. Listado de Productos

- **Ruta:** `GET /api/finanzas/productos/`
- **Query Params opcionales:**
  - `search`: Búsqueda por nombre o código `no_parte`.
  - `categoria`: Ej. `Abarrotes`, `Lácteos`.
  - `unidad_negocio`: Ej. `Supermercado`.
  - `page`, `page_size`: Paginación.

---

#### 7. Listado de Facturas (Ventas)

- **Ruta:** `GET /api/finanzas/facturas/`
- **Query Params opcionales:**
  - `cliente`: ID del cliente.
  - `tipo_compra`: `FISICA` o `ONLINE`.
  - `por_cobrar`: `true` o `false`.
  - `fecha_inicio`, `fecha_fin`: Rango de fechas.
  - `page`, `page_size`: Paginación.
- **Respuesta de ejemplo:**

```json
{
  "count": 100067,
  "results": [
    {
      "factura": "INV7811414-20100105-F",
      "cliente": "179",
      "cliente_nombre": "Carlos Morales Rojas",
      "fecha": "2010-01-05T00:00:00Z",
      "tipo_compra": "FISICA",
      "tipo_compra_nombre": "Física",
      "por_cobrar": false,
      "fecha_cobro": null,
      "total_venta": "777.00",
      "items_count": 1
    }
  ]
}
```

---

#### 8. Líneas de Venta Detalladas

- **Ruta:** `GET /api/finanzas/ventas/`
- **Query Params opcionales:**
  - `factura`: ID de factura específico.
  - `producto`: N° de parte.
  - `estado_pago`: `PAGADO` o `PENDIENTE`.
  - `page`, `page_size`: Paginación.

---

#### 9. Cuentas por Cobrar (Deuda)

- **Ruta:** `GET /api/finanzas/cuentas-por-cobrar/`
- **Query Params opcionales:**
  - `cliente`: ID de cliente específico.
  - `vencidas`: `true` para solo facturas con fecha de vencimiento pasada, `false` para vigentes.
  - `page`, `page_size`: Paginación.
- **Respuesta con resumen global inyectado:**

```json
{
  "count": 14928,
  "resumen": {
    "total_cuentas": 14928,
    "monto_total_por_cobrar": 57339252.0
  },
  "results": [
    {
      "id": 1,
      "factura": "INV7811412-20100107-L",
      "cliente": "1310",
      "cliente_nombre": "Ana Valenzuela",
      "cliente_contacto": "+56 9 1122 3344",
      "monto": "3288.00",
      "fecha_vencimiento": "2010-02-19",
      "vencida": true
    }
  ]
}
```

---

#### 10. Gastos de Insumo

- **Ruta:** `GET /api/finanzas/gastos/`
- **Query Params opcionales:**
  - `producto`: N° de parte.
  - `categoria`: Categoría de producto.
  - `fecha_inicio`, `fecha_fin`: Rango de fechas.
  - `page`, `page_size`: Paginación.
- **Respuesta con resumen de gastos inyectado:**

```json
{
  "count": 20000,
  "resumen": {
    "total_registros_gasto": 20000,
    "monto_total_gastos": 24484481.0
  },
  "results": [ ... ]
}
```

---

## ⚡ PARTE 3: Guía Específica de Conexión para el Repositorio Frontend (Vue 3 / Vite)

Esta sección detalla los cambios exactos que debe realizar el equipo de Frontend en la aplicación **`ux/prototype/cajaclara-ui/`** para reemplazar los datos estáticos de `dashboardMock.js` por llamadas reales a los endpoints del backend.

### 1. Diagnóstico del Frontend Actual

En la rama `ux`, la aplicación Vue 3 importa los datos de forma síncrona desde:

- `src/views/DashboardView.vue` importa `mockData` desde `@/data/dashboardMock`.
- Los componentes secundarios reciben estos datos como props:
  - `StatCard.vue` $\leftarrow$ `mockData.kpis`
  - `OperationsSummary.vue` $\leftarrow$ `mockData.operationsSummary`
  - `CashChart.vue` $\leftarrow$ `mockData.weeklyFlow`
  - `PriorityCollections.vue` $\leftarrow$ `mockData.priorityCollections`
  - `RecentOperations.vue` $\leftarrow$ `mockData.recentOperations`
  - `TopProducts.vue` $\leftarrow$ `mockData.topProducts`

---

### 2. Paso 1: Configurar la URL Base o Proxy en Vite

Para evitar problemas de URLs absolutas en el código del frontend, edita `ux/prototype/cajaclara-ui/vite.config.js` y agrega la configuración del `proxy`:

```javascript
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
```

_Con este proxy, cualquier petición a `/api/...` se redirige automáticamente al servidor Django en el puerto 8000._

---

### 3. Paso 2: Crear el Módulo de Servicio API (`src/services/api.js`)

Crea un archivo nuevo en `ux/prototype/cajaclara-ui/src/services/api.js` para centralizar todas las peticiones al backend:

```javascript
/**
 * Servicio de conexión con la API de Django (Caja Clara)
 */

const API_BASE = "/api/finanzas";

async function request(endpoint, params = {}) {
  const url = new URL(endpoint, window.location.origin);
  Object.keys(params).forEach((key) => {
    if (
      params[key] !== undefined &&
      params[key] !== null &&
      params[key] !== ""
    ) {
      url.searchParams.append(key, params[key]);
    }
  });

  const res = await fetch(url.toString(), {
    headers: {
      Accept: "application/json",
    },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `Error HTTP: ${res.status}`);
  }

  return res.json();
}

export const apiService = {
  // 1. Opciones para selects y dropdowns (categorías, fechas min/max)
  getOpcionesFiltros() {
    return request(`${API_BASE}/opciones-filtros/`);
  },

  // 2. Indicadores KPI Financieros (Saldo, Ventas, Gastos, Pendientes)
  getResumenFinanciero(filtros = {}) {
    return request(`${API_BASE}/resumen-mensual/`, filtros);
  },

  // 3. Serie temporal para el gráfico de barras (entradas vs salidas)
  getResumenAgrupado(agrupacion = "mensual", filtros = {}) {
    return request(`${API_BASE}/resumen-agrupado/`, { agrupacion, ...filtros });
  },

  // 4. Cobros que requieren atención (cuentas por cobrar vencidas)
  getCuentasPorCobrar(filtros = {}) {
    return request(`${API_BASE}/cuentas-por-cobrar/`, {
      page_size: 5,
      ...filtros,
    });
  },

  // 5. Últimos movimientos de caja (ventas recientes)
  getUltimosMovimientos(filtros = {}) {
    return request(`${API_BASE}/ventas/`, { page_size: 10, ...filtros });
  },

  // 6. Catálogo de productos más demandados
  getProductos(filtros = {}) {
    return request(`${API_BASE}/productos/`, { page_size: 4, ...filtros });
  },

  // 7. URL para descargar el archivo Excel
  getUrlExportarExcel(filtros = {}) {
    const url = new URL(`${API_BASE}/exportar-excel/`, window.location.origin);
    Object.keys(filtros).forEach((key) => {
      if (filtros[key]) url.searchParams.append(key, filtros[key]);
    });
    return url.toString();
  },
};
```

---

### 4. Paso 3: Tabla de Mapeo de Datos (API Backend $\rightarrow$ Props de Componentes)

| Componente Vue            | Variable Esperada en el Mock                   | Propiedad devuelta por la API                                                                                                                                                                                                       | Endpoint Backend                                     |
| :------------------------ | :--------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------- |
| **StatCard** (Saldo)      | `mockData.kpis.saldoPeriodo`                   | `resumen.flujo_caja_neto`                                                                                                                                                                                                           | `/api/finanzas/resumen-mensual/`                     |
| **StatCard** (Ventas)     | `mockData.kpis.ventasMes`                      | `resumen.total_ingresos`                                                                                                                                                                                                            | `/api/finanzas/resumen-mensual/`                     |
| **StatCard** (Gastos)     | `mockData.kpis.comprasGastos`                  | `resumen.total_costos`                                                                                                                                                                                                              | `/api/finanzas/resumen-mensual/`                     |
| **StatCard** (Por Cobrar) | `mockData.kpis.pendienteCobrar`                | `resumen.por_estado_pago.PENDIENTE.ingresos`                                                                                                                                                                                        | `/api/finanzas/resumen-mensual/`                     |
| **CashChart**             | `mockData.weeklyFlow`                          | `agrupado.periodos` $\rightarrow$ `[{ semana: p.periodo, ventas: p.ingresos, gastos: p.costos }]`                                                                                                                                   | `/api/finanzas/resumen-agrupado/?agrupacion=semanal` |
| **OperationsSummary**     | `mockData.operationsSummary.totalVentas`       | `resumen.total_transacciones`                                                                                                                                                                                                       | `/api/finanzas/resumen-mensual/`                     |
| **OperationsSummary**     | `mockData.operationsSummary.cuentasPendientes` | `cuentas.resumen.total_cuentas`                                                                                                                                                                                                     | `/api/finanzas/cuentas-por-cobrar/`                  |
| **PriorityCollections**   | `mockData.priorityCollections`                 | `cuentas.results.map(c => ({ id: c.id, cliente: c.cliente_nombre, documento: c.factura, monto: parseFloat(c.monto), vencimientoTexto: c.vencida ? 'Vencida' : c.fecha_vencimiento, estado: c.vencida ? 'VENCIDA' : 'PENDIENTE' }))` | `/api/finanzas/cuentas-por-cobrar/?vencidas=true`    |
| **RecentOperations**      | `mockData.recentOperations`                    | `ventas.results.map(v => ({ id: v.id, tipo: 'VENTA', concepto: v.categoria, detalle: v.producto_nombre, clienteProveedor: v.tipo_compra, fecha: v.fecha, estado: v.estado_pago, monto: parseFloat(v.total_venta) }))`               | `/api/finanzas/ventas/?page_size=5`                  |

---

### 5. Paso 4: Adaptar `src/views/DashboardView.vue`

En `ux/prototype/cajaclara-ui/src/views/DashboardView.vue`, sustituir la importación estática de `mockData` por un estado reactivo que carga los datos en el hook `onMounted`:

```vue
<script setup>
import { ref, onMounted } from "vue";
import { apiService } from "@/services/api";
import StatCard from "@/components/common/StatCard.vue";
import QuickActions from "@/components/common/QuickActions.vue";
import CashChart from "@/components/dashboard/CashChart.vue";
import OperationsSummary from "@/components/dashboard/OperationsSummary.vue";
import TopProducts from "@/components/dashboard/TopProducts.vue";
import PriorityCollections from "@/components/dashboard/PriorityCollections.vue";
import RecentOperations from "@/components/dashboard/RecentOperations.vue";
import NewOperationModal from "@/components/dashboard/NewOperationModal.vue";

// Estado reactivo del dashboard
const loading = ref(true);
const error = ref(null);

const kpis = ref({
  saldoPeriodo: 0,
  ventasMes: 0,
  comprasGastos: 0,
  pendienteCobrar: 0,
});

const operationsSummary = ref({
  totalVentas: 0,
  totalGastos: 0,
  unidadesVendidas: 0,
  cuentasPendientes: 0,
});

const weeklyFlow = ref([]);
const priorityCollections = ref([]);
const recentOperations = ref([]);
const topProducts = ref([]);

// Carga de datos reales desde el Backend
const cargarDatosDashboard = async () => {
  loading.value = true;
  error.value = null;
  try {
    // 1. Obtener rango de fechas disponible
    const opciones = await apiService.getOpcionesFiltros();
    const filtroRango = {
      fecha_inicio: opciones.rango_fechas_disponible.min_display,
      fecha_fin: opciones.rango_fechas_disponible.max_display,
    };

    // 2. Ejecutar peticiones en paralelo para máximo rendimiento
    const [resumen, agrupado, cuentas, ventas, productos] = await Promise.all([
      apiService.getResumenFinanciero(filtroRango),
      apiService.getResumenAgrupado("mensual", filtroRango),
      apiService.getCuentasPorCobrar({ vencidas: "true", page_size: 5 }),
      apiService.getUltimosMovimientos({ page_size: 5 }),
      apiService.getProductos({ page_size: 4 }),
    ]);

    // 3. Mapear KPIs
    kpis.value = {
      saldoPeriodo: resumen.flujo_caja_neto,
      ventasMes: resumen.total_ingresos,
      comprasGastos: resumen.total_costos,
      pendienteCobrar: resumen.por_estado_pago?.PENDIENTE?.ingresos || 0,
    };

    // 4. Mapear Resumen de Operaciones
    operationsSummary.value = {
      totalVentas: resumen.total_transacciones,
      totalGastos: 0,
      unidadesVendidas: resumen.total_transacciones,
      cuentasPendientes: cuentas.resumen?.total_cuentas || 0,
    };

    // 5. Mapear Flujo de Caja para el Gráfico
    weeklyFlow.value = (agrupado.periodos || []).slice(-8).map((p) => ({
      semana: p.periodo,
      ventas: p.ingresos,
      gastos: p.costos,
    }));

    // 6. Mapear Cobros Prioritarios
    priorityCollections.value = (cuentas.results || []).map((c) => ({
      id: c.id,
      cliente: c.cliente_nombre || `Cliente #${c.cliente}`,
      detalle: `Factura ${c.factura}`,
      documento: c.factura,
      monto: parseFloat(c.monto),
      vencimientoTexto: c.vencida ? "Vencida" : `Vence ${c.fecha_vencimiento}`,
      estado: c.vencida ? "VENCIDA" : "PENDIENTE",
    }));

    // 7. Mapear Movimientos Recientes
    recentOperations.value = (ventas.results || []).map((v) => ({
      id: v.id,
      tipo: "VENTA",
      concepto: v.categoria || "Venta",
      detalle: v.producto_nombre,
      clienteProveedor:
        v.tipo_compra === "ONLINE" ? "En Línea" : "Tienda Física",
      canal: v.tipo_compra,
      fecha: v.fecha ? v.fecha.replace("T", " ").slice(0, 16) : "",
      estado: v.estado_pago,
      monto: parseFloat(v.total_venta),
    }));

    // 8. Mapear Productos
    topProducts.value = (productos.results || []).map((p) => ({
      id: p.no_parte,
      nombre: p.producto,
      unidadesVendidas: p.total_vendido || 0,
      totalVentas: parseFloat(p.precio_venta || 0),
    }));
  } catch (err) {
    console.error("Error cargando el dashboard:", err);
    error.value = "No se pudieron conectar los datos con el servidor backend.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  cargarDatosDashboard();
});
</script>
```

---

### 6. Paso 5: Cómo Probar la Conexión de Ambos Equipos en Local

1. **Terminal 1 (Backend Django):**

   ```powershell
   venv\Scripts\python.exe manage.py runserver
   # Escuchando en http://127.0.0.1:8000
   ```

2. **Terminal 2 (Frontend Vue 3):**

   ```powershell
   cd scratch_ux\ux\prototype\cajaclara-ui
   npm install
   npm run dev
   # Abriendo en http://localhost:5173
   ```

3. **Resultado:** Al abrir `http://localhost:5173`, el dashboard de Vue mostrará los datos reales cargados desde la base de datos de Django en tiempo real, sin depender de archivos mock estáticos.
