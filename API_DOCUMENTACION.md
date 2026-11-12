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

La forma más simple de definirlas es copiar **`.env.example`** como **`.env`** (en la carpeta de `manage.py`) y completar los valores: el backend lo lee al arrancar. El archivo `.env` está en el `.gitignore`, así que las claves nunca se suben al repositorio.

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

Este comando crea todas las tablas, llaves foráneas e índices (por ejemplo, sobre la `fecha` de las facturas y el `estado` de las cuentas por cobrar) a partir de los modelos de Django. **No hay que escribir SQL a mano.**

### 1.3 Cargar los datos iniciales

Para poblar la base con los 6 archivos CSV del supermercado:

```bash
python manage.py importar_csv
```

Para vaciar las tablas y volver a importar desde cero:

```bash
python manage.py importar_csv --limpiar
```

Por defecto las fechas se desplazan un número exacto de semanas para que la última venta quede en la semana actual (cada venta conserva su día de la semana y los plazos de cobro no cambian). Para importar las fechas originales de los CSV (2010-2022):

```bash
python manage.py importar_csv --limpiar --fechas-originales
```

> Si ya tenías la base cargada antes del cambio a la hora de Chile, vuelve a importar con `--limpiar`.

El comando busca los CSV en `data/`. Si esa carpeta no existe, usa la de la Etapa 3 de la rama `datos` (`datos/Etapas_1-2-3/Etapa_3 Elaboracion de tablas/`). También se puede indicar otra:

```bash
python manage.py importar_csv --limpiar --carpeta "ruta/a/los/csv"
```

> **Después de actualizar el código, ejecuta `python manage.py migrate`.** La migración `0003_ordenar_modelo` reorganiza las tablas sin perder datos, pero se recomienda reimportar con `--limpiar` para partir de cero.

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

Solo los sitios listados en la variable `CORS_ALLOWED_ORIGINS` pueden llamar a la API desde el navegador. Por defecto se permite el servidor de Vite (`http://localhost:5173` y `http://127.0.0.1:5173`):

```python
CORS_ALLOWED_ORIGINS = _lista(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
```

Al publicar el frontend en otro dominio, se agrega ese dominio en el `.env` (por ejemplo `CORS_ALLOWED_ORIGINS=https://cajaclara.ejemplo.cl`).

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

### 2.6 🟦 Seguridad y login (`settings.py`)

- **Toda la API exige login** (`IsAuthenticated` por defecto). Solo `/api/` (el catálogo) y las rutas de `/api/auth/` son públicas.
- **Clave secreta, modo depuración y dominios** se leen del `.env`: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y `DJANGO_ALLOWED_HOSTS`. Con `DJANGO_DEBUG=False` el backend no arranca si falta la clave.
- **Duración de los tokens:** `JWT_ACCESS_MINUTOS` (30 por defecto) y `JWT_REFRESH_DIAS` (7 por defecto).
- **Intentos de login:** máximo `LOGIN_RATE` (10 por minuto por defecto); después responde `429`.
- **Usuarios:** como hay un solo negocio, no hay registro público. Los crea un administrador con `python manage.py createsuperuser` o desde `/admin/` → *Usuarios*.

### ✅ Checklist del equipo de Backend

