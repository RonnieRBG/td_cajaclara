# 📘 Documentación de Integración — Caja Clara

Guía para conectar las tres capas del proyecto (**Base de Datos → Backend Django → Frontend Vue 3**) de forma que cada equipo pueda trabajar y desplegar su parte de manera independiente.

---

## 🧭 Índice

0. [Visión general: cómo se conectan las piezas](#0-visión-general-cómo-se-conectan-las-piezas)
1. [Equipo de Base de Datos](#parte-1--equipo-de-base-de-datos)
2. [Equipo de Backend](#parte-2--equipo-de-backend)
3. [Contrato de la API (referencia para ambos equipos)](#parte-3--contrato-de-la-api)
4. [Equipo de Frontend](#parte-4--equipo-de-frontend)
5. [Punto de acoplamiento: qué campos dependen de quién](#parte-5--punto-de-acoplamiento)
6. [Prueba de integración en local](#parte-6--prueba-de-integración-en-local)
7. [Anexo: pendientes y correcciones a futuro](#anexo--pendientes-y-correcciones-a-futuro)

> **Convención de este documento**
>
> - 🟦 **BACKEND**
> - 🟩 **FRONTEND**
> - 🟨 **AMBOS**
> - ⚠️ **Pxx** =(#anexo--pendientes-y-correcciones-a-futuro).

---

## 0. Visión general: cómo se conectan las piezas

```
┌──────────────────────┐   fetch /api/...   ┌──────────────────────┐   ORM Django   ┌──────────────────┐
│  FRONTEND (Vue 3)    │ ─────────────────▶ │  BACKEND (Django/DRF)│ ─────────────▶ │  BASE DE DATOS   │
│  localhost:5173      │                    │  127.0.0.1:8000      │                │  SQLite / Postgres│
│                      │ ◀───────────────── │                      │ ◀───────────── │  / MySQL         │
│  services/api.js     │       JSON         │  /api/finanzas/...   │                │                  │
└──────────────────────┘                    └──────────────────────┘                └──────────────────┘
        ▲                                             ▲
        │ Proxy de Vite: /api → :8000                 │ Variables de entorno DB_*
```

**Idea clave:** el único punto de contacto entre frontend y backend es el **contrato de la API** (rutas, parámetros y nombres de campos JSON, Parte 3 y Parte 5). Mientras ese contrato no cambie, cada equipo puede modificar su código libremente.

| Equipo        | Lo que entrega                                         | Lo que necesita del otro equipo          |
| :------------ | :----------------------------------------------------- | :--------------------------------------- |
| Base de datos | Servidor de BD accesible + credenciales                | Nada (el backend crea las tablas)        |
| Backend       | Endpoints `/api/finanzas/...` que respetan el contrato | Credenciales de la BD (variables `DB_*`) |
| Frontend      | Dashboard que consume la API                           | Backend corriendo en el puerto 8000      |

---

## Parte 1 — Equipo de Base de Datos

El backend es **agnóstico al motor de base de datos**. No hay que tocar código Python para cambiar de motor: todo se controla con variables de entorno.

### 1.1 Variables de entorno

Si no se define ninguna, el backend usa SQLite (`db.sqlite3`) para desarrollo local.

| Variable      | Para qué sirve                            | Ejemplo PostgreSQL                        | Ejemplo MySQL              |
| :------------ | :---------------------------------------- | :---------------------------------------- | :------------------------- |
| `DB_ENGINE`   | Driver del motor                          | `django.db.backends.postgresql`           | `django.db.backends.mysql` |
| `DB_NAME`     | Nombre de la base de datos                | `cajaclara_db`                            | `cajaclara_db`             |
| `DB_USER`     | Usuario con permisos de lectura/escritura | `postgres`                                | `app_user`                 |
| `DB_PASSWORD` | Contraseña del usuario                    | `tu_password_segura`                      | `tu_password_segura`       |
| `DB_HOST`     | Host o IP del servidor                    | `localhost`, `10.x.x.x` o Cloud SQL Proxy | `127.0.0.1`                |
| `DB_PORT`     | Puerto                                    | `5432`                                    | `3306`                     |

Ejemplo en **PowerShell**:

```powershell
$env:DB_ENGINE="django.db.backends.postgresql"
$env:DB_NAME="cajaclara"
$env:DB_USER="postgres"
$env:DB_PASSWORD="secretpassword"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="5432"
```

> 💡 Según el motor, el backend necesita el driver de Python instalado en su entorno virtual: `psycopg2-binary` (PostgreSQL) o `mysqlclient` (MySQL). `requirements.txt`.

### 1.2 Crear las tablas (migraciones)

Con las variables ya definidas, ejecutar desde la carpeta del backend:

```bash
python manage.py migrate
```

Este comando crea todas las tablas, llaves foráneas e índices (por ejemplo, sobre `fecha` y `estado_pago`) a partir de los modelos de Django. **No hay que escribir SQL a mano.**

### 1.3 Cargar los datos iniciales

Para poblar la base con los 6 archivos CSV del supermercado:

```bash
python manage.py importar_csv
```

Para vaciar las tablas y volver a importar desde cero:

```bash
python manage.py importar_csv --limpiar
```

### ✅ Checklist del equipo de Base de Datos

- [ ] Servidor de BD creado y accesible desde la máquina donde corre Django.
- [ ] Usuario con permisos de lectura y escritura sobre la base `DB_NAME`.
- [ ] Variables `DB_*` entregadas al equipo de backend (por canal seguro, **nunca en el repositorio**).
- [ ] `migrate` ejecutado sin errores.
- [ ] `importar_csv` ejecutado y datos verificados (por ejemplo, que `facturas` tenga ~100.067 registros).

---

## Parte 2 — Equipo de Backend

Esta sección esta lista **las piezas del código Django de las que depende el acoplamiento**. Si alguna se modifica, puede romper al frontend o a la base de datos.

### 2.1 🟦 Configuración de base de datos (`settings.py`)

El bloque `DATABASES` debe leer las variables de entorno y usar SQLite como respaldo. La forma esperada es:

```python
import os

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}
```

**Regla:** no escribir credenciales directamente en este archivo.

### 2.2 🟦 CORS (`settings.py`)

Actualmente está abierto a cualquier origen para facilitar el desarrollo:

```python
INSTALLED_APPS = [
    # ...
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # debe ir lo más arriba posible
    # ...
]

CORS_ALLOW_ALL_ORIGINS = True  # ⚠️ P07: solo para desarrollo
```

> Con el proxy de Vite (Parte 4.2), el navegador cree que le habla al mismo origen, así que en desarrollo CORS ni siquiera entra en juego. Sí importa si el frontend se despliega en otro dominio.

### 2.3 🟦 Paginación (`settings.py` o clase propia)

El frontend asume este comportamiento en **todos** los listados:

- Tamaño por defecto: **50**.
- Se puede cambiar con `?page_size=N`, con un **máximo de 500**.
- Respuesta con las claves `count`, `next`, `previous` y `results`.

Configuración equivalente en DRF:

```python
from rest_framework.pagination import PageNumberPagination

class PaginacionEstandar(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500
```

### 2.4 🟦 Formatos de fecha aceptados

Todos los parámetros `fecha_inicio` y `fecha_fin` deben aceptar **los dos formatos**:

- `DD/MM/AAAA` (formato chileno, por ejemplo `31/12/2012`)
- `AAAA-MM-DD` (ISO, por ejemplo `2012-12-31`)

El frontend envía el formato `DD/MM/AAAA` porque usa `min_display` y `max_display` de `opciones-filtros`.

### 2.5 🟦 Serializers: el verdadero contrato

**Los nombres de campo que devuelven los serializers son lo que el frontend lee.** Renombrar un campo (por ejemplo, `cliente_nombre` → `nombre_cliente`) rompe el dashboard sin dar error en el backend.

La lista exacta de campos que el frontend consume está en la [Parte 5](#parte-5--punto-de-acoplamiento). Antes de cambiar un serializer, revisar esa tabla.

### ✅ Checklist del equipo de Backend

- [ ] `DATABASES` lee las variables `DB_*` (2.1).
- [ ] Driver de la BD de producción incluido en `requirements.txt`.
- [ ] `corsheaders` instalado y configurado (2.2).
- [ ] Paginación con `page_size` configurable y máximo de 500 (2.3).
- [ ] Filtros de fecha aceptan `DD/MM/AAAA` y `AAAA-MM-DD` (2.4).
- [ ] Todos los campos marcados como 🟦 en la [Parte 5](#parte-5--punto-de-acoplamiento) existen en las respuestas (⚠️ ver P02 y P03).
- [ ] Servidor corriendo en `127.0.0.1:8000`.

---

## Parte 3 — Contrato de la API

Referencia común para **ambos equipos**. Todas las rutas cuelgan de:

- **URL base en desarrollo:** `http://localhost:8000`
- **Prefijo:** `/api/finanzas/`

### Resumen de endpoints

| #   | Método y ruta              | Para qué sirve                         | Paginado | Lo usa el dashboard |
| :-- | :------------------------- | :------------------------------------- | :------: | :-----------------: |
| 1   | `GET /opciones-filtros/`   | Valores para selects y rango de fechas |    No    |         ✅          |
| 2   | `GET /resumen-mensual/`    | KPIs financieros de un rango de fechas |    No    |         ✅          |
| 3   | `GET /resumen-agrupado/`   | Serie temporal para gráficos           |    No    |         ✅          |
| 4   | `GET /exportar-excel/`     | Descarga de archivo `.xlsx`            |    No    |   (botón export)    |
| 5   | `GET /clientes/`           | Listado de clientes                    |    Sí    |          —          |
| 6   | `GET /productos/`          | Listado de productos                   |    Sí    |         ✅          |
| 7   | `GET /facturas/`           | Listado de facturas (ventas)           |    Sí    |          —          |
| 8   | `GET /ventas/`             | Líneas de venta detalladas             |    Sí    |         ✅          |
| 9   | `GET /cuentas-por-cobrar/` | Deuda de clientes + resumen global     |    Sí    |         ✅          |
| 10  | `GET /gastos/`             | Gastos de insumo + resumen global      |    Sí    |          —          |

### Estructura de los listados paginados

```json
{
  "count": 100067,
  "next": "http://localhost:8000/api/finanzas/facturas/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

Los endpoints 9 y 10 agregan además una clave `resumen` con totales globales, que **no depende de la página**.

---

### 1. Opciones de filtros

`GET /api/finanzas/opciones-filtros/`

Devuelve los valores para inicializar los `<select>` y los selectores de fecha. **El frontend lo llama primero** para saber qué rango de fechas pedir.

```json
{
  "categorias": ["Abarrotes", "Carnes", "Lácteos", "Limpieza"],
  "unidades_negocio": ["Supermercado"],
  "tipos_compra": [
    { "codigo": "FISICA", "nombre": "Física" },
    { "codigo": "ONLINE", "nombre": "En línea" }
  ],
  "estados_pago": [
    { "codigo": "PAGADO", "nombre": "Pagado" },
    { "codigo": "PENDIENTE", "nombre": "Pendiente" },
    { "codigo": "ANULADO", "nombre": "Anulado" }
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

### 2. Resumen de KPIs financieros

`GET /api/finanzas/resumen-mensual/` ⚠️ P06

| Parámetro      | Obligatorio | Valores                              |
| :------------- | :---------: | :----------------------------------- |
| `fecha_inicio` |     No      | `01/01/2010` o `2010-01-01`          |
| `fecha_fin`    |     No      | `31/12/2012` o `2012-12-31`          |
| `tipo_compra`  |     No      | `FISICA` u `ONLINE` (omitir = todos) |

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

### 3. Serie temporal para gráficos

`GET /api/finanzas/resumen-agrupado/`

| Parámetro                                  | Obligatorio | Valores                                                         |
| :----------------------------------------- | :---------: | :-------------------------------------------------------------- |
| `agrupacion`                               |     No      | `diaria`, `mensual` (por defecto), `trimestral`, `anual` ⚠️ P01 |
| `fecha_inicio`, `fecha_fin`, `tipo_compra` |     No      | Igual que el endpoint 2                                         |

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

### 4. Exportación a Excel

`GET /api/finanzas/exportar-excel/`

- **Parámetros:** los mismos del endpoint 2.
- **Respuesta:** archivo binario `.xlsx` con encabezados formateados y celdas con formato contable.
- **En el frontend:** no se usa `fetch`; se abre la URL directamente (por ejemplo, con `window.location.href` o un `<a href>`), y el navegador descarga el archivo.

---

### 5. Clientes

`GET /api/finanzas/clientes/`

| Parámetro           | Valores                                |
| :------------------ | :------------------------------------- |
| `search`            | Texto: busca por nombre, ID o teléfono |
| `page`, `page_size` | Paginación                             |

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

> ℹ️ Los montos en los listados vienen como **texto** (`"125000.00"`), no como número. El frontend debe convertirlos con `parseFloat()`.

---

### 6. Productos

`GET /api/finanzas/productos/` ⚠️ P03

| Parámetro           | Valores                              |
| :------------------ | :----------------------------------- |
| `search`            | Busca por nombre o código `no_parte` |
| `categoria`         | Por ejemplo, `Abarrotes`, `Lácteos`  |
| `unidad_negocio`    | Por ejemplo, `Supermercado`          |
| `page`, `page_size` | Paginación                           |

> 🟦 **Falta documentar la respuesta de ejemplo.** El frontend espera al menos `no_parte`, `producto`, `total_vendido` y `precio_venta`.

---

### 7. Facturas (ventas)

`GET /api/finanzas/facturas/`

| Parámetro                   | Valores             |
| :-------------------------- | :------------------ |
| `cliente`                   | ID del cliente      |
| `tipo_compra`               | `FISICA` u `ONLINE` |
| `por_cobrar`                | `true` o `false`    |
| `fecha_inicio`, `fecha_fin` | Rango de fechas     |
| `page`, `page_size`         | Paginación          |

```json
{
  "count": 100067,
  "next": "http://localhost:8000/api/finanzas/facturas/?page=2",
  "previous": null,
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

### 8. Líneas de venta detalladas

`GET /api/finanzas/ventas/` ⚠️ P02

| Parámetro           | Valores                |
| :------------------ | :--------------------- |
| `factura`           | ID de factura          |
| `producto`          | N° de parte            |
| `estado_pago`       | `PAGADO` o `PENDIENTE` |
| `page`, `page_size` | Paginación             |

> 🟦 **Falta documentar la respuesta de ejemplo.** El frontend espera al menos `id`, `categoria`, `producto_nombre`, `tipo_compra`, `fecha`, `estado_pago` y `total_venta`.

---

### 9. Cuentas por cobrar

`GET /api/finanzas/cuentas-por-cobrar/`

| Parámetro           | Valores                                                           |
| :------------------ | :---------------------------------------------------------------- |
| `cliente`           | ID de cliente                                                     |
| `vencidas`          | `true` = solo vencidas · `false` = solo vigentes · omitir = todas |
| `page`, `page_size` | Paginación                                                        |

```json
{
  "count": 14928,
  "next": "http://localhost:8000/api/finanzas/cuentas-por-cobrar/?page=2",
  "previous": null,
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

### 10. Gastos de insumo

`GET /api/finanzas/gastos/`

| Parámetro                   | Valores               |
| :-------------------------- | :-------------------- |
| `producto`                  | N° de parte           |
| `categoria`                 | Categoría de producto |
| `fecha_inicio`, `fecha_fin` | Rango de fechas       |
| `page`, `page_size`         | Paginación            |

```json
{
  "count": 20000,
  "next": "...",
  "previous": null,
  "resumen": {
    "total_registros_gasto": 20000,
    "monto_total_gastos": 24484481.0
  },
  "results": [ ... ]
}
```

---

## Parte 4 — Equipo de Frontend

Todos los cambios se hacen dentro de la aplicación Vue ubicada en la rama `ux`:

```
ux/prototype/cajaclara-ui/
├── vite.config.js                    ← Paso 1: MODIFICAR (agregar proxy)
└── src/
    ├── services/
    │   └── api.js                    ← Paso 2: CREAR (archivo nuevo)
    ├── views/
    │   └── DashboardView.vue         ← Pasos 3 y 4: MODIFICAR (script y template)
    ├── data/
    │   └── dashboardMock.js          ← Deja de usarse (no borrar hasta validar)
    └── components/                   ← NO se modifican (siguen recibiendo props)
```

### 4.1 Situación actual

Hoy `DashboardView.vue` importa datos falsos de forma estática y los pasa como props:

| Componente                | Recibe hoy                     |
| :------------------------ | :----------------------------- |
| `StatCard.vue`            | `mockData.kpis`                |
| `OperationsSummary.vue`   | `mockData.operationsSummary`   |
| `CashChart.vue`           | `mockData.weeklyFlow`          |
| `PriorityCollections.vue` | `mockData.priorityCollections` |
| `RecentOperations.vue`    | `mockData.recentOperations`    |
| `TopProducts.vue`         | `mockData.topProducts`         |

**Estrategia:** se reemplaza `mockData` por variables reactivas **con la misma forma** que el mock. Así, los componentes hijos no necesitan ningún cambio.

### 4.2 🟩 Paso 1 — Proxy en Vite (`vite.config.js`)

**Qué hace:** toda petición del frontend que empiece con `/api` se reenvía a Django (`127.0.0.1:8000`). El código usa rutas relativas (`/api/finanzas/...`) y no hay que escribir la URL del backend en ningún componente.

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
    // ▼▼▼ BLOQUE NUEVO ▼▼▼
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
      },
    },
    // ▲▲▲ FIN BLOQUE NUEVO ▲▲▲
  },
});
```

> ⚠️ El proxy **solo funciona con `npm run dev`**. En un build de producción hay que resolver la URL del backend de otra forma (variable `VITE_API_URL` o servidor web que haga el reenvío).

### 4.3 🟩 Paso 2 — Servicio de API (`src/services/api.js`, archivo nuevo)

**Qué hace:** centraliza todas las llamadas al backend. Si una ruta cambia, se corrige solo aquí.

- `request()` arma la URL agregando solo los parámetros que tienen valor, hace el `fetch` y lanza un error legible si la respuesta no es 2xx.
- `apiService` expone un método por cada endpoint que usa el dashboard.

```javascript
/**
 * Servicio de conexión con la API de Django (Caja Clara)
 */

const API_BASE = "/api/finanzas";

async function request(endpoint, params = {}) {
  const url = new URL(endpoint, window.location.origin);

  // Solo se agregan los parámetros con valor (se ignoran undefined, null y "")
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
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `Error HTTP: ${res.status}`);
  }

  return res.json();
}

export const apiService = {
  // Endpoint 1 — Opciones para selects y rango de fechas
  getOpcionesFiltros() {
    return request(`${API_BASE}/opciones-filtros/`);
  },

  // Endpoint 2 — KPIs (saldo, ventas, gastos, pendiente)
  getResumenFinanciero(filtros = {}) {
    return request(`${API_BASE}/resumen-mensual/`, filtros);
  },

  // Endpoint 3 — Serie temporal para el gráfico
  getResumenAgrupado(agrupacion = "mensual", filtros = {}) {
    return request(`${API_BASE}/resumen-agrupado/`, { agrupacion, ...filtros });
  },

  // Endpoint 9 — Cobros que requieren atención
  getCuentasPorCobrar(filtros = {}) {
    return request(`${API_BASE}/cuentas-por-cobrar/`, {
      page_size: 5,
      ...filtros,
    });
  },

  // Endpoint 8 — Últimos movimientos
  getUltimosMovimientos(filtros = {}) {
    return request(`${API_BASE}/ventas/`, { page_size: 10, ...filtros });
  },

  // Endpoint 6 — Productos
  getProductos(filtros = {}) {
    return request(`${API_BASE}/productos/`, { page_size: 4, ...filtros });
  },

  // Endpoint 4 — URL de descarga del Excel (no hace fetch, devuelve la URL)
  getUrlExportarExcel(filtros = {}) {
    const url = new URL(`${API_BASE}/exportar-excel/`, window.location.origin);
    Object.keys(filtros).forEach((key) => {
      if (filtros[key]) url.searchParams.append(key, filtros[key]);
    });
    return url.toString();
  },
};
```

### 4.4 🟩 Paso 3 — Lógica del dashboard (`<script setup>` de `DashboardView.vue`)

**Qué cambia:**

1. Se **elimina** `import mockData from "@/data/dashboardMock"`.
2. Se crean variables `ref()` con la misma forma que tenía el mock.
3. Al montar el componente (`onMounted`) se cargan los datos:
   - **Primero** `opciones-filtros`, para conocer el rango de fechas.
   - **Después**, en paralelo con `Promise.all`, los otros 5 endpoints.
4. Cada respuesta se transforma ("mapea") al formato que esperan los componentes.

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

// ── Estado de la pantalla ────────────────────────────────
const loading = ref(true);
const error = ref(null);

// ── Datos (misma forma que tenía mockData) ───────────────
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

// ── Carga desde el backend ───────────────────────────────
const cargarDatosDashboard = async () => {
  loading.value = true;
  error.value = null;

  try {
    // 1. Rango de fechas disponible en la BD
    const opciones = await apiService.getOpcionesFiltros();
    const filtroRango = {
      fecha_inicio: opciones.rango_fechas_disponible.min_display,
      fecha_fin: opciones.rango_fechas_disponible.max_display,
    };

    // 2. Resto de peticiones en paralelo
    const [resumen, agrupado, cuentas, ventas, productos] = await Promise.all([
      apiService.getResumenFinanciero(filtroRango),
      apiService.getResumenAgrupado("mensual", filtroRango), // ⚠️ P01
      apiService.getCuentasPorCobrar({ vencidas: "true", page_size: 5 }),
      apiService.getUltimosMovimientos({ page_size: 5 }),
      apiService.getProductos({ page_size: 4 }),
    ]);

    // 3. KPIs
    kpis.value = {
      saldoPeriodo: resumen.flujo_caja_neto,
      ventasMes: resumen.total_ingresos, // ⚠️ P06
      comprasGastos: resumen.total_costos,
      pendienteCobrar: resumen.por_estado_pago?.PENDIENTE?.ingresos || 0,
    };

    // 4. Resumen de operaciones
    operationsSummary.value = {
      totalVentas: resumen.total_transacciones,
      totalGastos: 0, // ⚠️ P05
      unidadesVendidas: resumen.total_transacciones, // ⚠️ P04
      cuentasPendientes: cuentas.resumen?.total_cuentas || 0,
    };

    // 5. Gráfico de flujo de caja (últimos 8 periodos)
    weeklyFlow.value = (agrupado.periodos || []).slice(-8).map((p) => ({
      semana: p.periodo,
      ventas: p.ingresos,
      gastos: p.costos,
    }));

    // 6. Cobros prioritarios
    priorityCollections.value = (cuentas.results || []).map((c) => ({
      id: c.id,
      cliente: c.cliente_nombre || `Cliente #${c.cliente}`,
      detalle: `Factura ${c.factura}`,
      documento: c.factura,
      monto: parseFloat(c.monto),
      vencimientoTexto: c.vencida ? "Vencida" : `Vence ${c.fecha_vencimiento}`,
      estado: c.vencida ? "VENCIDA" : "PENDIENTE",
    }));

    // 7. Movimientos recientes ⚠️ P02
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

    // 8. Productos ⚠️ P03
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

onMounted(cargarDatosDashboard);
</script>
```

### 4.5 🟩 Paso 4 — Ajustar el `<template>` de `DashboardView.vue`

Como `mockData` ya no existe, hay que reemplazar cada referencia en el template:

| Buscar en el template          | Reemplazar por        |
| :----------------------------- | :-------------------- |
| `mockData.kpis`                | `kpis`                |
| `mockData.operationsSummary`   | `operationsSummary`   |
| `mockData.weeklyFlow`          | `weeklyFlow`          |
| `mockData.priorityCollections` | `priorityCollections` |
| `mockData.recentOperations`    | `recentOperations`    |
| `mockData.topProducts`         | `topProducts`         |

> En el template **no** se escribe `.value`: Vue desenvuelve los `ref` automáticamente.

Además, conviene mostrar los estados de carga y error para que la pantalla no aparezca en cero mientras llegan los datos:

```vue
<template>
  <div v-if="loading" class="dashboard-estado">Cargando datos…</div>

  <div v-else-if="error" class="dashboard-estado dashboard-error">
    {{ error }}
    <button @click="cargarDatosDashboard">Reintentar</button>
  </div>

  <div v-else>
    <!-- contenido actual del dashboard, con las referencias ya reemplazadas -->
  </div>
</template>
```

### ✅ Checklist del equipo de Frontend

- [ ] Proxy agregado en `vite.config.js` (4.2).
- [ ] Archivo `src/services/api.js` creado (4.3).
- [ ] `DashboardView.vue` ya no importa `dashboardMock` (4.4).
- [ ] Todas las referencias `mockData.*` del template reemplazadas (4.5).
- [ ] Estados de carga y error visibles en pantalla (4.5).
- [ ] Componentes hijos **sin cambios**.
- [ ] Ver en DevTools → Network que las llamadas a `/api/...` responden 200.

---

## Parte 5 — Punto de acoplamiento

Esta tabla es **el contrato entre ambos equipos** 🟨. Cada fila dice qué campo del JSON lee el frontend y qué prop alimenta.

- Si el **backend** renombra o elimina uno de estos campos, el dashboard se rompe.
- Si el **frontend** necesita un campo nuevo, debe pedirlo al backend y agregarlo aquí.

| Componente (prop)                        | Campo que lee el frontend                                                                  | Endpoint                           | Estado                 |
| :--------------------------------------- | :----------------------------------------------------------------------------------------- | :--------------------------------- | :--------------------- |
| StatCard · `saldoPeriodo`                | `flujo_caja_neto`                                                                          | `resumen-mensual`                  | ✅ Documentado         |
| StatCard · `ventasMes`                   | `total_ingresos`                                                                           | `resumen-mensual`                  | ✅ ⚠️ P06              |
| StatCard · `comprasGastos`               | `total_costos`                                                                             | `resumen-mensual`                  | ✅ Documentado         |
| StatCard · `pendienteCobrar`             | `por_estado_pago.PENDIENTE.ingresos`                                                       | `resumen-mensual`                  | ✅ Documentado         |
| OperationsSummary · `totalVentas`        | `total_transacciones`                                                                      | `resumen-mensual`                  | ✅ Documentado         |
| OperationsSummary · `totalGastos`        | — (fijo en 0)                                                                              | —                                  | ⚠️ P05                 |
| OperationsSummary · `unidadesVendidas`   | `total_transacciones`                                                                      | `resumen-mensual`                  | ⚠️ P04                 |
| OperationsSummary · `cuentasPendientes`  | `resumen.total_cuentas`                                                                    | `cuentas-por-cobrar`               | ✅ Documentado         |
| CashChart · `semana`, `ventas`, `gastos` | `periodos[].periodo`, `.ingresos`, `.costos`                                               | `resumen-agrupado`                 | ✅ ⚠️ P01              |
| PriorityCollections                      | `id`, `cliente`, `cliente_nombre`, `factura`, `monto`, `fecha_vencimiento`, `vencida`      | `cuentas-por-cobrar?vencidas=true` | ✅ Documentado         |
| RecentOperations                         | `id`, `categoria`, `producto_nombre`, `tipo_compra`, `fecha`, `estado_pago`, `total_venta` | `ventas`                           | ❓ Sin confirmar · P02 |
| TopProducts                              | `no_parte`, `producto`, `total_vendido`, `precio_venta`                                    | `productos`                        | ❓ Sin confirmar · P03 |

---

## Parte 6 — Prueba de integración en local

Se necesitan **dos terminales abiertas al mismo tiempo**.

**Terminal 1 — Backend (Django):**

```powershell
# Desde la carpeta raíz del backend
venv\Scripts\python.exe manage.py runserver
# Debe quedar escuchando en http://127.0.0.1:8000
```

Prueba rápida: abrir `http://127.0.0.1:8000/api/finanzas/opciones-filtros/` en el navegador. Si se ve el JSON, el backend está bien.

**Terminal 2 — Frontend (Vue 3):**

```powershell
cd ux\prototype\cajaclara-ui   # ⚠️ P08: verificar la ruta real en tu equipo
npm install
npm run dev
# Abre en http://localhost:5173
```

**Resultado esperado:** al abrir `http://localhost:5173`, el dashboard muestra datos reales de la base de datos, sin depender de `dashboardMock.js`.

### Si algo falla

| Síntoma                                      | Causa probable                                   | Qué revisar                                |
| :------------------------------------------- | :----------------------------------------------- | :----------------------------------------- |
| Mensaje "No se pudieron conectar los datos…" | Django no está corriendo o el proxy no se aplicó | Terminal 1 activa; reiniciar `npm run dev` |
| Error 404 en `/api/...`                      | Ruta mal escrita o URL no registrada en Django   | `urls.py` del backend y `API_BASE`         |
| Error 500                                    | Excepción en el backend                          | Consola de la Terminal 1                   |
| Tarjetas en `NaN` o vacías                   | El campo no existe en el JSON (nombre distinto)  | Parte 5 + DevTools → Network → Response    |
| Carga muy lenta                              | Consultas pesadas sobre ~100k registros          | Índices en la BD y consultas del backend   |

---

## Anexo — Pendientes y correcciones a futuro

Problemas detectados al revisar este documento. No bloquean la primera integración, pero conviene resolverlos.

**Prioridad:** 🔴 Alta (puede romper o mostrar datos incorrectos) · 🟠 Media (dato engañoso) · 🟢 Baja (documentación o detalle)

| ID  | Prioridad | Problema                                                                                                                                                                                                                                        | Dónde                           | Responsable | Propuesta                                                                                                              |
| :-- | :-------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------ | :---------- | :--------------------------------------------------------------------------------------------------------------------- |
| P01 |    🟠     | La versión anterior de la tabla de mapeo pedía `agrupacion=semanal`, pero el endpoint solo acepta `diaria`, `mensual`, `trimestral` y `anual`. El código usa `mensual`, mientras que el componente y su prop se llaman `weeklyFlow` / `semana`. | `resumen-agrupado`, `CashChart` | 🟨 Ambos    | Decidir: (a) el backend agrega `semanal`, o (b) el frontend renombra `weeklyFlow` → `cashFlow` y `semana` → `periodo`. |

| P02 | 🔴 | El endpoint `/ventas/` no tiene respuesta de ejemplo documentada. El frontend usa `id`, `categoria`, `producto_nombre`, `tipo_compra`, `fecha`, `estado_pago` y `total_venta` sin confirmar que existan. | `VentaSerializer`, `RecentOperations` | 🟦 Backend | Revisar el serializer, agregar los campos que falten y documentar un JSON de ejemplo en la Parte 3. |

| P03 | 🔴 | El endpoint `/productos/` no tiene respuesta de ejemplo. El frontend usa `no_parte`, `producto`, `total_vendido` y `precio_venta`. `total_vendido` probablemente requiere una agregación (`Sum`) que podría no existir. Además, "TopProducts" implica productos más vendidos, pero no se pide ningún orden. | `ProductoSerializer`, `TopProducts` | 🟦 Backend | Agregar `total_vendido` con `annotate`, permitir `?ordering=-total_vendido` y documentar la respuesta. |

| P04 | 🔴 | `unidadesVendidas` se llena con `total_transacciones`. Una transacción no equivale a una unidad, así que el dato mostrado es incorrecto. | `DashboardView.vue` (paso 4 del script) | 🟨 Ambos | El backend agrega `total_unidades` en `resumen-mensual`; el frontend lo usa. |

| P05 | 🟠 | `totalGastos` está fijo en `0`. | `DashboardView.vue` (paso 4 del script) | 🟩 Frontend | Usar `resumen.total_costos` o `gastos.resumen.monto_total_gastos`, según lo que defina el equipo. |

| P06 | 🟠 | El endpoint se llama `resumen-mensual`, pero acepta cualquier rango. El dashboard lo llama con todo el histórico (2010–2022), así que el KPI `ventasMes` muestra 12 años de ventas, no un mes. | Nombre del endpoint, KPI `ventasMes` | 🟨 Ambos | Renombrar a `resumen-financiero` (manteniendo el alias antiguo por un tiempo) y que el dashboard pida el último mes disponible, o cambiar la etiqueta del KPI. |

| P07 | 🟠 | `CORS_ALLOW_ALL_ORIGINS = True` permite que cualquier sitio consuma la API. | `settings.py` | 🟦 Backend | En producción, usar `CORS_ALLOWED_ORIGINS` con la lista de dominios permitidos, controlado por variable de entorno. |

| P08 | 🟢 | La guía de prueba usaba la ruta `scratch_ux\ux\prototype\cajaclara-ui`, mientras que el resto del documento usa `ux/prototype/cajaclara-ui`. | Parte 6 | Documentación | Confirmar la ruta real en el repositorio y unificarla. |

| P09 | 🟢 | El ejemplo original de `cuentas-por-cobrar` omitía `next` y `previous`. Se agregaron en esta versión asumiendo la paginación estándar. | Parte 3, endpoint 9 | 🟦 Backend | Verificar con una llamada real que la respuesta incluya ambas claves. |

| P10 | 🟢 | `vencimientoTexto` muestra la fecha en formato ISO (`Vence 2010-02-19`), distinto del formato chileno usado en el resto de la app. | `DashboardView.vue` (paso 6 del script) | 🟩 Frontend | Formatear con `toLocaleDateString("es-CL")`. |

| P11 | 🟢 | El proxy de Vite solo existe en desarrollo. No hay definido cómo encuentra el frontend al backend en producción. | `vite.config.js`, `api.js` | 🟨 Ambos | Usar una variable `VITE_API_URL` en `API_BASE`, o servir ambos detrás del mismo dominio. |
