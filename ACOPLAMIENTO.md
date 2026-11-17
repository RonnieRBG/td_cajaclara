# 🔗 Acoplamiento de Caja Clara — qué tiene que hacer cada equipo

Guía paso a paso para juntar las tres ramas del proyecto en una sola aplicación que funcione:

```text
  🗄️ Datos (rama datos)          🧠 Backend (rama backend)          🎨 Frontend / UX (rama ux)
  Base Neon (PostgreSQL)  ──►    API Django REST            ──►     Prototipo Vue 3 + Vite
  6 tablas + vistas BI           /api/finanzas/...                  ux/prototype/cajaclara-ui
```

> **Regla de oro:** las tablas las define el **equipo de datos** (`datos/Etapas_4-5-6/Etapa_4_Carga_y_Nube/schema_postgresql.sql`). El backend usa exactamente esas tablas y columnas, y la API entrega los campos con **los mismos nombres** (`id_factura`, `id_cliente`, `id_producto`, `precio_venta`…). El frontend solo habla con la API, nunca con la base.
>
> El detalle de cada endpoint (parámetros y respuestas de ejemplo) está en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md). Este archivo dice **quién hace qué y en qué orden**.

---

## 📅 Orden de trabajo

| Paso | Equipo   | Qué se hace                                                        | Depende de | Estado (17/11/2026)                                   |
| :--: | :------- | :----------------------------------------------------------------- | :--------: | :---------------------------------------------------- |
|  1   | Datos    | Dejar Neon listo y entregar las credenciales del backend           |     —      | 🟡 Neon cargado; faltan claves nuevas y entregarlas   |
|  2   | Datos    | Crear (una sola vez) las tablas de usuarios de Django en Neon      |     1      | ⏳ Pendiente                                          |
|  3   | Backend  | Conectar la API a Neon y comprobar el esquema                      |    1, 2    | 🟡 Backend listo; espera las credenciales             |
|  4   | Frontend | Conectar el prototipo a la API (login, lecturas y formularios)     |     3      | 🟡 Login, Dashboard y Resumen conectados (rama `integration/ux-backend`); faltan Operaciones, Cobros y formularios |
|  5   | Todos    | Prueba de integración completa (checklist final)                   |  1 al 4    | ⏳ Pendiente                                          |
|  6   | Backend + Frontend | Publicar: backend en un servicio + frontend en Vercel (Parte 5) | 3, 5 | ⏳ Falta elegir dónde publicar el backend |