- [ ] `DATABASES` lee las variables `DB_*` (2.1).
- [ ] Driver de la BD de producción incluido en `requirements.txt`.
- [ ] `corsheaders` instalado y configurado (2.2).
- [ ] Paginación con `page_size` configurable y máximo de 500 (2.3).
- [ ] Filtros de fecha aceptan `DD/MM/AAAA` y `AAAA-MM-DD` (2.4).
- [ ] Todos los campos marcados como 🟦 en la [Parte 5](#parte-5--punto-de-acoplamiento) existen en las respuestas (⚠️ ver P02 y P03).
- [ ] Servidor corriendo en `127.0.0.1:8000`.
- [ ] Archivo `.env` creado a partir de `.env.example` (en producción: `DJANGO_DEBUG=False` y `DJANGO_SECRET_KEY` propia).
- [ ] Al menos un usuario creado (`python manage.py createsuperuser`).
- [ ] `python manage.py test` sin errores.

---

## Parte 3 — Contrato de la API

Referencia común para **ambos equipos**. Todas las rutas cuelgan de:

- **URL base en desarrollo:** `http://localhost:8000`
- **Prefijo:** `/api/finanzas/`

### 🔐 Autenticación (JWT)

**Todas las rutas de `/api/finanzas/` exigen iniciar sesión.** Sin token responden `401`.

| Método y ruta            | Para qué sirve                                  | Cuerpo (JSON)              |
| :----------------------- | :---------------------------------------------- | :------------------------- |
| `POST /api/auth/login/`   | Iniciar sesión                                  | `username`, `password`     |
| `POST /api/auth/refresh/` | Obtener un `access` nuevo cuando el actual vence | `refresh`                  |
| `POST /api/auth/logout/`  | Cerrar sesión (invalida el `refresh`)           | `refresh`                  |
| `GET /api/auth/perfil/`   | Datos del usuario que inició sesión             | —                          |

**Login:**

```json
// POST /api/auth/login/
{ "username": "admin", "password": "••••••••" }

// Respuesta 200
{
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "usuario": {
    "id": 1,
    "username": "admin",
    "nombre": "Ana Pérez",
    "email": "admin@cajaclara.cl",
    "es_admin": true
  }
}
```

**Cómo se usa el token:** en cada consulta se envía el encabezado

```
Authorization: Bearer <access>
```

**Cuánto duran:** el `access` dura **30 minutos** y el `refresh` **7 días**. Cuando una consulta responde `401`, el frontend llama a `/api/auth/refresh/` con el `refresh`; recibe un `access` **y un `refresh` nuevos** (el anterior deja de servir) y repite la consulta. Si el refresh también falla, se vuelve a la pantalla de login.

| Respuesta | Cuándo                                                  |
| :-------: | :------------------------------------------------------ |
|   `401`   | Sin token, token vencido o inválido, o clave incorrecta (`"Usuario o contraseña incorrectos."`) |
|   `429`   | Demasiados intentos de login seguidos (10 por minuto)   |

> No hay registro público de usuarios: los crea un administrador (ver 2.6).

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
| 10  | `GET /gastos/`             | Gastos (compras y otros) + resumen     |    Sí    |          —          |

**Registrar datos** (detalle en el endpoint 11):

| Método y ruta                                  | Para qué sirve                                   |
| :--------------------------------------------- | :----------------------------------------------- |
| `POST /facturas/`                              | Registrar una venta (al contado o a crédito)     |
| `GET /facturas/{factura}/`                     | Ver una venta con sus productos y su deuda       |
| `POST /facturas/{factura}/anular/`             | Anular una venta                                 |
| `POST /cuentas-por-cobrar/{id}/pagar/`         | Registrar el pago de una deuda                   |
| `POST /cuentas-por-cobrar/{id}/revertir-pago/` | Deshacer un pago registrado por error            |
| `POST /gastos/`                                | Registrar una compra u otro gasto                |
| `POST /clientes/`                              | Registrar un cliente                             |

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
    "fecha_inicio": "01/01/2026",
    "fecha_fin": "30/06/2026",
    "periodo_tipo": "personalizado"
  },
  "filtro_tipo_compra": "TODOS",
  "total_transacciones": 176,
  "total_unidades": 654,
  "total_ingresos": 445662.0,
  "total_costos": 325328.0,
  "utilidad_bruta": 120334.0,
  "flujo_caja_neto": 120334.0,
  "margen_porcentaje": 27.0,
  "por_estado_pago": {
    "PAGADO": {
      "nombre": "Pagado",
      "transacciones": 149,
      "ingresos": 373181.0
    },
    "PENDIENTE": {
      "nombre": "Pendiente",
      "transacciones": 27,
      "ingresos": 72481.0
    },
    "ANULADO": {
      "nombre": "Anulado",
      "transacciones": 0,
      "ingresos": 0.0
    }
  },
  "flujo_caja": {
    "entradas": {
      "ventas_contado": 373181.0,
      "cobros": 0.0,
      "total": 373181.0
    },
    "salidas": {
      "compras": 984629.0,
      "otros_gastos": 0.0,
      "total": 984629.0
    },
    "saldo": -611448.0
  }
}
```

| Campo                 | Significado                                                                                                              |
| :-------------------- | :----------------------------------------------------------------------------------------------------------------------- |
| `total_ingresos`      | Todo lo **vendido** en el período (al contado y a crédito), sin anuladas.                                                |
| `total_costos`        | Costo de la mercadería vendida.                                                                                          |
| `utilidad_bruta`      | `total_ingresos - total_costos`.                                                                                         |
| `flujo_caja_neto`     | ⚠️ Se mantiene por compatibilidad, pero es **igual a `utilidad_bruta`**, no al dinero en caja. Usar `flujo_caja.saldo`.  |
| `total_unidades`      | Unidades vendidas (suma de cantidades).                                                                                  |
| `flujo_caja.entradas` | Dinero que **entró**: ventas al contado del período (`ventas_contado`) + deudas **cobradas** en el período (`cobros`).   |
| `flujo_caja.salidas`  | Dinero que **salió**: `compras` de mercadería + `otros_gastos` (arriendo, flete, servicios…).                            |
| `flujo_caja.saldo`    | `entradas.total - salidas.total`. Es el "Saldo del periodo" del dashboard.                                               |

> Una venta a crédito suma en `total_ingresos` el día que se vende, pero entra a `flujo_caja` el día que se **paga**. El filtro `tipo_compra` afecta las entradas; los gastos no tienen canal y siempre se cuentan completos.


---

### 3. Serie temporal para gráficos

`GET /api/finanzas/resumen-agrupado/`

| Parámetro                                  | Obligatorio | Valores                                                         |
| :----------------------------------------- | :---------: | :-------------------------------------------------------------- |
| `agrupacion`                               |     No      | `diaria`, `semanal` (lunes a domingo), `semanas_mes` (1-7, 8-14, 15-21, 22-fin de mes, como el gráfico del diseño), `mensual` (por defecto), `trimestral`, `anual` |
| `fecha_inicio`, `fecha_fin`, `tipo_compra` |     No      | Igual que el endpoint 2                                         |

```json
{
  "rango_aplicado": {
    "fecha_inicio": "01/05/2026",
    "fecha_fin": "30/06/2026"
  },
  "agrupacion": "mensual",
  "filtro_tipo_compra": "TODOS",
  "totales": {
    "total_transacciones": 50,
    "total_ingresos": 100953.0,
    "total_costos": 81926.0,
    "utilidad": 19027.0,
    "margen_porcentaje": 18.85,
    "flujo_caja": {
      "entradas": {
        "ventas_contado": 79867.0,
        "cobros": 0.0,
        "total": 79867.0
      },
      "salidas": {
        "compras": 333463.0,
        "otros_gastos": 0.0,
        "total": 333463.0
      },
      "saldo": -253596.0
    }
  },
  "periodos": [
    {
      "periodo": "May 2026",
      "fecha_inicio": "01/05/2026",
      "fecha_fin": "31/05/2026",
      "total_transacciones": 23,
      "total_ingresos": 32980.0,
      "total_costos": 22909.0,
      "utilidad": 10071.0,
      "margen_porcentaje": 30.54,
      "flujo_caja": {
        "entradas": {
          "ventas_contado": 22596.0,
          "cobros": 0.0,
          "total": 22596.0
        },
        "salidas": {
          "compras": 164216.0,
          "otros_gastos": 0.0,
          "total": 164216.0
        },
        "saldo": -141620.0
      }
    }
  ]
}
```

> Cada período trae su propio `flujo_caja` (entradas, salidas y saldo), listo para el gráfico de ventas vs. gastos, y un `rango` corto para la etiqueta (ej. `"01 - 07 Oct"`).
>
> **Gráfico semanal del dashboard:** `?agrupacion=semanas_mes&fecha_inicio=01/10/2026&fecha_fin=31/10/2026` devuelve 4 períodos: `Sem 1 Oct 2026` (`01 - 07 Oct`), `Sem 2`, `Sem 3` y `Sem 4` (`22 - 31 Oct`).


---

### 4. Exportación a Excel

`GET /api/finanzas/exportar-excel/`

- **Parámetros:** los mismos del endpoint 2.
- **Respuesta:** archivo binario `.xlsx` con encabezados formateados y celdas con formato contable.
- **En el frontend:** como la API exige el token, **no sirve abrir la URL directamente** (un `<a href>` no envía el encabezado `Authorization`). Se descarga con `fetch` + token y se guarda el archivo desde el navegador (ver `descargarExcel()` en 4.3).

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

`GET /api/finanzas/productos/`

| Parámetro                   | Valores                                                                                     |
| :-------------------------- | :------------------------------------------------------------------------------------------ |
| `search`                    | Busca por nombre o código `no_parte`                                                        |
| `categoria`                 | Por ejemplo, `Abarrotes`, `Lácteos`                                                         |
| `unidad_negocio`            | Por ejemplo, `Supermercado`                                                                 |
| `fecha_inicio`, `fecha_fin` | Período para calcular `total_vendido` y `total_ingresos` (sin fechas = todo el historial)  |
| `tipo_compra`               | `FISICA` u `ONLINE` (para los mismos totales)                                               |
| `ordering`                  | `producto` (por defecto), `total_vendido`, `total_ingresos`, `precio_venta`, `no_parte`. Con `-` adelante, de mayor a menor. |
| `page`, `page_size`         | Paginación                                                                                  |

**Productos más vendidos del mes:** `?ordering=-total_vendido&fecha_inicio=01/10/2026&fecha_fin=31/10/2026&page_size=4`

```json
{
  "count": 7488,
  "next": "http://localhost:8000/api/finanzas/productos/?fecha_fin=31%2F10%2F2026&fecha_inicio=01%2F01%2F2026&ordering=-total_vendido&page=2&page_size=2",
  "previous": null,
  "results": [
    {
      "no_parte": "P860421",
      "producto": "Sopa Ajinomen instantánea fideos pollo verd.",
      "categoria": "Abarrotes",
      "unidad_negocio": "Supermercado",
      "precio_venta": "274.00",
      "costo_venta": "137.00",
      "total_vendido": 199,
      "total_ingresos": "54526.00"
    },
    {
      "no_parte": "P745145",
      "producto": "Mezcla te Suntea polvo durazno",
      "categoria": "Bebidas sin alcohol",
      "unidad_negocio": "Supermercado",
      "precio_venta": "262.00",
      "costo_venta": "131.00",
      "total_vendido": 50,
      "total_ingresos": "13100.00"
    }
  ]
}
```

| Campo            | Significado                                                       |
| :--------------- | :---------------------------------------------------------------- |
| `total_vendido`  | Unidades vendidas en el período (sin ventas anuladas).           |
| `total_ingresos` | Monto vendido en el período (cantidad × precio de cada venta).   |
| `precio_venta`   | Precio de catálogo actual (el que se propone al vender).         |

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
  "count": 14928,
  "next": "http://localhost:8000/api/finanzas/facturas/?page=2&por_cobrar=true",
  "previous": null,
  "results": [
    {
      "factura": "INV7778787-20220820-F",
      "cliente": "1305",
      "cliente_nombre": "Raúl Castillo Medina",
      "fecha": "2026-08-08T00:00:00-04:00",
      "tipo_compra": "FISICA",
      "tipo_compra_nombre": "Física",
      "por_cobrar": true,
      "anulada": false,
      "estado_pago": "PAGADO",
      "fecha_vencimiento": "2026-09-29",
      "total_venta": "72.00",
      "items_count": 1
    }
  ]
}
```

