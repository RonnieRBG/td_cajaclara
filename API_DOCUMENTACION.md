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
> - ⚠️ **Pxx** = ver el [anexo](#anexo--pendientes-y-correcciones-a-futuro).

---

## 0. Visión general: cómo se conectan las piezas

```
┌──────────────────────┐   fetch /api/...   ┌──────────────────────┐   ORM Django   ┌──────────────────────────┐
│  FRONTEND (Vue 3)    │ ─────────────────▶ │  BACKEND (Django/DRF)│ ─────────────▶ │  BASE DE DATOS (Neon)    │
│  localhost:5173      │                    │  127.0.0.1:8000      │                │  esquema del equipo de   │
│                      │ ◀───────────────── │                      │ ◀───────────── │  datos + vistas Power BI │
│  services/api.js     │       JSON         │  /api/finanzas/...   │                │                          │
└──────────────────────┘                    └──────────────────────┘                └──────────────────────────┘
        ▲                                             ▲
        │ Proxy de Vite: /api → :8000                 │ Variables de entorno DB_* (usuario cajaclara_app_rw)
```

**Idea clave:** las tablas las define el **equipo de datos** (rama `datos`, `Etapa_4_Carga_y_Nube/schema_postgresql.sql`). El backend usa **exactamente** esas tablas y columnas, sin agregar ni cambiar nada, y la API devuelve los campos con **los mismos nombres de columna** (`id_factura`, `id_cliente`, `id_producto`, `precio_venta`…). Así la base, la API, el frontend y Power BI hablan el mismo idioma.

| Equipo        | Lo que entrega                                                  | Lo que necesita del otro equipo                    |
| :------------ | :-------------------------------------------------------------- | :------------------------------------------------- |
| Base de datos | Tablas en Neon con datos + usuario `cajaclara_app_rw`          | Nada                                               |
| Backend       | Endpoints `/api/finanzas/...` que respetan el contrato         | Credenciales de Neon (variables `DB_*`)            |
| Frontend      | Dashboard que consume la API                                    | Backend corriendo en el puerto 8000                |

### Las 6 tablas (iguales al esquema del equipo de datos)

| Tabla               | Columnas                                                                                 | Modelo Django    |
| :------------------ | :--------------------------------------------------------------------------------------- | :--------------- |
| `cliente`           | `id_cliente` (PK), `nombre`, `contacto` (único)                                          | `Cliente`        |
| `producto`          | `id_producto` (PK), `categoria`, `producto`, `unidad_negocio`                            | `Producto`       |
| `venta`             | `id_factura` (PK), `id_cliente`, `fecha`, `tipo_compra` (`Física` / `En Línea`), `por_cobrar` | `Venta`     |
| `detalle_venta`     | `id_detalle` (PK), `id_factura`, `id_producto`, `cantidad`, `precio_venta`, `costo_venta` | `DetalleVenta`  |
| `cuenta_por_cobrar` | `id_cuenta` (PK), `id_factura` (único), `id_cliente`, `monto`, `fecha_vencimiento`, `estado` (`PAGADA` / `PENDIENTE` / `VENCIDA`), `fecha_pago` | `CuentaPorCobrar` |
| `gastos_insumo`     | `id_gasto` (PK), `id_producto`, `fecha`, `monto`                                         | `GastoInsumo`    |

- **Montos enteros** en pesos chilenos (sin decimales).
- **Fechas sin hora** (`AAAA-MM-DD`).
- Los ID numéricos **no los genera la base** (en el esquema son `INTEGER PRIMARY KEY` sin secuencia): el backend asigna el siguiente número (`finanzas/ids.py`).
- El backend **no borra filas**: el usuario `cajaclara_app_rw` solo puede leer, insertar y actualizar.

---

## Parte 1 — Equipo de Base de Datos

### 1.1 Lo que el backend necesita

1. El esquema `schema_postgresql.sql` y los datos ya cargados en Neon (Etapa 4).
2. El script `roles_y_permisos_postgresql.sql` aplicado (usuario `cajaclara_app_rw`).
3. **Una sola vez**, con el usuario administrador (`neondb_owner`), crear las tablas propias de Django (usuarios, login, sesiones) y registrar que las 6 tablas ya existen:

```bash
# con DB_USER=neondb_owner en el .env (solo para este paso)
python manage.py migrate --fake-initial
python manage.py createsuperuser
```

`--fake-initial` hace que Django **no toque** las 6 tablas del equipo de datos: ve que ya existen y solo las anota como creadas. Las tablas de Django (`auth_user`, `token_blacklist_*`, `django_*`) sí se crean; como las crea `neondb_owner`, los permisos por defecto del script de roles se las dan a `cajaclara_app_rw`.

4. Comprobar que todo calza (solo lee, no modifica nada):

```bash
python manage.py verificar_esquema
```

```
✓ cliente: contacto, id_cliente, nombre
✓ producto: categoria, id_producto, producto, unidad_negocio
✓ venta: fecha, id_cliente, id_factura, por_cobrar, tipo_compra
✓ detalle_venta: cantidad, costo_venta, id_detalle, id_factura, id_producto, precio_venta
✓ cuenta_por_cobrar: estado, fecha_pago, fecha_vencimiento, id_cliente, id_cuenta, id_factura, monto
✓ gastos_insumo: fecha, id_gasto, id_producto, monto
El esquema de la base coincide con el backend.
```

> ⚠️ Si el equipo de datos cambia una tabla o columna, el backend tiene que cambiar el modelo en el mismo momento. `verificar_esquema` avisa qué falta.

### 1.2 Variables de entorno

Se copian de **`.env.example`** a **`.env`** (en la carpeta de `manage.py`). El `.env` está en el `.gitignore`: las claves nunca se suben al repositorio. Sin `DB_ENGINE`, el backend usa SQLite local.

| Variable      | Para qué sirve                    | Neon                                 |
| :------------ | :-------------------------------- | :----------------------------------- |
| `DB_ENGINE`   | Driver del motor                  | `django.db.backends.postgresql`      |
| `DB_NAME`     | Nombre de la base                 | `neondb`                             |
| `DB_USER`     | Usuario                           | `cajaclara_app_rw`                   |
| `DB_PASSWORD` | Contraseña                        | (la entrega el equipo de datos)      |
| `DB_HOST`     | Servidor                          | `ep-xxxx.aws.neon.tech`              |
| `DB_PORT`     | Puerto                            | `5432`                               |
| `DB_SSLMODE`  | Conexión cifrada                  | `require` (Neon lo exige)            |

### 1.3 Base local para desarrollo (sin Neon)

Para trabajar sin conexión, el backend crea en SQLite las mismas 6 tablas y carga los CSV del equipo de datos (`data/` = copia de `Etapa_4_Carga_y_Nube/datos_procesados/`):

```bash
python manage.py migrate
python manage.py importar_csv
```

- `--limpiar` vacía las tablas antes de importar.
- `--fechas-originales` mantiene las fechas de los CSV (2010-2022). Por defecto se desplazan un número exacto de semanas para que la última venta quede en la semana actual (cada venta conserva su día de la semana y los plazos de cobro no cambian).
- `--carpeta "ruta"` usa otra carpeta. El comando acepta tanto el formato de la Etapa 4 (con `estado` y `fecha_pago`) como el de la Etapa 3.
- Al terminar crea también las **vistas de métricas** del equipo de datos (`crear_vistas_metricas`), con sus mismos scripts (copiados en `finanzas/sql/`). En Neon ese comando no toca nada: las vistas ya existen.

> Si tenías un `db.sqlite3` anterior a este cambio, **bórralo** y vuelve a correr `migrate` e `importar_csv`: las tablas cambiaron de nombre y de columnas.

### ✅ Checklist del equipo de Base de Datos

- [ ] Esquema y datos cargados en Neon (Etapa 4).
- [ ] `roles_y_permisos_postgresql.sql` aplicado con contraseñas reales.
- [ ] `migrate --fake-initial` y `createsuperuser` ejecutados una vez con `neondb_owner`.
- [ ] Variables `DB_*` entregadas al equipo backend por canal seguro (**nunca en el repositorio**).
- [ ] `verificar_esquema` sin errores.

---

## Parte 2 — Equipo de Backend

Las piezas del código Django de las que depende el acoplamiento. Si alguna se modifica, puede romper al frontend o a la base de datos.

### 2.1 🟦 Modelos = esquema del equipo de datos (`finanzas/models.py`)

- Cada modelo tiene `db_table` y `db_column` con los nombres exactos del esquema.
- **No agregar columnas ni tablas** a esos modelos: el usuario `cajaclara_app_rw` no puede alterar el esquema. Si hace falta un dato nuevo, se acuerda con el equipo de datos y ellos lo agregan primero.
- La prueba `EsquemaDelEquipoDeDatosTests` falla si una tabla o columna deja de calzar.

### 2.2 🟦 Configuración de base de datos (`settings.py`)

`DATABASES` lee las variables `DB_*` (y `DB_SSLMODE`). Sin `DB_ENGINE` usa SQLite. **No escribir credenciales en el código.**

### 2.3 🟦 CORS (`settings.py`)

Solo los sitios de `CORS_ALLOWED_ORIGINS` pueden llamar a la API desde el navegador. Por defecto, el servidor de Vite (`http://localhost:5173` y `http://127.0.0.1:5173`). Al publicar el frontend en otro dominio se agrega en el `.env`.

### 2.4 🟦 Paginación

En **todos** los listados: 50 por página por defecto, `?page_size=N` hasta 500, y respuesta con `count`, `next`, `previous` y `results`.

### 2.5 🟦 Formatos de fecha aceptados

`fecha_inicio` y `fecha_fin` aceptan `DD/MM/AAAA` (`31/12/2012`) y `AAAA-MM-DD` (`2012-12-31`).

### 2.6 🟦 Serializers: el verdadero contrato

**Los nombres de campo que devuelven los serializers son lo que el frontend lee.** Son los mismos nombres de columna del esquema de datos. Antes de cambiar uno, revisar la [Parte 5](#parte-5--punto-de-acoplamiento).

### 2.7 🟦 Seguridad y login (`settings.py`)

- **Toda la API exige login** (`IsAuthenticated`). Solo `/api/` (el catálogo) y `/api/auth/` son públicas.
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y `DJANGO_ALLOWED_HOSTS` se leen del `.env`. Con `DJANGO_DEBUG=False` el backend no arranca si falta la clave.
- Tokens: `JWT_ACCESS_MINUTOS` (30) y `JWT_REFRESH_DIAS` (7). Intentos de login: `LOGIN_RATE` (10 por minuto).
- No hay registro público: los usuarios los crea un administrador.

### ✅ Checklist del equipo de Backend

- [ ] `python manage.py test` sin errores (incluye la prueba del esquema).
- [ ] `verificar_esquema` sin errores contra Neon.
- [ ] `.env` creado a partir de `.env.example` (en producción: `DJANGO_DEBUG=False` y `DJANGO_SECRET_KEY` propia).
- [ ] Servidor corriendo en `127.0.0.1:8000`.

---

## Parte 3 — Contrato de la API

Referencia común para **ambos equipos**.

- **URL base en desarrollo:** `http://localhost:8000`
- **Prefijo:** `/api/finanzas/`
- **Montos:** números enteros en pesos chilenos (ya no llegan como texto ni con decimales).
- **Fechas:** `AAAA-MM-DD`.
- **`tipo_compra`:** `"Física"` o `"En Línea"` (como en la base). Como parámetro también se acepta sin tilde o en mayúsculas (`fisica`, `EN LINEA`, `ONLINE`).

### 🔐 Autenticación (JWT)

**Todas las rutas de `/api/finanzas/` exigen iniciar sesión.** Sin token responden `401`.

| Método y ruta             | Para qué sirve                                   | Cuerpo (JSON)          |
| :------------------------ | :----------------------------------------------- | :--------------------- |
| `POST /api/auth/login/`   | Iniciar sesión                                   | `username`, `password` |
| `POST /api/auth/refresh/` | Obtener un `access` nuevo cuando el actual vence | `refresh`              |
| `POST /api/auth/logout/`  | Cerrar sesión (invalida el `refresh`)            | `refresh`              |
| `GET /api/auth/perfil/`   | Datos del usuario que inició sesión              | —                      |

**Login:**

```json
// POST /api/auth/login/
{ "username": "admin", "password": "••••••••" }

// Respuesta 200
{
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "usuario": { "id": 1, "username": "admin", "nombre": "Ana Pérez", "email": "admin@cajaclara.cl", "es_admin": true }
}
```

En cada consulta se envía el encabezado `Authorization: Bearer <access>`. El `access` dura **30 minutos** y el `refresh` **7 días**. Cuando una consulta responde `401`, el frontend llama a `/api/auth/refresh/` con el `refresh`; recibe un `access` **y un `refresh` nuevos** y repite la consulta. Si el refresh también falla, se vuelve a la pantalla de login.

| Respuesta | Cuándo                                                                                         |
| :-------: | :--------------------------------------------------------------------------------------------- |
|   `401`   | Sin token, token vencido o inválido, o clave incorrecta (`"Usuario o contraseña incorrectos."`) |
|   `429`   | Demasiados intentos de login seguidos (10 por minuto)                                          |

### Resumen de endpoints

| #   | Método y ruta              | Para qué sirve                         | Tabla                | Paginado | Lo usa el dashboard |
| :-- | :------------------------- | :------------------------------------- | :------------------- | :------: | :-----------------: |
| 1   | `GET /opciones-filtros/`   | Valores para selects y rango de fechas | varias               |    No    |         ✅          |
| 2   | `GET /resumen-mensual/`    | KPIs financieros de un rango de fechas | varias               |    No    |         ✅          |
| 3   | `GET /resumen-agrupado/`   | Serie temporal para gráficos           | varias               |    No    |         ✅          |
| 4   | `GET /exportar-excel/`     | Descarga de archivo `.xlsx`            | `detalle_venta`      |    No    |   (botón export)    |
| 5   | `GET /clientes/`           | Listado de clientes                    | `cliente`            |    Sí    |          —          |
| 6   | `GET /productos/`          | Listado de productos                   | `producto`           |    Sí    |         ✅          |
| 7   | `GET /facturas/`           | Listado de ventas                      | `venta`              |    Sí    |          —          |
| 8   | `GET /ventas/`             | Líneas de venta                        | `detalle_venta`      |    Sí    |         ✅          |
| 9   | `GET /cuentas-por-cobrar/` | Deudas de clientes + resumen global    | `cuenta_por_cobrar`  |    Sí    |         ✅          |
| 10  | `GET /gastos/`             | Gastos en insumos + resumen            | `gastos_insumo`      |    Sí    |          —          |
| 12  | `GET /alertas-cobro/`      | Cobros vencidos o por vencer, por prioridad | `cuenta_por_cobrar` |  Sí    |         ✅          |
| 13  | `GET /metricas/{nombre}/`  | Métricas del equipo de datos (las de Power BI) | vistas `vw_*`  | Según la vista | (análisis)   |

**Registrar datos** (detalle en el endpoint 11):

| Método y ruta                                        | Para qué sirve                               |
| :--------------------------------------------------- | :------------------------------------------- |
| `POST /facturas/`                                    | Registrar una venta (al contado o a crédito) |
| `GET /facturas/{id_factura}/`                        | Ver una venta con sus productos y su deuda   |
| `POST /cuentas-por-cobrar/{id_cuenta}/pagar/`        | Registrar el pago de una deuda               |
| `POST /cuentas-por-cobrar/{id_cuenta}/revertir-pago/`| Deshacer un pago registrado por error        |
| `POST /gastos/`                                      | Registrar un gasto en insumos                |
| `POST /clientes/`                                    | Registrar un cliente                         |

### Estructura de los listados paginados

```json
{
  "count": 100067,
  "next": "http://localhost:8000/api/finanzas/facturas/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

Los endpoints 9, 10 y 12 agregan una clave `resumen` con totales que **no dependen de la página**.

---

### 1. Opciones de filtros

`GET /api/finanzas/opciones-filtros/`

**El frontend lo llama primero** para saber qué rango de fechas pedir.

```json
{
  "categorias": ["Abarrotes", "Aseo del hogar", "Bebidas sin alcohol", "..."],
  "unidades_negocio": ["Supermercado"],
  "tipos_compra": [
    { "codigo": "Física", "nombre": "Física" },
    { "codigo": "En Línea", "nombre": "En Línea" }
  ],
  "estados_pago": [
    { "codigo": "PAGADO", "nombre": "Pagado" },
    { "codigo": "PENDIENTE", "nombre": "Pendiente" }
  ],
  "estados_cuenta": [
    { "codigo": "PENDIENTE", "nombre": "Pendiente" },
    { "codigo": "VENCIDA", "nombre": "Vencida" },
    { "codigo": "PAGADA", "nombre": "Pagada" }
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

| Parámetro      | Obligatorio | Valores                                                          |
| :------------- | :---------: | :--------------------------------------------------------------- |
| `periodo`      |     No      | `mensual` (por defecto), `trimestral` o `anual`: hasta hoy       |
| `fecha_inicio` |     No      | `01/08/2022` o `2022-08-01` (junto con `fecha_fin`)              |
| `fecha_fin`    |     No      | `31/08/2022` o `2022-08-31`                                      |
| `tipo_compra`  |     No      | `Física` o `En Línea` (omitir = todos)                           |

```json
// GET /api/finanzas/resumen-mensual/?fecha_inicio=2022-08-01&fecha_fin=2022-08-31
{
  "rango_aplicado": { "fecha_inicio": "01/08/2022", "fecha_fin": "31/08/2022", "periodo_tipo": "personalizado" },
  "filtro_tipo_compra": "TODOS",
  "total_transacciones": 19,
  "total_unidades": 38,
  "total_ingresos": 16057,
  "total_costos": 12871,
  "utilidad_bruta": 3186,
  "margen_porcentaje": 19.84,
  "por_estado_pago": {
    "PAGADO": { "nombre": "Pagado", "transacciones": 17, "ingresos": 12902 },
    "PENDIENTE": { "nombre": "Pendiente", "transacciones": 2, "ingresos": 3155 }
  },
  "flujo_caja": {
    "entradas": { "ventas_contado": 12902, "cobros": 11613, "total": 24515 },
    "salidas": { "gastos_insumo": 188863, "total": 188863 },
    "saldo": -164348
  }
}
```

| Campo                 | Significado                                                                                                            |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| `total_transacciones` | Líneas de venta del período (filas de `detalle_venta`).                                                                |
| `total_ingresos`      | Todo lo **vendido** en el período (al contado y a crédito).                                                            |
| `total_costos`        | Costo de la mercadería vendida (`cantidad × costo_venta`).                                                             |
| `utilidad_bruta`      | `total_ingresos - total_costos`.                                                                                       |
| `total_unidades`      | Unidades vendidas (suma de cantidades).                                                                                |
| `flujo_caja.entradas` | Dinero que **entró**: ventas al contado (`ventas_contado`) + deudas **cobradas** en el período (`cobros`).             |
| `flujo_caja.salidas`  | Dinero que **salió**: `gastos_insumo` del período.                                                                     |
| `flujo_caja.saldo`    | `entradas.total - salidas.total`. Es el "Saldo del periodo" del dashboard.                                             |

> Es el mismo cálculo que la vista `vw_flujo_caja_mensual` del equipo de datos (se comprobó mes a mes con los datos de Neon). Una venta a crédito suma en `total_ingresos` el día que se vende, pero entra a `flujo_caja` el día que se **paga**. El filtro `tipo_compra` afecta las entradas; los gastos no tienen canal.

---

### 3. Serie temporal para gráficos

`GET /api/finanzas/resumen-agrupado/`

| Parámetro                    | Obligatorio | Valores                                                                                                                                                         |
| :--------------------------- | :---------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fecha_inicio`               |     Sí      | `01/01/2022` o `2022-01-01`                                                                                                                                     |
| `fecha_fin`                  |     No      | Por defecto, hoy                                                                                                                                                |
| `agrupacion`                 |     No      | `diaria`, `semanal` (lunes a domingo), `semanas_mes` (1-7, 8-14, 15-21, 22-fin de mes, como el gráfico del diseño), `mensual` (por defecto), `trimestral`, `anual` |
| `tipo_compra`                |     No      | Igual que el endpoint 2                                                                                                                                         |

```json
// GET /api/finanzas/resumen-agrupado/?fecha_inicio=2022-01-01&fecha_fin=2022-03-31&agrupacion=mensual
{
  "rango_aplicado": { "fecha_inicio": "01/01/2022", "fecha_fin": "31/03/2022" },
  "agrupacion": "mensual",
  "filtro_tipo_compra": "TODOS",
  "totales": {
    "total_transacciones": 105,
    "total_ingresos": 237080,
    "total_costos": 161915,
    "utilidad": 75165,
    "margen_porcentaje": 31.7,
    "flujo_caja": {
      "entradas": { "ventas_contado": 220448, "cobros": 67405, "total": 287853 },
      "salidas": { "gastos_insumo": 493795, "total": 493795 },
      "saldo": -205942
    }
  },
  "periodos": [
    {
      "periodo": "Ene 2022",
      "fecha_inicio": "01/01/2022",
      "fecha_fin": "31/01/2022",
      "rango": "01 - 31 Ene",
      "total_transacciones": 43,
      "total_ingresos": 94000,
      "total_costos": 72395,
      "utilidad": 21605,
      "margen_porcentaje": 22.98,
      "flujo_caja": {
        "entradas": { "ventas_contado": 83950, "cobros": 54033, "total": 137983 },
        "salidas": { "gastos_insumo": 182637, "total": 182637 },
        "saldo": -44654
      }
    }
  ]
}
```

> **Gráfico semanal del dashboard:** `?agrupacion=semanas_mes&fecha_inicio=01/10/2026&fecha_fin=31/10/2026` devuelve 4 períodos: `Sem 1 Oct 2026` (`01 - 07 Oct`), `Sem 2`, `Sem 3` y `Sem 4` (`22 - 31 Oct`).

---

### 4. Exportación a Excel

`GET /api/finanzas/exportar-excel/`

- **Parámetros:** los mismos del endpoint 2.
- **Respuesta:** archivo `.xlsx` con el detalle de ventas (factura, producto, tipo de compra, cantidad, precio, costo, totales, utilidad y estado de pago).
- **En el frontend:** como la API exige el token, **no sirve un `<a href>`**. Se descarga con `fetch` + token (ver `descargarExcel()` en 4.3).

---

### 5. Clientes

`GET /api/finanzas/clientes/`

| Parámetro           | Valores                                       |
| :------------------ | :-------------------------------------------- |
| `search`            | Texto: busca por nombre, contacto o `id_cliente` |
| `page`, `page_size` | Paginación                                    |

```json
{
  "count": 2000,
  "next": "http://localhost:8000/api/finanzas/clientes/?page=2",
  "previous": null,
  "results": [
    {
      "id_cliente": 564,
      "nombre": "Ana Aguilar Martínez",
      "contacto": "+56 9 9783 6571",
      "total_facturas": 43,
      "total_deuda": 0
    }
  ]
}
```

`total_deuda` = suma de sus cuentas **no pagadas** (pendientes y vencidas).

---

### 6. Productos

`GET /api/finanzas/productos/`

| Parámetro                   | Valores                                                                                    |
| :-------------------------- | :----------------------------------------------------------------------------------------- |
| `search`                    | Busca por nombre o `id_producto`                                                           |
| `categoria`                 | Por ejemplo, `Abarrotes`                                                                   |
| `unidad_negocio`            | Por ejemplo, `Supermercado`                                                                |
| `fecha_inicio`, `fecha_fin` | Período para calcular `total_vendido` y `total_ingresos` (sin fechas = todo el historial)  |
| `tipo_compra`               | `Física` o `En Línea` (para los mismos totales)                                            |
| `ordering`                  | `producto` (por defecto), `total_vendido`, `total_ingresos`, `id_producto`. Con `-` adelante, de mayor a menor. |
| `page`, `page_size`         | Paginación                                                                                 |

**Productos más vendidos del mes:** `?ordering=-total_vendido&fecha_inicio=01/10/2026&fecha_fin=31/10/2026&page_size=4`

```json
{
  "count": 7488,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id_producto": "P474155",
      "producto": "Mezcla te Suntea polvo durazno",
      "categoria": "Bebidas sin alcohol",
      "unidad_negocio": "Supermercado",
      "total_vendido": 23807,
      "total_ingresos": 18837301
    }
  ]
}
```

> El esquema de datos **no tiene precio de catálogo**: el precio y el costo viven en cada línea de venta (`detalle_venta`).

---

### 7. Facturas (tabla `venta`)

`GET /api/finanzas/facturas/`

| Parámetro                   | Valores               |
| :-------------------------- | :-------------------- |
| `cliente`                   | `id_cliente`          |
| `tipo_compra`               | `Física` o `En Línea` |
| `por_cobrar`                | `true` o `false`      |
| `fecha_inicio`, `fecha_fin` | Rango de fechas       |
| `page`, `page_size`         | Paginación            |

```json
{
  "count": 14928,
  "next": "http://localhost:8000/api/finanzas/facturas/?page=2&por_cobrar=true",
  "previous": null,
  "results": [
    {
      "id_factura": "INV7778787-20220820-F",
      "id_cliente": 1305,
      "cliente_nombre": "Raúl Castillo Medina",
      "fecha": "2022-08-20",
      "tipo_compra": "Física",
      "por_cobrar": true,
      "estado_pago": "PENDIENTE",
      "fecha_vencimiento": "2022-09-09",
      "total_venta": 72,
      "items_count": 1
    }
  ]
}
```

| Campo               | Significado                                                                         |
| :------------------ | :---------------------------------------------------------------------------------- |
| `por_cobrar`        | `true` = se vendió a crédito. No cambia cuando el cliente paga.                     |
| `estado_pago`       | `PAGADO` o `PENDIENTE`. Se calcula con la venta y su cuenta por cobrar.             |
| `fecha_vencimiento` | Fecha límite de pago de su cuenta por cobrar (`null` si fue al contado).            |

---

### 8. Líneas de venta (tabla `detalle_venta`)

`GET /api/finanzas/ventas/`

| Parámetro           | Valores                 |
| :------------------ | :---------------------- |
| `factura`           | `id_factura`            |
| `producto`          | `id_producto`           |
| `tipo_compra`       | `Física` o `En Línea`   |
| `estado_pago`       | `PAGADO` o `PENDIENTE`  |
| `page`, `page_size` | Paginación              |

```json
{
  "count": 103489,
  "next": "http://localhost:8000/api/finanzas/ventas/?page=2",
  "previous": null,
  "results": [
    {
      "id_detalle": 103489,
      "id_factura": "INV7777090-20221118-F",
      "id_producto": "P982901",
      "producto_nombre": "Multiesponja Scotch brite cocina colors pague 2 lleve 3",
      "categoria": "Aseo del hogar",
      "tipo_compra": "Física",
      "fecha": "2022-11-18",
      "cantidad": 2,
      "precio_venta": 176,
      "costo_venta": 148,
      "total_venta": 352,
      "total_costo": 296,
      "utilidad": 56,
      "estado_pago": "PAGADO"
    }
  ]
}
```

> `precio_venta` y `costo_venta` son **unitarios**. `fecha`, `tipo_compra` y `estado_pago` se leen desde la venta.

---

### 9. Cuentas por cobrar (tabla `cuenta_por_cobrar`)

`GET /api/finanzas/cuentas-por-cobrar/` (ejemplo: `?estado=VENCIDA&page_size=1` sobre los datos de Neon, consultado el 16/11/2026)

| Parámetro           | Valores                                                                      |
| :------------------ | :--------------------------------------------------------------------------- |
| `cliente`           | `id_cliente`                                                                 |
| `factura`           | `id_factura`                                                                 |
| `estado`            | `PENDIENTE` (aún no vence) · `VENCIDA` · `PAGADA` (estado a la fecha de hoy) |
| `vencidas`          | `true` = solo vencidas · `false` = todas menos las vencidas · omitir = todas |
| `page`, `page_size` | Paginación                                                                   |

```json
{
  "count": 8,
  "next": "http://localhost:8000/api/finanzas/cuentas-por-cobrar/?estado=VENCIDA&page=2&page_size=1",
  "previous": null,
  "results": [
    {
      "id_cuenta": 14853,
      "id_factura": "INV7777527-20210822-L",
      "fecha_emision": "2021-08-22",
      "id_cliente": 653,
      "cliente_nombre": "Patricia Molina Contreras",
      "cliente_contacto": "+56 9 2208 9846",
      "monto": 1662,
      "fecha_vencimiento": "2021-10-07",
      "estado": "VENCIDA",
      "estado_actual": "VENCIDA",
      "dias_atraso": 1866,
      "fecha_pago": null
    }
  ],
  "resumen": {
    "total_cuentas": 8,
    "monto_total_por_cobrar": 10725,
    "por_estado": {
      "PENDIENTE": { "nombre": "Pendiente", "cantidad": 0, "monto": 0 },
      "VENCIDA": { "nombre": "Vencida", "cantidad": 8, "monto": 10725 },
      "PAGADA": { "nombre": "Pagada", "cantidad": 0, "monto": 0 }
    }
  }
}
```

| Campo                    | Significado                                                                                                    |
| :----------------------- | :------------------------------------------------------------------------------------------------------------- |
| `estado`                 | Lo guardado en la base: `PENDIENTE`, `VENCIDA` o `PAGADA` (el equipo de datos guarda `VENCIDA` a su fecha de corte). |
| `estado_actual`          | Lo que debe mostrar la pantalla **hoy**: `PAGADA`; `VENCIDA` si está guardada así o si su fecha ya pasó; si no, `PENDIENTE`. |
| `dias_atraso`            | Días desde el vencimiento (0 si no está vencida o ya se pagó).                                                  |
| `fecha_pago`             | Fecha en que se pagó (`null` mientras no se pague).                                                            |
| `monto_total_por_cobrar` | Suma de pendientes + vencidas.                                                                                 |

---

### 10. Gastos (tabla `gastos_insumo`)

`GET /api/finanzas/gastos/`

Cada gasto es una compra de insumos ligada a un producto.

| Parámetro                   | Valores                                          |
| :-------------------------- | :----------------------------------------------- |
| `producto`                  | `id_producto`                                    |
| `categoria`                 | Categoría del producto comprado (ej. `Abarrotes`) |
| `fecha_inicio`, `fecha_fin` | Rango de fechas                                  |
| `page`, `page_size`         | Paginación                                       |

```json
{
  "count": 20000,
  "next": "http://localhost:8000/api/finanzas/gastos/?page=2",
  "previous": null,
  "results": [
    {
      "id_gasto": 20000,
      "id_producto": "P755255",
      "producto_nombre": "Dulces surtidos El paraguitas",
      "categoria": "Snacks y confitería",
      "fecha": "2022-11-18",
      "monto": 1171
    }
  ],
  "resumen": { "total_registros_gasto": 20000, "monto_total_gastos": 24484481 }
}
```

---

### 11. Registrar datos (POST)

Todos exigen login y reciben JSON (`Content-Type: application/json`). **No hay endpoints para borrar ni anular**: el usuario de la base solo puede leer, insertar y actualizar.

| Respuesta | Cuándo                                                                                            |
| :-------: | :------------------------------------------------------------------------------------------------ |
|   `201`   | Se creó (venta, gasto o cliente). La respuesta trae el registro completo.                         |
|   `200`   | Se aplicó la acción (pagar, revertir pago).                                                       |
|   `400`   | Datos inválidos: `{"campo": ["mensaje"]}`. Regla del negocio no cumplida: `{"error": "mensaje"}`. |
|   `404`   | No existe la venta o la cuenta indicada.                                                          |

#### 11.1 Registrar una venta — `POST /api/finanzas/facturas/`

| Campo                   | Obligatorio    | Valores                                                                   |
| :---------------------- | :------------: | :------------------------------------------------------------------------ |
| `items`                 |       Sí       | Lista de productos (mínimo 1)                                             |
| `items[].id_producto`   |       Sí       | Ej. `P100055`                                                             |
| `items[].cantidad`      |       Sí       | Entero ≥ 1                                                                |
| `items[].precio_venta`  |       No       | Precio unitario. Si no se envía, el de la última venta del producto       |
| `items[].costo_venta`   |       No       | Costo unitario. Si no se envía, el de la última venta del producto        |
| `id_cliente`            |       Sí       | En el esquema de datos toda venta tiene cliente                           |
| `tipo_compra`           |       No       | `Física` (por defecto) o `En Línea`                                       |
| `por_cobrar`            |       No       | `true` = venta a crédito (por defecto `false`)                            |
| `fecha_vencimiento`     | Solo a crédito | `AAAA-MM-DD`, no anterior a la venta                                      |
| `fecha`                 |       No       | `AAAA-MM-DD`, por defecto hoy                                             |

```json
// Venta a crédito
{
  "id_cliente": 179,
  "items": [{ "id_producto": "P126966", "cantidad": 2 }],
  "tipo_compra": "En Línea",
  "por_cobrar": true,
  "fecha_vencimiento": "2026-12-31"
}

// Respuesta 201: la venta con sus productos y la deuda creada
{
  "id_factura": "CC9A0EBF05-20261116-L",
  "id_cliente": 179,
  "cliente_nombre": "José Vega Reyes",
  "fecha": "2026-11-16",
  "tipo_compra": "En Línea",
  "por_cobrar": true,
  "estado_pago": "PENDIENTE",
  "fecha_vencimiento": "2026-12-31",
  "total_venta": 818,
  "items_count": 1,
  "detalles": [
    { "id_detalle": 103490, "id_producto": "P126966", "producto_nombre": "Aguardiente Nectar club",
      "cantidad": 2, "precio_venta": 409, "costo_venta": 352, "total_venta": 818 }
  ],
  "cuenta_por_cobrar": {
    "id_cuenta": 14929, "id_factura": "CC9A0EBF05-20261116-L", "fecha_emision": "2026-11-16",
    "id_cliente": 179, "cliente_nombre": "José Vega Reyes", "cliente_contacto": "+56 9 9821 7744",
    "monto": 818, "fecha_vencimiento": "2026-12-31", "estado": "PENDIENTE", "estado_actual": "PENDIENTE",
    "dias_atraso": 0, "fecha_pago": null
  }
}
```

- Una venta **al contado** es igual, sin `por_cobrar` ni `fecha_vencimiento`; su `cuenta_por_cobrar` es `null`.
- Si un producto **nunca se ha vendido**, hay que enviar su `precio_venta` y `costo_venta` (si no, `400`).
- El número de factura lo genera el backend (prefijo `CC`, ej. `CC9A0EBF05-20261116-L`; `F` = Física, `L` = En Línea).

#### 11.2 Ver una venta — `GET /api/finanzas/facturas/{id_factura}/`

Devuelve lo mismo que la respuesta de 11.1.

#### 11.3 Registrar un pago — `POST /api/finanzas/cuentas-por-cobrar/{id_cuenta}/pagar/`

```json
// Cuerpo (opcional; por defecto, hoy)
{ "fecha_pago": "2026-11-16" }
```

Responde la cuenta con `"estado": "PAGADA"` y su `fecha_pago`.

- El pago es **completo** (no hay abonos parciales).
- La fecha de pago no puede ser futura ni anterior a la venta.
- Pagar dos veces responde `400`: `{"error": "La cuenta ya está pagada (el 16/11/2026)."}`.

#### 11.4 Deshacer un pago — `POST /api/finanzas/cuentas-por-cobrar/{id_cuenta}/revertir-pago/`

Sin cuerpo. `fecha_pago` queda en `null` y la cuenta vuelve a `PENDIENTE`, o a `VENCIDA` si su fecha ya pasó.

#### 11.5 Registrar un gasto — `POST /api/finanzas/gastos/`

| Campo         | Obligatorio | Valores                       |
| :------------ | :---------: | :---------------------------- |
| `id_producto` |     Sí      | Producto comprado             |
| `monto`       |     Sí      | Entero mayor que 0            |
| `fecha`       |     No      | `AAAA-MM-DD`, por defecto hoy |

```json
// Cuerpo
{ "id_producto": "P126966", "monto": 5000 }

// Respuesta 201
{ "id_gasto": 20001, "id_producto": "P126966", "producto_nombre": "Aguardiente Nectar club",
  "categoria": "Bebidas sin alcohol", "fecha": "2026-11-16", "monto": 5000 }
```

#### 11.6 Registrar un cliente — `POST /api/finanzas/clientes/`

`nombre` y `contacto` son obligatorios, y `contacto` no se puede repetir (como en el esquema de datos).

```json
// Cuerpo
{ "nombre": "Kiosco Don Luis", "contacto": "+56 9 5587 2216" }

// Respuesta 201 (el ID sigue la numeración)
{ "id_cliente": 2001, "nombre": "Kiosco Don Luis", "contacto": "+56 9 5587 2216", "total_facturas": 0, "total_deuda": 0 }
```

---

### 12. Alertas de cobro

`GET /api/finanzas/alertas-cobro/`

Cuentas **vencidas o que vencen pronto**, ordenadas por urgencia. Es la Tarea 29 del equipo de datos: usa la **misma lógica, los mismos campos y el mismo mensaje** que su vista `vw_alertas_cobro`. La diferencia es la fecha: la vista (y Power BI) calculan a una fecha fija (`2022-09-01`); la API calcula **a la fecha de hoy**, como indica la "Sección B" de su script para la operación en vivo.

| Parámetro           | Valores                                                                                         |
| :------------------ | :---------------------------------------------------------------------------------------------- |
| `dias_aviso`        | Cuántos días hacia adelante avisar. Por defecto `15`.                                           |
| `prioridad`         | `CRITICA`, `ALTA`, `MEDIA` o `BAJA`                                                             |
| `cliente`           | `id_cliente`                                                                                    |
| `todas`             | `true` = incluye también las vigentes que vencen después de la ventana                          |
| `fecha_corte`       | Calcula a esa fecha en vez de hoy. Con `2022-09-01` entrega **lo mismo que `vw_alertas_cobro`** |
| `page`, `page_size` | Paginación                                                                                      |

| `prioridad_alerta`    | `ventana_alerta`     | Cuándo                                              |
| :-------------------- | :------------------- | :-------------------------------------------------- |
| `1_CRITICA_VENCIDA`   | Vencida              | Guardada como `VENCIDA` o con fecha ya pasada       |
| `2_ALTA_PROXIMA_7D`   | Vence en <= 7 días   | Vence dentro de 7 días                              |
| `3_MEDIA_PROXIMA_15D` | Vence en 8-15 días   | Vence entre 8 y 15 días                             |
| `4_BAJA_VIGENTE`      | Vigente > 15 días    | Solo aparece con `todas=true` o un `dias_aviso` mayor |

```json
// GET /api/finanzas/alertas-cobro/?fecha_corte=2022-09-01
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "id_cuenta": 14853,
      "id_factura": "INV7777527-20210822-L",
      "id_cliente": 653,
      "cliente_nombre": "Patricia Molina Contreras",
      "cliente_contacto": "+56 9 2208 9846",
      "fecha_emision": "2021-08-22",
      "fecha_vencimiento": "2021-10-07",
      "estado": "VENCIDA",
      "monto": 1662,
      "dias_para_vencer": -329,
      "dias_atraso": 329,
      "tipo_alerta": "VENCIDA",
      "prioridad_alerta": "1_CRITICA_VENCIDA",
      "ventana_alerta": "Vencida",
      "requiere_notificacion": true,
      "mensaje_sugerido": "Recordatorio urgente: cliente Patricia Molina Contreras mantiene factura INV7777527-20210822-L vencida hace 329 días por $1662."
    }
  ],
  "resumen": {
    "fecha_corte": "2022-09-01",
    "dias_aviso": 15,
    "total_alertas": 8,
    "monto_total": 10725,
    "por_prioridad": {
      "1_CRITICA_VENCIDA": { "nombre": "Vencida", "cantidad": 6, "monto": 7570 },
      "2_ALTA_PROXIMA_7D": { "nombre": "Vence en <= 7 días", "cantidad": 1, "monto": 3083 },
      "3_MEDIA_PROXIMA_15D": { "nombre": "Vence en 8-15 días", "cantidad": 1, "monto": 72 },
      "4_BAJA_VIGENTE": { "nombre": "Vigente > 15 días", "cantidad": 0, "monto": 0 }
    }
  }
}
```

> Se comparó campo por campo con `vw_alertas_cobro` sobre los datos del equipo de datos: las 8 alertas coinciden (6 críticas por $7.570, 1 alta por $3.083 y 1 media por $72, igual que en su instructivo de la Etapa 6). **Sin `fecha_corte`** (hoy), esas mismas 8 cuentas salen todas como críticas, porque ya pasó su fecha.
>
> Al pagar una cuenta (11.3), deja de aparecer en las alertas.

---

### 13. Métricas del equipo de datos (las mismas de Power BI)

`GET /api/finanzas/metricas/` → lista las métricas con sus filtros y columnas.
`GET /api/finanzas/metricas/{nombre}/` → filas de la vista.

Es la Tarea 30: la API **lee las vistas SQL del equipo de datos, sin recalcular**. Las columnas del JSON son las de la vista. Así la app y el tablero de Power BI muestran exactamente los mismos números.

| `{nombre}`                   | Vista                           | Qué responde                                                        | Filtros (`?columna=valor`)                                          | Paginada |
| :--------------------------- | :------------------------------ | :------------------------------------------------------------------ | :------------------------------------------------------------------ | :------: |
| `margen-productos`           | `vw_margen_producto_categoria`  | Margen por producto, categoría y mes                                | `anio`, `mes`, `periodo`, `cobertura`, `id_producto`, `categoria`, `search` | Sí |
| `ventas-categoria-mes`       | `vw_ventas_categoria_mes`       | Ventas y margen por categoría y mes                                 | `anio`, `mes`, `periodo`, `cobertura`, `categoria`                  |    Sí    |
| `flujo-caja-mensual`         | `vw_flujo_caja_mensual`         | Lo facturado, lo cobrado, los gastos y el flujo neto de cada mes    | `anio`, `mes`, `periodo`, `cobertura`                               |    Sí    |
| `cuentas-por-cobrar-cliente` | `vw_cuentas_por_cobrar_cliente` | Cuánto debe cada cliente y su historial de atrasos                  | `id_cliente`, `con_deuda=true`, `search`                            |    Sí    |
| `morosidad`                  | `vw_indicador_morosidad`        | Indicador de morosidad en 3 escenarios                              | —                                                                   |    No    |
| `ranking-productos`          | `vw_ranking_productos`          | Productos estrella, de nicho, de alto volumen y de baja venta       | `categoria`, `clasificacion_desempeno`, `id_producto`, `sin_alerta_escala=true`, `search` | Sí |
| `sustentabilidad`            | `vw_sustentabilidad_negocio`    | Por año: margen contra gastos y contra lo vendido al fiado          | `anio`, `cobertura`                                                 |    No    |

- **`ordering`**: cualquier columna de la vista; con `-` adelante, de mayor a menor. Varias separadas por coma (`?ordering=-anio,-ventas`).
- **`periodo`** tiene la forma `AAAA-MM` (ej. `2019-05`). **`cobertura`** es `completa` (2010–2020) o `parcial` (2021–2022), como la definió el equipo de datos.
- Las paginadas responden `count`, `next`, `previous` y `results`; las otras, `{"vista": "...", "results": [...]}`.

```json
// GET /api/finanzas/metricas/ranking-productos/?page_size=1
{
  "count": 7408,
  "next": "http://localhost:8000/api/finanzas/metricas/ranking-productos/?page=2&page_size=1",
  "previous": null,
  "results": [
    {
      "id_producto": "P474155", "producto": "Mezcla te Suntea polvo durazno", "categoria": "Bebidas sin alcohol",
      "num_facturas": 25, "unidades_vendidas": 23108, "ventas": 18441667, "costo": 16351867, "margen": 2089800,
      "margen_pct": 11.33, "alerta_escala_etapa2": false, "rank_ventas": 1, "rank_margen": 4,
      "clasificacion_desempeno": "Estrella"
    }
  ]
}