> El frontend **no necesita esperar a Neon**: puede avanzar desde el día 1 contra el backend en local con SQLite (ver 3.1).
>
> 🤖 **Equipo UX:** si usan un asistente de IA, la [Parte 3B](#-parte-3b--prompt-para-la-ia-del-equipo-ux) trae un prompt listo para copiar con todo el contexto.

---

## 🗄️ Parte 1 — Equipo de Datos

### Paso 1.1 — Confirmar que Neon tiene el esquema y los datos

En el **SQL Editor de Neon** (como `neondb_owner`), revisar que las 6 tablas tengan las filas esperadas:

```sql
SELECT 'cliente' AS tabla, COUNT(*) FROM cliente
UNION ALL SELECT 'producto', COUNT(*) FROM producto
UNION ALL SELECT 'venta', COUNT(*) FROM venta
UNION ALL SELECT 'detalle_venta', COUNT(*) FROM detalle_venta
UNION ALL SELECT 'cuenta_por_cobrar', COUNT(*) FROM cuenta_por_cobrar
UNION ALL SELECT 'gastos_insumo', COUNT(*) FROM gastos_insumo;
```

| Tabla               | Filas esperadas |
| :------------------ | --------------: |
| `cliente`           |           2.000 |
| `producto`          |           7.488 |
| `venta`             |         100.067 |
| `detalle_venta`     |         103.489 |
| `cuenta_por_cobrar` |          14.928 |
| `gastos_insumo`     |          20.000 |

### Paso 1.2 — Cambiar las contraseñas de los roles

El archivo `roles_y_permisos_postgresql.sql` que está en la rama `datos` tiene contraseñas escritas (`SuperPowerBi.1` y `SuperDjango.1`), y el repositorio es visible para otros. Hay que cambiarlas en Neon:

```sql
ALTER ROLE cajaclara_app_rw     PASSWORD '<clave_nueva_de_al_menos_20_caracteres>';
ALTER ROLE cajaclara_lectura_bi PASSWORD '<otra_clave_nueva>';
```

Y en el archivo del repositorio, dejar `REEMPLAZAR_CLAVE_SEGURA_APP` / `REEMPLAZAR_CLAVE_SEGURA_BI` en lugar de las claves reales. Actualizar luego la conexión de Power BI con la clave nueva.

### Paso 1.3 — Entregar las credenciales al equipo backend

Por un canal privado (mensaje directo o gestor de claves del equipo, **nunca en GitHub**):

```dotenv
DB_ENGINE=django.db.backends.postgresql
DB_NAME=neondb
DB_USER=cajaclara_app_rw
DB_PASSWORD=<clave del paso 1.2>
DB_HOST=ep-xxxx.aws.neon.tech
DB_PORT=5432
DB_SSLMODE=require
```

### Paso 1.4 — Crear las tablas de usuarios de Django (una sola vez)

El login de la API necesita tablas propias de Django (`auth_user`, `token_blacklist_*`, `django_*`). El usuario `cajaclara_app_rw` no puede crear tablas, así que lo hace **una vez** el equipo de datos con `neondb_owner`, desde una copia de la rama `backend`:

```bash
git clone -b backend https://github.com/RonnieRBG/td_cajaclara.git cajaclara_backend
cd cajaclara_backend
python -m venv venv
venv\Scripts\activate            # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Crear un archivo `.env` (junto a `manage.py`) con los datos del paso 1.3, pero con el **usuario administrador**:

```dotenv
DB_ENGINE=django.db.backends.postgresql
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=<clave de neondb_owner>
DB_HOST=ep-xxxx.aws.neon.tech
DB_PORT=5432
DB_SSLMODE=require
```

Y ejecutar:

```bash
python manage.py migrate --fake-initial    # crea las tablas de Django; NO toca las 6 tablas de datos
python manage.py createsuperuser           # primer usuario para entrar a la app
python manage.py verificar_esquema         # debe terminar en "El esquema de la base coincide con el backend."
```

> `--fake-initial` es obligatorio: hace que Django vea que las 6 tablas ya existen y solo las anote, sin modificarlas. Como las tablas nuevas las crea `neondb_owner`, los permisos por defecto del script de roles se las dan a `cajaclara_app_rw` automáticamente.
>
> Al terminar, **borrar ese `.env`** (tiene la clave del administrador).

> `verificar_esquema` también avisa si faltan las **vistas de métricas** de la Etapa 5 (`vw_margen_producto_categoria`, `vw_ranking_productos`, etc.). La API las lee en `/api/finanzas/metricas/`, así que deben existir en Neon y `cajaclara_app_rw` debe tener `SELECT` sobre ellas (el `GRANT` ya viene al final de `vistas_metricas_postgresql.sql`).

### Paso 1.5 — Respaldo antes de conectar la app

En Neon: **Dashboard → Branches → Create branch** (por ejemplo `antes-de-la-api`). Si algo sale mal en la prueba, se vuelve a ese punto.

### Paso 1.6 — Regla para cambios futuros

Si el equipo de datos necesita **cambiar una tabla, una columna o una vista de métricas** (agregar, renombrar, cambiar tipo):

1. Avisar al equipo backend **antes** de aplicarlo en Neon.
2. El backend ajusta el modelo en `finanzas/models.py` el mismo día.
3. Ambos corren `python manage.py verificar_esquema` para confirmar.

### ✅ Checklist del equipo de Datos

- [ ] Las 6 tablas tienen las filas esperadas (1.1).
- [ ] Contraseñas de los roles cambiadas en Neon y quitadas del repositorio (1.2).
- [ ] Credenciales de `cajaclara_app_rw` entregadas al backend por canal privado (1.3).
- [ ] `migrate --fake-initial` y `createsuperuser` ejecutados con `neondb_owner` (1.4).
- [ ] `verificar_esquema` sin errores (1.4).
- [ ] Branch de respaldo creado en Neon (1.5).

---

## 🧠 Parte 2 — Equipo de Backend

### Paso 2.1 — Configurar la conexión a Neon

En la carpeta de `manage.py`, copiar `.env.example` como `.env` y completar con lo que entregó el equipo de datos (paso 1.3). Además:

```dotenv
DJANGO_DEBUG=True                                   # False al publicar
DJANGO_SECRET_KEY=<generar una>                     # python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Paso 2.2 — Comprobar el esquema y las pruebas

```bash
python manage.py verificar_esquema    # con el .env de Neon: solo lee, no modifica nada
python manage.py test                 # usa una base temporal en SQLite (ver nota)
```

> Para correr las pruebas, comentar temporalmente `DB_ENGINE` en el `.env`: `cajaclara_app_rw` no puede crear la base de pruebas en Neon. Hoy son 51 pruebas, y una de ellas (`EsquemaDelEquipoDeDatosTests`) falla si una tabla o columna deja de coincidir con el esquema de datos.

### Paso 2.3 — Levantar la API y probarla contra Neon

```bash
python manage.py runserver
```

1. Abrir `http://127.0.0.1:8000/api/`: catálogo público de endpoints.
2. Entrar a `http://127.0.0.1:8000/admin/` con el usuario del paso 1.4.
3. Abrir `http://127.0.0.1:8000/api/finanzas/opciones-filtros/`: debe mostrar `rango_fechas_disponible` de `2010-01-05` a `2022-11-18`.
4. Abrir `http://127.0.0.1:8000/api/finanzas/metricas/`: las 7 métricas deben decir `"disponible": true` (son las vistas de la Etapa 5).
5. Comparar un mes con la vista de datos. Por ejemplo, agosto de 2022:
   - API: `/api/finanzas/resumen-mensual/?fecha_inicio=2022-08-01&fecha_fin=2022-08-31` → `flujo_caja.saldo`
   - Neon: `SELECT flujo_caja_neto FROM vw_flujo_caja_mensual WHERE periodo = '2022-08';`
   - Los dos deben dar **-164348**.

### Paso 2.4 — Crear los usuarios de la app (los administra backend)

Hay **dos tipos de usuario** y es fácil confundirlos:

| Tipo                          | Qué es                                                          | Ejemplos                               | Quién lo maneja |
| :---------------------------- | :-------------------------------------------------------------- | :------------------------------------- | :-------------- |
| **Usuario de la base de datos** | Con el que Django se conecta a Neon. Nadie entra a la app con él. | `cajaclara_app_rw`, `neondb_owner`   | Datos           |
| **Usuario de la app**         | Con el que una persona entra al login (Vercel o local). Es una fila de la tabla `auth_user` de Django, guardada en Neon. | `admin`, `demo`, `jorge` | **Backend** |

- **No hay un usuario ni una contraseña fijos en el código**, y no debe haberlos. Tampoco hay registro público.
- **Requisito:** las tablas de usuarios de Django deben existir en Neon (paso 1.4). Crearlas necesita `neondb_owner`. Si el equipo de datos prefiere, puede pasarle esa clave a backend **solo para ese paso**, y backend la borra de su `.env` al terminar.
- Después, backend crea los usuarios de la app con las credenciales normales (`cajaclara_app_rw`):

```bash
python manage.py createsuperuser      # administrador (entra también a /admin/)
```

  o desde `/admin/` → **Usuarios** → **Agregar** (para usuarios comunes, como el de la demo).

- Se sugiere: **un administrador** (backend), **un usuario por integrante** que lo necesite y **un usuario `demo`** para la presentación.
- Las contraseñas se entregan por un canal privado. **Nunca** en GitHub, en el README ni en las variables de Vercel.
- En **local** (SQLite), cada persona crea su propio usuario con `createsuperuser`: no hace falta pedirlo.

### Paso 2.5 — Avisar al frontend

Cuando 2.3 funcione, avisar al equipo de frontend que la API está lista y entregarles **un usuario de prueba** (no el administrador). El equipo UX **no necesita credenciales de Neon**: solo un usuario de la app.

### Paso 2.6 — Si el equipo de datos cambia el esquema

1. Ajustar `finanzas/models.py` (`db_table`, `db_column`, tipo).
2. `python manage.py makemigrations finanzas` y, en Neon, `python manage.py migrate --fake finanzas` (la tabla ya la cambió datos).
3. Actualizar el serializer si el campo sale en la API y anotarlo en la Parte 5 de `API_DOCUMENTACION.md` para que frontend se entere.
4. `verificar_esquema` y `test`.

### ✅ Checklist del equipo de Backend

- [ ] `.env` con Neon, clave secreta y CORS (2.1).
- [ ] `verificar_esquema` y `test` sin errores (2.2).
- [ ] Saldo de agosto 2022 igual a `vw_flujo_caja_mensual` (2.3).
- [ ] Usuarios de la app creados: administrador, integrantes y `demo` (2.4).
- [ ] Usuario de prueba entregado al frontend (2.5).

---

## 🎨 Parte 3 — Equipo de Frontend / UX

El prototipo está en `ux/prototype/cajaclara-ui`.

> **Estado al 17/11/2026**
>
> El trabajo de integración está en la rama **`integration/ux-backend`** (Jorge, commit `1463e4e`). Es `ux` + `backend` unidos; el merge no cambió el código del backend y se puede volver a unir con la rama `backend` actual sin conflictos. Todavía **no está en `main`**.
>
> - ✅ **Login** listo y compatible con el backend (login, perfil, renovación del token, cierre de sesión, errores y CORS).
> - ✅ **Dashboard y Resumen mensual** conectados a la API, con modo de datos simulados opcional (`VITE_USE_MOCKS=true`). Se probaron sus adaptadores con las respuestas reales de la API (datos 2010-2022): los 10 funcionan sin errores y el saldo de agosto 2022 da **-$164.348**, igual que `vw_flujo_caja_mensual`.
> - ✅ `node_modules/` y `dist/` fuera del repositorio.
> - 🔧 **Dos ajustes pendientes** (enviados a Jorge):
>   1. **Cobros prioritarios:** usar `tipo_alerta` (`VENCIDA` o `POR_VENCER`) en vez de `estado`. Hay cuentas guardadas como `PENDIENTE` que ya vencieron (2 de 8) y se verían como "Pendiente" siendo críticas.
>   2. **Resumen mensual:** "ventas" (lo vendido, agosto: $16.057) menos gastos ($188.863) no da el saldo (-$164.348), porque el saldo incluye cobros de fiados de meses anteriores. Mostrar "Entradas de caja" (`flujo_caja.entradas.total` = $24.515) o agregar la línea "Cobros de fiados" (`flujo_caja.entradas.cobros`).
> - 🟡 **Faltan:** pantallas de **Operaciones** y **Cobros**, los **formularios** (venta, gasto, pago, cliente) y **Exportar a Excel** (pasos 3.5 a 3.9).
> - 🌐 El sitio en Vercel (`https://tdcajaclara-cajaclara-ui-omega.vercel.app`) todavía muestra datos simulados: falta publicar el backend (Parte 5).

### Paso 3.1 — Tener el backend corriendo en local (sin esperar a Neon)

```bash
git clone -b backend https://github.com/RonnieRBG/td_cajaclara.git cajaclara_backend
cd cajaclara_backend
python -m venv venv
venv\Scripts\activate            # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate         # crea las mismas 6 tablas en SQLite
python manage.py importar_csv    # carga los CSV del equipo de datos (fechas movidas a la semana actual)
python manage.py createsuperuser
python manage.py runserver       # queda en http://127.0.0.1:8000
```

> En local las fechas se desplazan para que la última venta quede en esta semana, así el dashboard muestra "el mes actual" con datos. **En Neon no**: ahí los datos terminan en noviembre de 2022 (ver paso 3.8).

### Paso 3.2 — Limpiar la rama `ux` antes de integrar ✅

**Hecho** (commits `e520c03` y `df42a8e`): `node_modules/` y `dist/` ya no están en el repositorio y el `.gitignore` de la raíz los excluye. El `.gitignore` del prototipo excluye `.env`.

### Paso 3.3 — Conexión con la API ✅ (sin proxy)

**Hecho, de otra forma:** el prototipo llama a la API directamente con la variable `VITE_API_BASE_URL` (`.env.example`: `http://127.0.0.1:8000/api`). Funciona porque el backend ya acepta el origen del servidor de Vite (`http://localhost:5173` y `http://127.0.0.1:5173`) en `CORS_ALLOWED_ORIGINS`. **El proxy de Vite no hace falta.**

Para correrlo: copiar `.env.example` como `.env` en `ux/prototype/cajaclara-ui/` y luego `npm install` y `npm run dev`.

> **Al publicar:** `VITE_API_BASE_URL` pasa a ser la dirección pública del backend (ej. `https://<backend>/api`), y el backend agrega la dirección pública del frontend en `CORS_ALLOWED_ORIGINS` (sección *Publicar el backend* del README).
>
> Si algún día prefieren el proxy (por ejemplo, para evitar CORS en otro puerto), se agrega `server.proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } }` en `vite.config.js` y `VITE_API_BASE_URL=/api`.

### Paso 3.4 — Servicio de API y login ✅

**Hecho** (commit `1b64e4b`), con archivos propios de `ux` en vez del `api.js` de ejemplo:

| Archivo de `ux`                 | Qué hace                                                                                                  |
| :------------------------------ | :-------------------------------------------------------------------------------------------------------- |
| `src/services/apiClient.js`     | `apiRequest()`: agrega el token, renueva el `access` una sola vez si llega un `401` y guarda los tokens.  |
| `src/services/authService.js`   | `login`, `refreshToken`, `logout` y `getProfile` contra `/api/auth/...`.                                  |
| `src/composables/useAuth.js`    | Estado del usuario y aviso de sesión expirada (`auth:session-expired`).                                   |
| `src/views/LoginView.vue`       | Pantalla de login.                                                                                        |
| `src/router/index.js`           | `beforeEach`: las rutas con `requiresAuth` mandan a `/login` si no hay sesión.                            |
| `AppHeader.vue`                 | Botón **Cerrar sesión**.                                                                                  |

**Para conectar las pantallas (3.5), usar el mismo `apiRequest()`** con `authenticated: true, retryAfterRefresh: true`. Por ejemplo:

```js
import { apiRequest } from '@/services/apiClient'

const resumen = await apiRequest('/finanzas/resumen-mensual/?fecha_inicio=2022-08-01&fecha_fin=2022-08-31', {
  authenticated: true,
  retryAfterRefresh: true,
})
```

Las rutas y parámetros de cada consulta están en la sección 4.3 de `API_DOCUMENTACION.md` (`apiService`): sirven de guía aunque no se use ese archivo.

> `apiRequest()` lee las respuestas como JSON. Para **Exportar a Excel** (3.9) hace falta una función aparte que descargue el archivo con el token; ver 3.9.

### Paso 3.5 — Conectar cada pantalla

Reemplazar los mocks por llamadas a la API. Usar los **nombres de campo de la API** (iguales a las columnas de la base):

| Pantalla (ruta)                | Mock actual              | Endpoint(s) de la API                                                                                                                                   |
| :----------------------------- | :----------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Dashboard (`/`)                | `dashboardMock.js`       | `resumen-mensual`, `resumen-agrupado?agrupacion=semanas_mes`, `alertas-cobro?page_size=5` (cobros prioritarios), `operaciones?page_size=5` (operaciones recientes), `productos?ordering=-total_vendido&page_size=4` |
| Compras y ventas (`/operaciones`) | `operationsMock.js`   | `operaciones/?mes=AAAA-MM` (ventas y gastos juntos, con filtros `tipo`, `estado`, `search` y su `resumen`), `facturas/{id_factura}/` (detalle), `opciones/clientes/` y `opciones/productos/` (selectores de los formularios) |
| Cuentas por cobrar (`/cobros`) | `receivablesMock.js`     | `cuentas-por-cobrar/` (lista + `resumen`), `alertas-cobro/` (prioridad y mensaje de recordatorio), `cuentas-por-cobrar/{id_cuenta}/pagar/`               |
| Resumen mensual (`/resumen`)   | `monthlySummaryMock.js`  | `resumen-mensual?fecha_inicio=…&fecha_fin=…` (incluye `por_tipo_compra`), `resumen-agrupado?agrupacion=semanas_mes`, `productos?ordering=-total_vendido`, `facturas?ordering=-total_venta&page_size=1` (venta más grande), `clientes?ordering=-total_deuda&page_size=1` (quién debe más) |

Cambios de nombre más importantes respecto de los mocks:

| En el mock                            | En la API                                                      |
| :------------------------------------ | :------------------------------------------------------------- |
| `invoiceId`                           | `id_factura`                                                   |
| `id` de cliente (`cli-001`)           | `id_cliente` (número)                                          |
| `id` de producto (`prod-001`)         | `id_producto` (ej. `P100055`)                                  |
| `clientName`                          | `cliente_nombre`                                               |
| `contact` / `phone`                   | `cliente_contacto` / `contacto`                                |
| `dueDate`                             | `fecha_vencimiento`                                            |
| `issuedDate`                          | `fecha_emision` (en cuentas) / `fecha` (en ventas)             |
| `amount`                              | `monto` (cuentas y gastos) / `total_venta` (ventas)            |
| `status` de una cuenta                | `estado_actual` (`PENDIENTE`, `VENCIDA`, `PAGADA`)             |
| Canal "Física" / "En línea"           | `tipo_compra`: `"Física"` / `"En Línea"` (L mayúscula)         |
| `unitPrice`                           | `precio_venta` (de cada línea; no hay precio de catálogo)      |
| Gráfico semanal `semana`, `ventas`, `gastos` | `periodos[].rango`, `.flujo_caja.entradas.total`, `.flujo_caja.salidas.total` |

> Los montos llegan como **números enteros** (pesos chilenos): no hace falta `parseFloat`. Para mostrarlos: `monto.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' })`.
>
> La tabla completa campo por campo está en la **Parte 5 de `API_DOCUMENTACION.md`**.

### Paso 3.6 — Ajustar los formularios a lo que la base permite

> El detalle de cada formulario (campos, obligatorios, formato y de dónde sale cada lista desplegable) está en el **endpoint 16 de `API_DOCUMENTACION.md`**. El precio sugerido de un producto sale de `opciones/productos/` (`ultimo_precio_venta`).

La base del equipo de datos **no tiene** algunas cosas que el prototipo muestra. Hay que ajustar los formularios así:

| Formulario                                 | Qué cambiar                                                                                                                                                                         |
| :----------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nueva venta** (`NewOperationModal`, `OperationFormModal`) | El **cliente es obligatorio** siempre (también al contado). Cada producto se envía como `{ id_producto, cantidad }`; `precio_venta` y `costo_venta` son opcionales (si no se envían, se usan los de la última venta). Si es fiado: `por_cobrar: true` + `fecha_vencimiento`. |
| **Compra / gasto**                         | Solo existe **gasto en insumos**: `{ id_producto, monto, fecha? }`. Quitar del formulario **categorías de gasto** (arriendo, flete, servicios…), **proveedor** y **descripción**: no existen en la base. |
| **Registrar pago** (`PaymentModal`)        | `POST cuentas-por-cobrar/{id_cuenta}/pagar/` con `{ fecha_pago? }`. Pago completo, sin abonos.                                                                                     |
| **Nuevo cliente**                          | `nombre` y `contacto` obligatorios; el contacto no se puede repetir (la API responde `400`).                                                                                        |
| **Anular venta**                           | **Quitar el botón**: la base no permite anular ni borrar.                                                                                                                           |

Errores que devuelve la API al registrar (mostrarlos en un toast):

- `400` con `{"campo": ["mensaje"]}` → error en un campo del formulario.
- `400` con `{"error": "mensaje"}` → regla del negocio (ej. *"La cuenta ya está pagada"*).

### Paso 3.7 — Estados de carga, error y vacío

En cada vista:

- **Cargando:** mostrar un indicador mientras llegan los datos.
- **Error:** mensaje + botón *Reintentar*.
- **Vacío:** mensaje claro cuando el período no tiene movimientos (por ejemplo, *"No hay movimientos en este período"*).

### Paso 3.8 — Elegir el período inicial (importante con Neon)

En Neon las ventas llegan hasta **18/11/2022**. Si el dashboard parte en "el mes actual", con Neon aparecerá vacío. Para que funcione con ambas bases:

1. Llamar primero a `GET /api/finanzas/opciones-filtros/`.
2. Usar `rango_fechas_disponible.max` como mes inicial del dashboard y del resumen mensual.
3. Dejar el selector de período para que el usuario cambie de mes.

### Paso 3.9 — Botón Exportar a Excel

Un enlace `<a href>` directo **no funciona**, porque la descarga necesita el token. Y `apiRequest()` no sirve tal cual, porque la respuesta es un archivo y no JSON. Se descarga con `fetch` y el token guardado:

```js
import { tokenStore } from '@/services/apiClient'

export async function descargarExcel(filtros) {
  const url = `${import.meta.env.VITE_API_BASE_URL}/finanzas/exportar-excel/?${new URLSearchParams(filtros)}`
  const respuesta = await fetch(url, { headers: { Authorization: `Bearer ${tokenStore.access}` } })
  if (!respuesta.ok) throw new Error('No se pudo descargar el Excel.')
  const enlace = document.createElement('a')
  enlace.href = URL.createObjectURL(await respuesta.blob())
  enlace.download = 'cajaclara_ventas.xlsx'
  enlace.click()
  URL.revokeObjectURL(enlace.href)
}
```

> Si el `access` venció (`401`), llamar antes a `refreshToken()` de `authService.js` y reintentar.

### ✅ Checklist del equipo de Frontend

- [ ] Backend corriendo en local (3.1).
- [x] `node_modules/` y `dist/` fuera del repositorio (3.2).
- [x] Conexión con la API por `VITE_API_BASE_URL`, sin proxy (3.3).
- [x] Cliente de API, pantalla de login y protección de rutas (3.4). Probado contra el backend.
- [ ] Las 4 pantallas sin mocks (3.5). Dashboard y Resumen ✅ en `integration/ux-backend`; faltan Operaciones y Cobros.
- [ ] Formularios ajustados: cliente obligatorio, gasto = producto + monto, sin anular (3.6).
- [ ] Estados de carga, error y vacío (3.7).
- [x] Período inicial según `rango_fechas_disponible.max` (3.8). Hecho en `integration/ux-backend`.
- [ ] Exportar a Excel descargando con el token (3.9).

---

## 🤖 Parte 3B — Prompt para la IA del equipo UX

Para que el asistente de IA del equipo UX (Claude, Copilot, Cursor u otro) tenga todo el contexto y conecte el prototipo con el backend sin inventar campos. **Copiar el bloque completo** y pegarlo como primer mensaje, con el repositorio abierto en la rama `integration/ux-backend`.

```text
Eres el asistente del equipo UX/Frontend del proyecto Caja Clara (Bootcamp Talento Digital):
una app de flujo de caja para pymes, montos en pesos chilenos (CLP). Tu tarea es conectar el
prototipo Vue con la API del backend, reemplazando los datos simulados (mocks) por datos reales.

## 1. El repositorio y sus ramas
- Repositorio: RonnieRBG/td_cajaclara. Hay 3 equipos y cada uno trabaja en su rama:
  - `datos`: base PostgreSQL en Neon (6 tablas + vistas para Power BI). La define el equipo de datos.
  - `backend`: API Django REST que usa EXACTAMENTE el esquema de datos.
  - `ux`: este prototipo, en `ux/prototype/cajaclara-ui` (Vue 3 + Vue Router + Vite).
- La regla del proyecto es: datos define las tablas, backend se adapta a datos, y UX se adapta a los dos.

## 2. Reglas para ti
- Trabaja SOLO en la rama de integración del equipo UX, `integration/ux-backend` (o en `ux` si así
  te lo piden), y SOLO dentro de `ux/` (sobre todo `ux/prototype/cajaclara-ui/src`).
- Para traer novedades del backend: `git merge origin/backend` (no cambies sus archivos).
- NO modifiques, ni hagas commits o push en, las ramas `backend`, `datos` ni `main`.
- En la raíz de la rama `ux` hay una copia ANTIGUA de Django (`manage.py`, `cajaclara/`, `finanzas/`).
  NO la uses ni la modifiques: está desactualizada. El backend real está en la rama `backend`.
- `ux/INTEGRACION-BACKEND.md` está DESACTUALIZADO (habla de `Movimiento`, `Categoria` y de un solo
  endpoint). No lo uses como referencia. Al final, actualízalo para que apunte a los documentos del punto 3.
- No inventes campos ni endpoints. Si una pantalla necesita algo que la API no entrega, NO lo simules:
  anótalo en una lista "Pedidos al backend" y sigue con lo demás.
- Haz commits chicos y descriptivos en español (una pantalla o pieza por commit).

## 3. Fuentes de verdad (léelas antes de escribir código)
Están en la rama `backend`. Léelas sin cambiar de rama:
    git fetch origin
    git show origin/backend:ACOPLAMIENTO.md        # qué hace cada equipo; Parte 3 = tus pasos
    git show origin/backend:API_DOCUMENTACION.md   # contrato de la API, endpoint por endpoint
En API_DOCUMENTACION.md, lo más importante para ti:
  - Parte 3: cada endpoint con parámetros y respuesta de ejemplo (endpoints 1 a 16).
  - Endpoint 16: contrato de los formularios (campos, obligatorios, reglas).
  - Parte 5: tabla "qué campo de la API alimenta cada componente".
En ACOPLAMIENTO.md: paso 3.5 (qué endpoint usa cada pantalla y la tabla mock → API) y pasos 3.6 a 3.9.
Si algo de este prompt contradice esos documentos, mandan los documentos.

## 4. Levantar el backend en local (sin tocar la rama ux)
En una carpeta APARTE (no dentro del repo de ux):
    git clone -b backend https://github.com/RonnieRBG/td_cajaclara.git cajaclara_backend
    cd cajaclara_backend
    python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py importar_csv --fechas-originales     # datos 2010–2022, iguales a Neon
    python manage.py createsuperuser
    python manage.py runserver                            # http://127.0.0.1:8000/api/
Con `--fechas-originales` los números coinciden con la documentación y con Neon. Sin esa opción,
las fechas se mueven al presente (útil para ver "el mes actual" con datos).
Catálogo de endpoints: http://127.0.0.1:8000/api/

## 5. Lo que YA existe en ux (reutilízalo, no lo reescribas)
- `src/services/apiClient.js`: `apiRequest(path, { authenticated, retryAfterRefresh, method, body })`.
  Agrega el token, lo renueva solo si llega un 401 y lanza `ApiError` (con `status` y `validationErrors`).
- `src/services/authService.js`, `src/composables/useAuth.js`, `src/views/LoginView.vue` y el
  `beforeEach` de `src/router/index.js`: el login ya funciona y se probó contra el backend.
- `src/utils/formatters.js`: `formatCLP` y `formatDate` (espera fechas `AAAA-MM-DD`).
- `.env.example`: `VITE_API_BASE_URL=http://127.0.0.1:8000/api` (cópialo a `.env`). No hace falta
  proxy de Vite: el backend ya acepta CORS desde localhost:5173 y 127.0.0.1:5173.
Como `VITE_API_BASE_URL` ya termina en `/api`, las rutas se piden así:
    apiRequest('/finanzas/resumen-mensual/?fecha_inicio=2022-08-01&fecha_fin=2022-08-31',
               { authenticated: true, retryAfterRefresh: true })

## 6. Cómo hacerlo (en este orden)
1. Crea `src/services/finanzasService.js` con una función por endpoint (todas con
   `authenticated: true, retryAfterRefresh: true`), armando los parámetros con URLSearchParams.
2. Crea adaptadores (por ejemplo `src/services/adapters.js`) que conviertan la respuesta de la API
   a la forma que ya esperan los componentes. Así los componentes cambian lo mínimo.
   La tabla mock → API está en ACOPLAMIENTO.md, paso 3.5.
3. Conecta cada pantalla y borra su import de `@/data/*Mock`:
   - Dashboard (`/`): opciones-filtros/ (para el mes inicial), resumen-mensual/,
     resumen-agrupado/?agrupacion=semanas_mes, alertas-cobro/?page_size=5 (cobros prioritarios),
     operaciones/?page_size=5 (operaciones recientes), productos/?ordering=-total_vendido&page_size=4,
     cuentas-por-cobrar/?page_size=1 (solo su "resumen").
   - Compras y ventas (`/operaciones`): operaciones/?mes=AAAA-MM (filtros tipo, estado, search y su
     "resumen"); detalle con facturas/{id_factura}/.
   - Cuentas por cobrar (`/cobros`): cuentas-por-cobrar/ (lista + "resumen"), alertas-cobro/,
     pagar con POST cuentas-por-cobrar/{id_cuenta}/pagar/.
   - Resumen mensual (`/resumen`): resumen-mensual/ (incluye por_tipo_compra),
     resumen-agrupado/?agrupacion=semanas_mes, productos/?ordering=-total_vendido,
     facturas/?ordering=-total_venta&page_size=1, clientes/?ordering=-total_deuda&page_size=1.
4. Formularios (endpoint 16 de API_DOCUMENTACION.md):
   - Nueva venta: POST facturas/ con { id_cliente, items: [{ id_producto, cantidad, precio_venta?,
     costo_venta? }], tipo_compra, por_cobrar, fecha_vencimiento? }. El cliente es OBLIGATORIO
     siempre. Selectores: opciones/clientes/?search= y opciones/productos/?search= (este trae
     ultimo_precio_venta y ultimo_costo_venta como precio sugerido; si vienen null, pide precio y costo).
   - Gasto: POST gastos/ con { id_producto, monto, fecha? }. Quita del formulario categoría de
     gasto, proveedor y descripción: no existen en la base.
   - Cliente: POST clientes/ con { nombre, contacto } (contacto único).
   - Pago: POST cuentas-por-cobrar/{id_cuenta}/pagar/ con { fecha_pago? }. Pago completo, sin abonos.
   - Quita el botón "Anular venta": la base no permite anular ni borrar.
   - Errores: 400 con { campo: [mensaje] } → bajo el campo (ApiError.validationErrors);
     400 con { error: mensaje } → toast.
5. Estados de carga, error (con "Reintentar") y vacío en cada vista. Nunca muestres mocks como si
   fueran datos reales.
6. Período inicial: pide primero opciones-filtros/ y usa rango_fechas_disponible.max como mes inicial
   (en Neon los datos terminan en noviembre de 2022; "el mes actual" saldría vacío).
7. Exportar a Excel: GET finanzas/exportar-excel/ devuelve un archivo, no JSON, así que no sirve
   apiRequest(). Descárgalo con fetch + `Authorization: Bearer ${tokenStore.access}` (ejemplo en
   ACOPLAMIENTO.md, paso 3.9).
8. Actualiza `ux/INTEGRACION-BACKEND.md` y el README del prototipo con cómo correr ambos proyectos.

## 7. Reglas de datos (no las cambies)
- Los nombres de campo son los de la base: id_factura, id_cliente (número), id_producto (ej. P100055),
  id_cuenta, id_gasto, precio_venta, costo_venta, fecha_vencimiento, etc.
- Montos: enteros en CLP (ya son números: no uses parseFloat). Muéstralos con formatCLP.
- Fechas: "AAAA-MM-DD", sin hora. La base no guarda hora: no la muestres.
- tipo_compra: "Física" o "En Línea" (con tilde y L mayúscula).
- Cuentas por cobrar: para mostrar usa estado_actual (PENDIENTE, VENCIDA, PAGADA), no estado.
- Ventas: estado_pago es PAGADO o PENDIENTE; por_cobrar=true significa venta al fiado.
- Listados paginados: { count, next, previous, results } y a veces "resumen". Usa page y page_size.

## 8. Cómo verificar antes de dar por terminado
- `npm run build` sin errores en ux/prototype/cajaclara-ui.
- Con el backend importado con --fechas-originales, en agosto de 2022:
  saldo del período (flujo_caja.saldo) = -164.348; ventas = 16.057; gastos = 188.863.
- Registra un cliente, una venta al fiado, págala y registra un gasto: todo debe seguir ahí después
  de recargar la página.
- Cierra sesión: las rutas protegidas deben mandar a /login.
- Revisa la consola del navegador: sin errores de CORS ni 401 repetidos.

## 9. Qué entregar
- Commits en `integration/ux-backend` (nunca en backend, datos ni main).
- Un resumen corto con: pantallas conectadas, cambios en formularios, mocks eliminados y la lista
  "Pedidos al backend" (si quedó algo que la API no entrega).
```

> Si la IA encuentra algo que la API no entrega, la lista **"Pedidos al backend"** es la que hay que traer al equipo backend: se agrega en la rama `backend` y se actualiza `API_DOCUMENTACION.md`.

---

## 🤝 Parte 4 — Prueba de integración (todos juntos)

Con el backend conectado a **Neon** y el frontend corriendo (`npm run dev` → `http://localhost:5173`), hacer esta prueba completa. Ideal en una llamada con los tres equipos.

| #  | Acción en la app                                        | Resultado esperado                                                                                     | Quién revisa |
| :- | :------------------------------------------------------ | :----------------------------------------------------------------------------------------------------- | :----------- |
| 1  | Entrar con el usuario de prueba                         | Llega al dashboard. Con clave mala: mensaje de error.                                                  | Frontend     |
| 2  | Ver el dashboard de agosto 2022                         | Saldo del período = **-$164.348** (igual que `vw_flujo_caja_mensual`)                                  | Datos        |
| 3  | Ir a Cuentas por cobrar → filtro *Vencidas*             | **8** cuentas, total **$10.725**                                                                       | Datos        |
| 3b | Abrir `/api/finanzas/alertas-cobro/?fecha_corte=2022-09-01` | Igual que `SELECT prioridad_alerta, COUNT(*), SUM(monto) FROM vw_alertas_cobro GROUP BY 1`: 6 críticas ($7.570), 1 alta ($3.083), 1 media ($72) | Datos |
| 3c | Abrir `/api/finanzas/metricas/morosidad/` y `/metricas/ranking-productos/` | Los mismos números que las páginas 3 y 4 del tablero de Power BI                   | Datos        |
| 4  | Registrar un cliente nuevo                              | Aparece en la lista. En Neon: `SELECT * FROM cliente ORDER BY id_cliente DESC LIMIT 1;`               | Datos        |
| 5  | Registrar una venta **al fiado** para ese cliente       | En Neon aparece en `venta`, `detalle_venta` y `cuenta_por_cobrar` (estado `PENDIENTE`)                 | Datos        |
| 6  | Pagar esa cuenta                                        | Pasa a *Pagada*. En Neon: `estado = 'PAGADA'` y `fecha_pago` = hoy. El saldo del mes actual sube.      | Backend      |
| 7  | Registrar un gasto en insumos                           | Aparece en `gastos_insumo`. El saldo del mes actual baja.                                              | Backend      |
| 8  | Actualizar Power BI                                     | Las ventas, el pago y el gasto nuevos aparecen en el tablero                                           | Datos        |
| 9  | Exportar a Excel                                        | Se descarga el `.xlsx` con el detalle de ventas                                                        | Frontend     |
| 10 | Esperar a que venza el token (30 min) y seguir usando   | Sigue funcionando sin pedir login (el token se renueva solo)                                           | Frontend     |
| 11 | Cerrar sesión                                           | Vuelve al login; las rutas protegidas ya no se pueden abrir                                            | Frontend     |

> Los registros de prueba quedan en Neon (la API no puede borrarlos). Si se quiere dejar la base limpia, el equipo de datos vuelve al branch de respaldo del paso 1.5.

### Si algo falla

| Síntoma                                       | Causa probable                                            | Quién lo ve |
| :-------------------------------------------- | :-------------------------------------------------------- | :---------- |
| `verificar_esquema` muestra ✗                 | Datos cambió una tabla o columna                          | Datos + Backend |
| `permission denied for table auth_user`       | `migrate --fake-initial` no se corrió con `neondb_owner`  | Datos       |
| `relation "venta" already exists` al migrar   | Faltó `--fake-initial`                                    | Datos       |
| `SSL connection is required`                  | Falta `DB_SSLMODE=require` en el `.env`                   | Backend     |
| `401` en todas las consultas                  | No se inició sesión, o la consulta no usa `apiRequest(..., { authenticated: true })` | Frontend    |
| Error de CORS en la consola del navegador     | La dirección del frontend no está en `CORS_ALLOWED_ORIGINS` del backend, o `VITE_API_BASE_URL` apunta mal (3.3) | Backend / Frontend |
| Dashboard en cero con Neon                    | Está pidiendo el mes actual (paso 3.8)                    | Frontend    |
| Montos en `NaN` o campos vacíos               | Se usa un nombre de campo antiguo del mock (tabla del 3.5) | Frontend   |
| *"Falta configurar VITE_API_BASE_URL"*       | No se creó el `.env` del prototipo a partir de `.env.example` (3.3) | Frontend |
| `400` al registrar una venta                  | Falta `id_cliente`, o el producto nunca se vendió y no se envió `precio_venta`/`costo_venta` | Frontend |

---

## 🌐 Parte 5 — Publicar: backend + frontend en Vercel

**Vercel publica solo el frontend.** El backend Django se publica aparte (Render, Railway u otro). Sin el backend publicado, el sitio de Vercel no tiene una API a la cual conectarse: `127.0.0.1` es el computador de cada uno.

| Paso | Equipo   | Qué se hace                                                                                                   |
| :--: | :------- | :------------------------------------------------------------------------------------------------------------ |
|  1   | Datos    | Neon listo: claves nuevas, credenciales entregadas y paso 1.4 hecho.                                          |
|  2   | Backend  | Publicar el backend conectado a Neon (sección *Publicar el backend* del README) y crear los usuarios (2.4).  |
|  3   | Backend  | Agregar el dominio de Vercel en las variables del servicio del backend: `CORS_ALLOWED_ORIGINS=https://tdcajaclara-cajaclara-ui-omega.vercel.app` |
|  4   | Todos    | Pasar la integración a `main` (unir `integration/ux-backend` y la rama `backend` actual).                     |
|  5   | Frontend | En Vercel → **Settings → Environment Variables**: `VITE_API_BASE_URL=https://<dirección-del-backend>/api` y `VITE_USE_MOCKS=false`. Luego **Redeploy**. |
|  6   | Todos    | Entrar al sitio de Vercel con el usuario `demo` y repetir la prueba de la Parte 4.                            |

**Configuración del proyecto en Vercel:**

- **Root Directory:** `ux/prototype/cajaclara-ui`.
- **Rama de producción:** `main` (cuando la integración esté ahí).
- Las variables `VITE_*` se leen **al construir** el sitio: si se cambian, hay que volver a desplegar para que tomen efecto.
- Si al **recargar** una página interna (por ejemplo `/cobros`) aparece un error **404**, falta un `vercel.json` en `ux/prototype/cajaclara-ui/` que mande todas las rutas a `index.html`:

```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

> **Seguridad:** en Vercel solo van la dirección del backend y `VITE_USE_MOCKS`. Ninguna clave (ni de Neon ni de usuarios) va en las variables de Vercel: todo lo que empieza con `VITE_` queda visible en el código que descarga el navegador.

---

## 📌 Decisiones pendientes (para conversar entre los tres equipos)

- [ ] **Una regla para la fecha de corte:** las vistas de análisis de datos calculan al `2022-09-01` y la API operativa a la fecha de hoy (hoy: 6 vencidas según la vista, 8 según la API). Propuesta: lo histórico (`/metricas/`, Power BI) usa las vistas tal cual; lo operativo (`/cuentas-por-cobrar/`, `/alertas-cobro/`) usa hoy; y cada pantalla dice a qué fecha corresponde su número.
- [ ] **Fechas en Neon para la demo:** ¿se deja el período 2010–2022 (y el dashboard parte en nov. 2022) o datos desplaza las fechas al presente?
- [ ] **Gastos que no son insumos** (arriendo, flete, servicios): hoy la base no los permite. Si se quieren, datos tiene que agregar una tabla o columnas y avisar al backend.
- [ ] **Anular ventas:** la base no lo permite. Si se necesita, acordar cómo marcarlo (por ejemplo, una columna `anulada` en `venta`).
- [ ] **Pagos parciales (abonos):** hoy un pago es siempre completo.
- [ ] **Dónde se publica el backend** para la presentación final (Render, Railway u otro). El frontend ya está en Vercel; el backend está preparado (sección *Publicar el backend* del README). Con eso se completan los pasos de la Parte 5.
- [ ] **Qué mes muestra la demo:** con los datos en Neon, el mes inicial es noviembre 2022, que tiene muy pocas ventas (1 venta y 102 gastos). Elegir un mes con más movimiento o desplazar las fechas.