| Campo               | Significado                                                                                   |
| :------------------ | :-------------------------------------------------------------------------------------------- |
| `por_cobrar`        | `true` = se vendió a crédito. No cambia cuando el cliente paga.                               |
| `anulada`           | `true` = la venta se anuló y no suma en los resúmenes.                                        |
| `estado_pago`       | `PAGADO`, `PENDIENTE` o `ANULADO`. Se calcula con la factura y su cuenta por cobrar.          |
| `fecha_vencimiento` | Fecha límite de pago de su cuenta por cobrar (`null` si fue al contado). Antes `fecha_cobro`. |

---

### 8. Líneas de venta detalladas

`GET /api/finanzas/ventas/`

| Parámetro           | Valores                                |
| :------------------ | :------------------------------------- |
| `factura`           | ID de factura                          |
| `producto`          | N° de parte                            |
| `tipo_compra`       | `FISICA` u `ONLINE`                    |
| `estado_pago`       | `PAGADO`, `PENDIENTE` o `ANULADO`      |
| `page`, `page_size` | Paginación                             |

```json
{
  "count": 103489,
  "next": "http://localhost:8000/api/finanzas/ventas/?page=2",
  "previous": null,
  "results": [
    {
      "id": 103489,
      "factura": "INV7777090-20221118-F",
      "no_parte": "P982901",
      "producto_nombre": "Multiesponja Scotch brite cocina colors pague 2 lleve 3",
      "categoria": "Aseo del hogar",
      "tipo_compra": "FISICA",
      "fecha": "2026-11-06T00:00:00-03:00",
      "cantidad": 2,
      "precio_unitario": "176.00",
      "costo_unitario": "148.00",
      "total_venta": "352.00",
      "total_costo": "296.00",
      "utilidad": "56.00",
      "estado_pago": "PAGADO"
    }
  ]
}
```