// GET /api/finanzas/metricas/morosidad/
{
  "vista": "vw_indicador_morosidad",
  "results": [
    { "escenario": "Corte Final Dataset (2022-09-01)", "cuentas_por_cobrar_abiertas": 8, "cuentas_vencidas": 6,
      "monto_por_cobrar": 10725, "monto_vencido": 7570, "morosidad_monto_pct": 70.58, "morosidad_cuentas_pct": 75 },
    { "escenario": "Cierre Cobertura Completa (2020-12-31)", "cuentas_por_cobrar_abiertas": 167, "cuentas_vencidas": 26,
      "monto_por_cobrar": 469968, "monto_vencido": 63914, "morosidad_monto_pct": 13.6, "morosidad_cuentas_pct": 15.57 },
    { "escenario": "Histórico Pagos con Atraso (2010-2022)", "cuentas_por_cobrar_abiertas": 14928, "cuentas_vencidas": 3917,
      "monto_por_cobrar": 57339252, "monto_vencido": 15457664, "morosidad_monto_pct": 26.96, "morosidad_cuentas_pct": 26.24 }
  ]
}

// GET /api/finanzas/metricas/sustentabilidad/?anio=2019
{
  "vista": "vw_sustentabilidad_negocio",
  "results": [
    { "anio": 2019, "cobertura": "completa", "ventas": 57385826, "costo": 44054353, "margen_bruto": 13331473,
      "gastos_insumo": 1954429, "utilidad_neta_operativa": 11377044, "monto_fiado": 8748289,
      "ratio_margen_sobre_gastos": 6.82, "pct_ventas_fiadas": 15.24, "fiado_sobre_margen_pct": 65.62 }
  ]
}
```

**Cosas que hay que saber:**

- ⚠️ **Son vistas de análisis histórico con fechas de corte fijas** que definió el equipo de datos (`2022-09-01` para la cartera y la morosidad; `2020-12-31` para la "cobertura completa" y el ranking). Para lo operativo de **hoy** se usan `cuentas-por-cobrar/` (endpoint 9) y `alertas-cobro/` (endpoint 12). Por eso `morosidad` dice 6 cuentas vencidas y el endpoint 9 dice 8: no es un error, son dos fechas distintas (ver P16).
- **Si las vistas no existen**, responde `503` con el mensaje de qué hacer. En Neon las crea el equipo de datos; en local, `python manage.py crear_vistas_metricas` (lo hace solo `importar_csv`).
- **En local con fechas desplazadas** (el modo por defecto de `importar_csv`), estas vistas dan números distintos a los de Neon, porque sus fechas de corte son fijas. Para compararlas con Power BI en local: `python manage.py importar_csv --limpiar --fechas-originales`.
- Si el equipo de datos cambia una vista, se vuelven a copiar sus scripts en `finanzas/sql/` y se ajusta la lista de columnas en `finanzas/metricas.py`.

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
  // Endpoint 12 — Cobros prioritarios (vencidos y por vencer)
  getAlertasCobro(filtros = {}) {
    return request(`${API_BASE}/alertas-cobro/`, { page_size: 5, ...filtros });
  },

  // Endpoint 13 — Métricas del equipo de datos: getMetrica("ranking-productos", { categoria: "Abarrotes" })
  getMetrica(nombre, filtros = {}) {
    return request(`${API_BASE}/metricas/${nombre}/`, filtros);
  },

  getProductos(filtros = {}) {
    return request(`${API_BASE}/productos/`, { page_size: 4, ordering: "-total_vendido", ...filtros });
  },

  // Endpoint 11 — Registrar datos
  registrarVenta(venta) {
    // { id_cliente, items: [{ id_producto, cantidad, precio_venta?, costo_venta? }], tipo_compra, por_cobrar, fecha_vencimiento? }
    return enviar(`${API_BASE}/facturas/`, venta);
  },
  getVenta(idFactura) {
    return request(`${API_BASE}/facturas/${encodeURIComponent(idFactura)}/`);
  },
  registrarPago(idCuenta, fechaPago) {
    return enviar(`${API_BASE}/cuentas-por-cobrar/${idCuenta}/pagar/`, fechaPago ? { fecha_pago: fechaPago } : {});
  },
  revertirPago(idCuenta) {
    return enviar(`${API_BASE}/cuentas-por-cobrar/${idCuenta}/revertir-pago/`);
  },
  registrarGasto(gasto) {
    // { id_producto, monto, fecha? }
    return enviar(`${API_BASE}/gastos/`, gasto);
  },
  registrarCliente(cliente) {
    return enviar(`${API_BASE}/clientes/`, cliente); // { nombre, contacto }
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
      saldoPeriodo: resumen.flujo_caja.saldo,
      ventasMes: resumen.flujo_caja.entradas.total, // ⚠️ P06
      comprasGastos: resumen.flujo_caja.salidas.total,
      pendienteCobrar: cuentas.resumen?.monto_total_por_cobrar || 0,
    };

    // 4. Resumen de operaciones
    operationsSummary.value = {
      totalVentas: resumen.total_transacciones,
      totalGastos: resumen.flujo_caja.salidas.gastos_insumo,
      unidadesVendidas: resumen.total_unidades,
      cuentasPendientes: cuentas.resumen?.total_cuentas || 0,
    };

    // 5. Gráfico de flujo de caja (últimos 8 periodos)
    weeklyFlow.value = (agrupado.periodos || []).slice(-8).map((p) => ({
      semana: p.rango,
      ventas: p.flujo_caja.entradas.total,
      gastos: p.flujo_caja.salidas.total,
    }));

    // 6. Cobros prioritarios
    priorityCollections.value = (cuentas.results || []).map((c) => ({
      id: c.id_cuenta,
      cliente: c.cliente_nombre || `Cliente #${c.id_cliente}`,
      detalle: `Factura ${c.id_factura}`,
      documento: c.id_factura,
      monto: c.monto, // ya es un número entero
      vencimientoTexto: c.estado_actual === "VENCIDA" ? "Vencida" : `Vence ${c.fecha_vencimiento}`,
      estado: c.estado_actual,
    }));

    // 7. Movimientos recientes
    recentOperations.value = (ventas.results || []).map((v) => ({
      id: v.id_detalle,
      tipo: "VENTA",
      concepto: v.categoria || "Venta",
      detalle: v.producto_nombre,
      clienteProveedor: v.tipo_compra === "En Línea" ? "En Línea" : "Tienda Física",
      canal: v.tipo_compra,
      fecha: v.fecha, // "AAAA-MM-DD"
      estado: v.estado_pago,
      monto: v.total_venta,
    }));

    // 8. Productos
    topProducts.value = (productos.results || []).map((p) => ({
      id: p.id_producto,
      nombre: p.producto,
      unidadesVendidas: p.total_vendido,
      totalVentas: p.total_ingresos,
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
| StatCard · `saldoPeriodo`                | `flujo_caja.saldo`                                                                         | `resumen-mensual`                  | ✅ Documentado         |
| StatCard · `ventasMes`                   | `flujo_caja.entradas.total` ("dinero recibido por ventas")                                 | `resumen-mensual`                  | ✅ ⚠️ P06              |
| StatCard · `comprasGastos`               | `flujo_caja.salidas.total` (gastos en insumos)                                             | `resumen-mensual`                  | ✅ Documentado         |
| StatCard · `pendienteCobrar`             | `resumen.monto_total_por_cobrar`                                                           | `cuentas-por-cobrar`               | ✅ Documentado         |
| OperationsSummary · `totalVentas`        | `total_transacciones`                                                                      | `resumen-mensual`                  | ✅ Documentado         |
| OperationsSummary · `totalGastos`        | `flujo_caja.salidas.gastos_insumo` (monto) o `resumen.total_registros_gasto` (cantidad)   | `resumen-mensual` / `gastos`       | ✅ Documentado         |
| OperationsSummary · `unidadesVendidas`   | `total_unidades`                                                                           | `resumen-mensual`                  | ✅ Documentado         |
| OperationsSummary · `cuentasPendientes`  | `resumen.total_cuentas`                                                                    | `cuentas-por-cobrar`               | ✅ Documentado         |
| CashChart · `semana`, `ventas`, `gastos` | `periodos[].rango`, `.flujo_caja.entradas.total`, `.flujo_caja.salidas.total` | `resumen-agrupado?agrupacion=semanas_mes` | ✅ Documentado |
| PriorityCollections                      | `id_cuenta`, `id_cliente`, `cliente_nombre`, `id_factura`, `monto`, `fecha_vencimiento`, `prioridad_alerta`, `ventana_alerta`, `dias_atraso`, `dias_para_vencer`, `mensaje_sugerido` | `alertas-cobro?page_size=5` | ✅ Documentado |
| RecentOperations                         | `id_detalle`, `categoria`, `producto_nombre`, `tipo_compra`, `fecha`, `estado_pago`, `total_venta` | `ventas`                   | ✅ Documentado         |
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

| P02 | ✅ | Resuelto: `/ventas/` ya tiene respuesta de ejemplo documentada (Parte 3, endpoint 8) e incluye `id_detalle`, `categoria`, `producto_nombre`, `tipo_compra`, `fecha`, `estado_pago` y `total_venta`. | `DetalleVentaSerializer`, `RecentOperations` | 🟦 Backend | — |

| P03 | ✅ | Resuelto: `/productos/` calcula `total_vendido` y `total_ingresos` (por período y canal) y permite `?ordering=-total_vendido`. Respuesta documentada en el endpoint 6. | `ProductoSerializer`, `TopProducts` | 🟦 Backend | — |

| P04 | ✅ | Resuelto: `resumen-mensual` entrega `total_unidades` (suma de cantidades vendidas). El frontend debe usarlo en `unidadesVendidas`. | `resumen-mensual`, `gastos` | 🟨 Ambos | — |

| P05 | ✅ | Resuelto: los gastos existen en la API (`gastos` y `flujo_caja.salidas.gastos_insumo`). | `resumen-mensual`, `gastos` | 🟨 Ambos | — |

| P06 | 🟠 | El endpoint se llama `resumen-mensual`, pero acepta cualquier rango. El dashboard lo llama con todo el histórico (2010–2022), así que el KPI `ventasMes` muestra 12 años de ventas, no un mes. | Nombre del endpoint, KPI `ventasMes` | 🟨 Ambos | Renombrar a `resumen-financiero` (manteniendo el alias antiguo por un tiempo) y que el dashboard pida el último mes disponible, o cambiar la etiqueta del KPI. |

| P07 | ✅ | Resuelto: CORS ahora solo permite los dominios de `CORS_ALLOWED_ORIGINS` (por defecto, el servidor de Vite). Se configura en el `.env`. | `settings.py` | 🟦 Backend | — |

| P08 | 🟢 | La guía de prueba usaba la ruta `scratch_ux\ux\prototype\cajaclara-ui`, mientras que el resto del documento usa `ux/prototype/cajaclara-ui`. | Parte 6 | Documentación | Confirmar la ruta real en el repositorio y unificarla. |

| P09 | 🟢 | El ejemplo original de `cuentas-por-cobrar` omitía `next` y `previous`. Se agregaron en esta versión asumiendo la paginación estándar. | Parte 3, endpoint 9 | 🟦 Backend | Verificar con una llamada real que la respuesta incluya ambas claves. |

| P10 | 🟢 | `vencimientoTexto` muestra la fecha en formato ISO (`Vence 2010-02-19`), distinto del formato chileno usado en el resto de la app. | `DashboardView.vue` (paso 6 del script) | 🟩 Frontend | Formatear con `toLocaleDateString("es-CL")`. |

| P11 | 🟢 | El proxy de Vite solo existe en desarrollo. No hay definido cómo encuentra el frontend al backend en producción. | `vite.config.js`, `api.js` | 🟨 Ambos | Usar una variable `VITE_API_URL` en `API_BASE`, o servir ambos detrás del mismo dominio. |

| P12 | 🔴 | La API ahora exige login (JWT). El prototipo todavía no tiene pantalla de login ni envía el token, así que al conectarlo recibirá `401`. | Pantalla de login, `api.js` | 🟩 Frontend | Diseñar la pantalla de login y usar `authService` y `request()` de la sección 4.3. No hay registro público: los usuarios los crea un administrador. |

| P13 | 🟠 | En Neon los datos tienen sus fechas originales (2010 a nov. 2022). Si el dashboard pide "el mes actual" (`periodo=mensual`), verá casi todo en cero. En local no pasa porque `importar_csv` desplaza las fechas. | Dashboard, datos de Neon | 🟨 Ambos | Que el dashboard parta en el último mes con datos (`opciones-filtros` → `rango_fechas_disponible.max`), o que el equipo de datos acuerde desplazar las fechas para la demo. |

| P14 | 🟢 | En el esquema de datos los ID (`id_detalle`, `id_cuenta`, `id_gasto`, `id_cliente`) son `INTEGER PRIMARY KEY` sin secuencia. El backend asigna el siguiente número y reintenta si dos personas guardan a la vez. | `finanzas/ids.py` | 🟨 Ambos | Si el equipo de datos los cambia a `GENERATED BY DEFAULT AS IDENTITY`, el backend sigue funcionando igual. |

| P15 | 🟢 | Se quitó lo que no existe en el esquema de datos: anular ventas, ventas sin cliente, precio de catálogo, y tipo/categoría/proveedor/descripción de los gastos (todo gasto es de un producto). | Modelos, endpoint 11 | 🟨 Ambos | Si alguno se necesita, el equipo de datos agrega la columna primero y luego el backend. |

| P16 | 🟠 | Dos fechas de corte: las vistas de análisis del equipo de datos (`morosidad`, `cuentas-por-cobrar-cliente`, `vw_alertas_cobro`) calculan al `2022-09-01`; la API operativa (`cuentas-por-cobrar`, `alertas-cobro`) calcula a hoy. Con los datos actuales: 6 vencidas según la vista, 8 según la API. | Endpoints 9, 12 y 13; Power BI | 🟨 Datos + Backend | Acordar la regla: lo histórico usa las vistas tal cual; lo operativo usa la fecha de hoy. Mostrar en pantalla a qué fecha corresponde cada número. `alertas-cobro?fecha_corte=2022-09-01` reproduce la vista. |