> `fecha`, `tipo_compra` y `estado_pago` se leen desde la factura (ya no se guardan repetidos en cada línea). `id` ahora es un número.

---

### 9. Cuentas por cobrar

`GET /api/finanzas/cuentas-por-cobrar/`

| Parámetro           | Valores                                                                   |
| :------------------ | :------------------------------------------------------------------------ |
| `cliente`           | ID de cliente                                                             |
| `factura`           | ID de factura                                                             |
| `estado`            | `PENDIENTE` (aún no vence) · `VENCIDA` · `PAGADA`                          |
| `vencidas`          | `true` = solo vencidas · `false` = todas menos las vencidas · omitir = todas |
| `page`, `page_size` | Paginación                                                                |

```json
{
  "count": 14928,
  "next": "http://localhost:8000/api/finanzas/cuentas-por-cobrar/?page=2",
  "previous": null,
  "results": [
    {
      "id": 14928,
      "factura": "INV7778787-20220820-F",
      "fecha_emision": "2026-08-08T00:00:00-04:00",
      "cliente": "1305",
      "cliente_nombre": "Raúl Castillo Medina",
      "cliente_contacto": "+56 9 7484 7558",
      "monto": "72.00",
      "fecha_vencimiento": "2026-09-29",
      "estado": "PAGADA",
      "estado_actual": "PAGADA",
      "fecha_pago": "2026-11-11",
      "vencida": false
    }
  ],
  "resumen": {
    "total_cuentas": 14928,
    "monto_total_por_cobrar": 57339180.0,
    "por_estado": {
      "PENDIENTE": { "nombre": "Pendiente", "cantidad": 0, "monto": 0.0 },
      "VENCIDA": { "nombre": "Vencida", "cantidad": 14927, "monto": 57339180.0 },
      "PAGADA": { "nombre": "Pagada", "cantidad": 1, "monto": 72.0 }
    }
  }
}
```

| Campo                     | Significado                                                                              |
| :------------------------ | :--------------------------------------------------------------------------------------- |
| `estado`                  | Lo que está guardado: `PENDIENTE` o `PAGADA`.                                            |
| `estado_actual`           | Lo que debe mostrar la pantalla: `PENDIENTE`, `VENCIDA` (pendiente con fecha ya pasada) o `PAGADA`. |
| `fecha_pago`              | Fecha en que se pagó (`null` mientras esté pendiente).                                   |
| `vencida`                 | Atajo: `true` si `estado_actual` es `VENCIDA`.                                           |
| `monto_total_por_cobrar`  | Suma de pendientes + vencidas (no incluye las pagadas).                                  |

> Los CSV no informan pagos, así que al importar todas las cuentas parten `PENDIENTE`.

---

### 10. Gastos

`GET /api/finanzas/gastos/`

Incluye las **compras de productos** (`tipo = COMPRA`, siempre con producto) y los **otros gastos** del negocio (`tipo = OTRO`: arriendo, flete, servicios, etc., sin producto).

| Parámetro                   | Valores                                                                          |
| :-------------------------- | :------------------------------------------------------------------------------- |
| `tipo`                      | `COMPRA` u `OTRO`                                                                |
| `categoria`                 | `INSUMOS`, `TRANSPORTE`, `SERVICIOS`, `ARRIENDO`, `MANTENIMIENTO`, `LIMPIEZA`, `OTROS` |
| `categoria_producto`        | Categoría del producto comprado (ej. `Abarrotes`). Antes se llamaba `categoria`. |
| `producto`                  | N° de parte                                                                      |
| `proveedor`                 | Búsqueda parcial por nombre                                                      |
| `fecha_inicio`, `fecha_fin` | Rango de fechas                                                                  |
| `page`, `page_size`         | Paginación                                                                       |

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 20001,
      "tipo": "OTRO",
      "tipo_nombre": "Otro gasto",
      "categoria": "ARRIENDO",
      "categoria_nombre": "Arriendo",
      "producto": null,
      "producto_nombre": "",
      "categoria_producto": "",
      "proveedor": "Inmobiliaria Sur",
      "descripcion": "Arriendo local",
      "fecha": "2026-11-11",
      "monto": "350000.00"
    }
  ],
  "resumen": {
    "total_registros_gasto": 1,
    "monto_total_gastos": 350000.0,
    "por_tipo": {
      "COMPRA": { "nombre": "Compra", "cantidad": 0, "monto": 0.0 },
      "OTRO": { "nombre": "Otro gasto", "cantidad": 1, "monto": 350000.0 }
    }
  }
}
```

> Los 20.000 gastos de los CSV se importan como `COMPRA` con categoría `INSUMOS`.

> `GET /api/finanzas/opciones-filtros/` ahora también entrega `estados_cuenta`, `tipos_gasto` y `categorias_gasto` para llenar los selectores.

---

### 11. Registrar datos (POST)

Todos exigen login y reciben JSON (`Content-Type: application/json`).

| Respuesta | Cuándo                                                                                          |
| :-------: | :---------------------------------------------------------------------------------------------- |
|   `201`   | Se creó (venta, gasto o cliente). La respuesta trae el registro completo.                      |
|   `200`   | Se aplicó la acción (anular, pagar, revertir pago).                                             |
|   `400`   | Datos inválidos: `{"campo": ["mensaje"]}`. Regla del negocio no cumplida: `{"error": "mensaje"}`. |
|   `404`   | No existe la factura o la cuenta indicada.                                                     |

#### 11.1 Registrar una venta — `POST /api/finanzas/facturas/`

| Campo                         | Obligatorio      | Valores                                                              |
| :---------------------------- | :--------------: | :------------------------------------------------------------------- |
| `items`                       |        Sí        | Lista de productos (mínimo 1)                                        |
| `items[].producto`            |        Sí        | N° de parte (ej. `P100055`)                                          |
| `items[].cantidad`            |        Sí        | Entero ≥ 1                                                           |
| `items[].precio_unitario`     |        No        | Si no se envía, se usa el precio de catálogo                         |
| `tipo_compra`                 |        No        | `FISICA` (por defecto) u `ONLINE`                                    |
| `por_cobrar`                  |        No        | `true` = venta a crédito (por defecto `false`)                       |
| `cliente`                     | Solo a crédito   | ID del cliente                                                       |
| `fecha_vencimiento`           | Solo a crédito   | `AAAA-MM-DD`, no anterior a la venta                                 |
| `fecha`                       |        No        | Por defecto, ahora                                                   |

```json
// Venta a crédito
{
  "items": [
    { "producto": "P100055", "cantidad": 2 },
    { "producto": "P100083", "cantidad": 1, "precio_unitario": 1500 }
  ],
  "tipo_compra": "FISICA",
  "por_cobrar": true,
  "cliente": "179",
  "fecha_vencimiento": "2026-11-26"
}

// Respuesta 201: la factura con sus productos y la deuda creada
{
  "factura": "CC174E545A-20261111-F",
  "cliente": "179",
  "cliente_nombre": "José Vega Reyes",
  "fecha": "2026-11-11T23:08:34-03:00",
  "tipo_compra": "FISICA",
  "tipo_compra_nombre": "Física",
  "por_cobrar": true,
  "anulada": false,
  "estado_pago": "PENDIENTE",
  "fecha_vencimiento": "2026-11-26",
  "total_venta": "1788.00",
  "items_count": 2,
  "detalles": [
    { "id": 103491, "no_parte": "P100055", "producto_nombre": "Pasta Capelli D´Angelo Conzazoni",
      "cantidad": 2, "precio_unitario": "144.00", "costo_unitario": "124.00", "total_venta": "288.00" },
    { "id": 103492, "no_parte": "P100083", "producto_nombre": "Salchicha Rica",
      "cantidad": 1, "precio_unitario": "1500.00", "costo_unitario": "127.00", "total_venta": "1500.00" }
  ],
  "cuenta_por_cobrar": {
    "id": 14930,
    "monto": "1788.00",
    "fecha_vencimiento": "2026-11-26",
    "estado": "PENDIENTE",
    "estado_actual": "PENDIENTE",
    "fecha_pago": null,
    "vencida": false
  }
}
```

- Una venta **al contado** es igual, sin `por_cobrar`, `cliente` ni `fecha_vencimiento`; su `cuenta_por_cobrar` es `null`.
- El **costo** de cada línea se toma del catálogo del producto en ese momento.
- El número de factura lo genera el backend (prefijo `CC`).
- Ejemplo de error: `{"items": {"0": {"cantidad": ["Asegúrese de que este valor es mayor o igual a 1."]}}}`.

#### 11.2 Ver una venta — `GET /api/finanzas/facturas/{factura}/`

Devuelve lo mismo que la respuesta de 11.1. Sirve para la ventana de detalle de una operación.

#### 11.3 Anular una venta — `POST /api/finanzas/facturas/{factura}/anular/`

Sin cuerpo. La venta deja de sumar en los resúmenes y en el flujo de caja. Si era a crédito y **no se había pagado**, su deuda desaparece. Si **ya se pagó**, responde `400` (`"La venta ya fue pagada. Primero revierte el pago y luego anúlala."`).

#### 11.4 Registrar un pago — `POST /api/finanzas/cuentas-por-cobrar/{id}/pagar/`

```json
// Cuerpo (opcional; por defecto, hoy)
{ "fecha_pago": "2026-11-11" }

// Respuesta 200
{
  "id": 14930,
  "factura": "CC174E545A-20261111-F",
  "monto": "1788.00",
  "fecha_vencimiento": "2026-11-26",
  "estado": "PAGADA",
  "estado_actual": "PAGADA",
  "fecha_pago": "2026-11-11",
  "vencida": false
}
```

- El pago es **completo** (no hay abonos parciales).
- La fecha de pago no puede ser futura ni anterior a la venta.
- Pagar dos veces responde `400`: `{"error": "La cuenta ya está pagada (el 11/11/2026)."}`.
- Desde ese momento la venta aparece como `PAGADO` y el monto entra al `flujo_caja` en la fecha del pago.

#### 11.5 Deshacer un pago — `POST /api/finanzas/cuentas-por-cobrar/{id}/revertir-pago/`

Sin cuerpo. La cuenta vuelve a `PENDIENTE` y `fecha_pago` queda en `null`.

#### 11.6 Registrar un gasto — `POST /api/finanzas/gastos/`

| Campo         | Obligatorio      | Valores                                                                                 |
| :------------ | :--------------: | :-------------------------------------------------------------------------------------- |
| `tipo`        |        No        | `COMPRA` (por defecto) u `OTRO`                                                         |
| `producto`    | Solo en `COMPRA` | N° de parte del producto comprado. En `OTRO` no se envía.                               |
| `categoria`   |        No        | `INSUMOS`, `TRANSPORTE`, `SERVICIOS`, `ARRIENDO`, `MANTENIMIENTO`, `LIMPIEZA`, `OTROS`. Por defecto `INSUMOS` en compras y `OTROS` en otros gastos. |
| `monto`       |        Sí        | Mayor que 0                                                                             |
| `proveedor`   |        No        | Texto libre                                                                             |
| `descripcion` |        No        | Texto libre                                                                             |
| `fecha`       |        No        | Por defecto, hoy                                                                        |

```json
// Cuerpo
{ "tipo": "OTRO", "categoria": "TRANSPORTE", "monto": 18000,
  "proveedor": "Flete Don Mario", "descripcion": "Flete de mercadería" }

// Respuesta 201
{
  "id": 20001,
  "tipo": "OTRO",
  "tipo_nombre": "Otro gasto",
  "categoria": "TRANSPORTE",
  "categoria_nombre": "Transporte o flete",
  "producto": null,
  "producto_nombre": "",
  "categoria_producto": "",
  "proveedor": "Flete Don Mario",
  "descripcion": "Flete de mercadería",
  "fecha": "2026-11-11",
  "monto": "18000.00"
}
```

#### 11.7 Registrar un cliente — `POST /api/finanzas/clientes/`

```json
// Cuerpo
{ "nombre": "Kiosco Don Luis", "contacto": "+56 9 5587 2216" }

// Respuesta 201 (el ID sigue la numeración de los clientes existentes)
{ "cliente_id": "2001", "nombre": "Kiosco Don Luis", "contacto": "+56 9 5587 2216",
  "total_facturas": 0, "total_deuda": "0.00" }
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

**Qué hace:** centraliza todas las llamadas al backend y el manejo del login. Si una ruta cambia, se corrige solo aquí.

- `authService` inicia y cierra sesión y guarda los tokens en `localStorage`.
- `request()` arma la URL agregando solo los parámetros que tienen valor, **envía el token**, lo **renueva solo** si venció y lanza un error legible si la respuesta no es 2xx.
- `apiService` expone un método por cada endpoint que usa el dashboard.

```javascript
/**
 * Servicio de conexión con la API de Django (Caja Clara)
 */

const API_BASE = "/api/finanzas";
const AUTH_BASE = "/api/auth";

// ---------- Tokens (se guardan en el navegador) ----------
const tokens = {
  get access() { return localStorage.getItem("cc_access"); },
  get refresh() { return localStorage.getItem("cc_refresh"); },
  guardar({ access, refresh }) {
    if (access) localStorage.setItem("cc_access", access);
    if (refresh) localStorage.setItem("cc_refresh", refresh);
  },
  borrar() {
    localStorage.removeItem("cc_access");
    localStorage.removeItem("cc_refresh");
  },
};

async function postJSON(url, cuerpo) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(cuerpo),
  });
  const datos = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(datos.detail || datos.error || `Error HTTP: ${res.status}`);
  return datos;
}

// Pide un access nuevo con el refresh. Devuelve false si la sesión expiró.
async function renovarToken() {
  if (!tokens.refresh) return false;
  try {
    tokens.guardar(await postJSON(`${AUTH_BASE}/refresh/`, { refresh: tokens.refresh }));
    return true;
  } catch {
    tokens.borrar();
    return false;
  }
}

export const authService = {
  async login(username, password) {
    const datos = await postJSON(`${AUTH_BASE}/login/`, { username, password });
    tokens.guardar(datos);
    return datos.usuario; // { id, username, nombre, email, es_admin }
  },
  async logout() {
    if (tokens.refresh) await postJSON(`${AUTH_BASE}/logout/`, { refresh: tokens.refresh }).catch(() => {});
    tokens.borrar();
  },
  estaLogueado() {
    return Boolean(tokens.access);
  },
  perfil() {
    return request(`${AUTH_BASE}/perfil/`);
  },
};

function armarUrl(endpoint, params = {}) {
  const url = new URL(endpoint, window.location.origin);
  // Solo se agregan los parámetros con valor (se ignoran undefined, null y "")
  Object.keys(params).forEach((key) => {
    if (params[key] !== undefined && params[key] !== null && params[key] !== "") {
      url.searchParams.append(key, params[key]);
    }
  });
  return url.toString();
}

async function fetchConToken(url, reintentar = true, opciones = {}) {
  const res = await fetch(url, {
    ...opciones,
    headers: {
      Accept: "application/json",
      ...(opciones.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${tokens.access}`,
    },
  });
  // Token vencido: se renueva una vez y se repite la consulta
  if (res.status === 401 && reintentar && (await renovarToken())) {
    return fetchConToken(url, false, opciones);
  }
  if (res.status === 401) {
    tokens.borrar();
    window.dispatchEvent(new Event("sesion-expirada")); // la app redirige al login
  }
  return res;
}

async function request(endpoint, params = {}) {
  const res = await fetchConToken(armarUrl(endpoint, params));
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.detail || `Error HTTP: ${res.status}`);
  }
  return res.json();
}

// POST con token. Si el backend rechaza los datos, el error trae los mensajes por campo.
async function enviar(endpoint, cuerpo = {}) {
  const res = await fetchConToken(armarUrl(endpoint), true, {
    method: "POST",
    body: JSON.stringify(cuerpo),
  });
  const datos = await res.json().catch(() => ({}));
  if (!res.ok) {
    const error = new Error(datos.error || datos.detail || "Revisa los datos ingresados.");
    error.campos = datos; // ej: { items: { 0: { cantidad: ["..."] } } }
    throw error;
  }
  return datos;
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

  // Endpoint 6 — Productos más vendidos (filtros: fecha_inicio, fecha_fin, tipo_compra)
  getProductos(filtros = {}) {
    return request(`${API_BASE}/productos/`, { page_size: 4, ordering: "-total_vendido", ...filtros });
  },

  // Endpoint 11 — Registrar datos
  registrarVenta(venta) {
    // { items: [{ producto, cantidad, precio_unitario? }], tipo_compra, por_cobrar, cliente?, fecha_vencimiento? }
    return enviar(`${API_BASE}/facturas/`, venta);
  },
  getVenta(factura) {
    return request(`${API_BASE}/facturas/${encodeURIComponent(factura)}/`);
  },
  anularVenta(factura) {
    return enviar(`${API_BASE}/facturas/${encodeURIComponent(factura)}/anular/`);
  },
  registrarPago(cuentaId, fechaPago) {
    return enviar(`${API_BASE}/cuentas-por-cobrar/${cuentaId}/pagar/`, fechaPago ? { fecha_pago: fechaPago } : {});
  },
  revertirPago(cuentaId) {
    return enviar(`${API_BASE}/cuentas-por-cobrar/${cuentaId}/revertir-pago/`);
  },
  registrarGasto(gasto) {
    // { tipo: "COMPRA" | "OTRO", monto, producto?, categoria?, proveedor?, descripcion?, fecha? }
    return enviar(`${API_BASE}/gastos/`, gasto);
  },
  registrarCliente(cliente) {
    return enviar(`${API_BASE}/clientes/`, cliente); // { nombre, contacto? }
  },

  // Endpoint 4 — Descarga del Excel (con token, por eso no sirve un <a href>)
  async descargarExcel(filtros = {}) {
    const res = await fetchConToken(armarUrl(`${API_BASE}/exportar-excel/`, filtros));
    if (!res.ok) throw new Error(`No se pudo descargar el Excel (HTTP ${res.status})`);
    const nombre =
      res.headers.get("Content-Disposition")?.match(/filename="(.+)"/)?.[1] || "reporte_ventas.xlsx";
    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(await res.blob());
    enlace.download = nombre;
    enlace.click();
    URL.revokeObjectURL(enlace.href);
  },
};
```

> **Pantalla de login (🟩 Frontend):** antes de mostrar el dashboard, si `authService.estaLogueado()` es `false`, mostrar un formulario que llame a `authService.login(usuario, clave)`. Escuchar el evento `sesion-expirada` para volver al login, y usar `authService.logout()` en el botón *Cerrar sesión*.

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
- [ ] Pantalla de login que usa `authService.login()` y vuelve al login con el evento `sesion-expirada` (4.3).
- [ ] Botón "Exportar a Excel" usa `apiService.descargarExcel()` (no un `<a href>`).
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
| StatCard · `saldoPeriodo`                | `flujo_caja.saldo` (antes `flujo_caja_neto`, que en realidad es la utilidad)               | `resumen-mensual`                  | ✅ Documentado         |
| StatCard · `ventasMes`                   | `flujo_caja.entradas.total` ("dinero recibido por ventas")                                 | `resumen-mensual`                  | ✅ ⚠️ P06              |
| StatCard · `comprasGastos`               | `flujo_caja.salidas.total` (compras + otros gastos)                                        | `resumen-mensual`                  | ✅ Documentado         |
| StatCard · `pendienteCobrar`             | `por_estado_pago.PENDIENTE.ingresos`                                                       | `resumen-mensual`                  | ✅ Documentado         |
| OperationsSummary · `totalVentas`        | `total_transacciones`                                                                      | `resumen-mensual`                  | ✅ Documentado         |
| OperationsSummary · `totalGastos`        | `resumen.total_registros_gasto`                                                            | `gastos`                           | ✅ Documentado         |
| OperationsSummary · `unidadesVendidas`   | `total_unidades`                                                                           | `resumen-mensual`                  | ✅ Documentado         |
| OperationsSummary · `cuentasPendientes`  | `resumen.total_cuentas`                                                                    | `cuentas-por-cobrar`               | ✅ Documentado         |
| CashChart · `semana`, `ventas`, `gastos` | `periodos[].rango`, `.flujo_caja.entradas.total`, `.flujo_caja.salidas.total` | `resumen-agrupado?agrupacion=semanas_mes` | ✅ Documentado |
| PriorityCollections                      | `id`, `cliente`, `cliente_nombre`, `factura`, `monto`, `fecha_vencimiento`, `vencida`      | `cuentas-por-cobrar?vencidas=true` | ✅ Documentado         |
| RecentOperations                         | `id`, `categoria`, `producto_nombre`, `tipo_compra`, `fecha`, `estado_pago`, `total_venta` | `ventas`                           | ✅ Documentado         |
| TopProducts · `nombre`, `unidadesVendidas`, `totalVentas` | `producto`, `total_vendido`, `total_ingresos` | `productos?ordering=-total_vendido&page_size=4` + fechas del mes | ✅ Documentado |

---

## Parte 6 — Prueba de integración en local

Se necesitan **dos terminales abiertas al mismo tiempo**.

**Terminal 1 — Backend (Django):**

```powershell
# Desde la carpeta raíz del backend
venv\Scripts\python.exe manage.py runserver
# Debe quedar escuchando en http://127.0.0.1:8000
```

Antes de la primera prueba, crear un usuario (una sola vez):

```powershell
venv\Scripts\python.exe manage.py createsuperuser
```

Prueba rápida: abrir `http://127.0.0.1:8000/api/` en el navegador (es público). Para ver los datos en el navegador, entrar primero a `http://127.0.0.1:8000/admin/` con ese usuario y luego abrir `http://127.0.0.1:8000/api/finanzas/opciones-filtros/`. Sin iniciar sesión, la API responde `401`, y eso es lo esperado.

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
| Error 401 en `/api/finanzas/...`             | No se inició sesión o el token venció            | Login (4.3) y encabezado `Authorization`   |
| Error 429 en `/api/auth/login/`              | Demasiados intentos de login seguidos            | Esperar un minuto                          |
| Error 500                                    | Excepción en el backend                          | Consola de la Terminal 1                   |
| Tarjetas en `NaN` o vacías                   | El campo no existe en el JSON (nombre distinto)  | Parte 5 + DevTools → Network → Response    |
| Carga muy lenta                              | Consultas pesadas sobre ~100k registros          | Índices en la BD y consultas del backend   |

---

## Anexo — Pendientes y correcciones a futuro

Problemas detectados al revisar este documento. No bloquean la primera integración, pero conviene resolverlos.

**Prioridad:** 🔴 Alta (puede romper o mostrar datos incorrectos) · 🟠 Media (dato engañoso) · 🟢 Baja (documentación o detalle)

| ID  | Prioridad | Problema                                                                                                                                                                                                                                        | Dónde                           | Responsable | Propuesta                                                                                                              |
| :-- | :-------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------ | :---------- | :--------------------------------------------------------------------------------------------------------------------- |
| P01 | ✅ | Resuelto: `resumen-agrupado` acepta `agrupacion=semanal` (lunes a domingo) y `semanas_mes` (las 4 semanas del mes que usa el gráfico del diseño), con un `rango` corto para la etiqueta. | `resumen-agrupado`, `CashChart` | 🟦 Backend | — |

| P02 | ✅ | Resuelto: `/ventas/` ya tiene respuesta de ejemplo documentada (Parte 3, endpoint 8) e incluye `id`, `categoria`, `producto_nombre`, `tipo_compra`, `fecha`, `estado_pago` y `total_venta`. | `DetalleVentaSerializer`, `RecentOperations` | 🟦 Backend | — |

| P03 | ✅ | Resuelto: `/productos/` calcula `total_vendido` y `total_ingresos` (por período y canal) y permite `?ordering=-total_vendido`. Respuesta documentada en el endpoint 6. | `ProductoSerializer`, `TopProducts` | 🟦 Backend | — |

| P04 | ✅ | Resuelto: `resumen-mensual` entrega `total_unidades` (suma de cantidades vendidas). El frontend debe usarlo en `unidadesVendidas`. | `resumen-mensual`, `gastos` | 🟨 Ambos | — |

| P05 | ✅ | Resuelto: los gastos ahora existen en la API (`gastos` y `flujo_caja.salidas`). Usar `flujo_caja.salidas.total` para el monto y `gastos.resumen.total_registros_gasto` para la cantidad. | `resumen-mensual`, `gastos` | 🟨 Ambos | — |

| P06 | 🟠 | El endpoint se llama `resumen-mensual`, pero acepta cualquier rango. El dashboard lo llama con todo el histórico (2010–2022), así que el KPI `ventasMes` muestra 12 años de ventas, no un mes. | Nombre del endpoint, KPI `ventasMes` | 🟨 Ambos | Renombrar a `resumen-financiero` (manteniendo el alias antiguo por un tiempo) y que el dashboard pida el último mes disponible, o cambiar la etiqueta del KPI. |

| P07 | ✅ | Resuelto: CORS ahora solo permite los dominios de `CORS_ALLOWED_ORIGINS` (por defecto, el servidor de Vite). Se configura en el `.env`. | `settings.py` | 🟦 Backend | — |

| P08 | 🟢 | La guía de prueba usaba la ruta `scratch_ux\ux\prototype\cajaclara-ui`, mientras que el resto del documento usa `ux/prototype/cajaclara-ui`. | Parte 6 | Documentación | Confirmar la ruta real en el repositorio y unificarla. |

| P09 | 🟢 | El ejemplo original de `cuentas-por-cobrar` omitía `next` y `previous`. Se agregaron en esta versión asumiendo la paginación estándar. | Parte 3, endpoint 9 | 🟦 Backend | Verificar con una llamada real que la respuesta incluya ambas claves. |

| P10 | 🟢 | `vencimientoTexto` muestra la fecha en formato ISO (`Vence 2010-02-19`), distinto del formato chileno usado en el resto de la app. | `DashboardView.vue` (paso 6 del script) | 🟩 Frontend | Formatear con `toLocaleDateString("es-CL")`. |

| P11 | 🟢 | El proxy de Vite solo existe en desarrollo. No hay definido cómo encuentra el frontend al backend en producción. | `vite.config.js`, `api.js` | 🟨 Ambos | Usar una variable `VITE_API_URL` en `API_BASE`, o servir ambos detrás del mismo dominio. |

| P12 | 🔴 | La API ahora exige login (JWT). El prototipo todavía no tiene pantalla de login ni envía el token, así que al conectarlo recibirá `401`. | Pantalla de login, `api.js` | 🟩 Frontend | Diseñar la pantalla de login y usar `authService` y `request()` de la sección 4.3. No hay registro público: los usuarios los crea un administrador. |
