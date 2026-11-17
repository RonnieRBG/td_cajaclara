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

| Paso | Equipo   | Qué se hace                                                        | Depende de |
| :--: | :------- | :----------------------------------------------------------------- | :--------: |
|  1   | Datos    | Dejar Neon listo y entregar las credenciales del backend           |     —      |
|  2   | Datos    | Crear (una sola vez) las tablas de usuarios de Django en Neon      |     1      |
|  3   | Backend  | Conectar la API a Neon y comprobar el esquema                      |    1, 2    |
|  4   | Frontend | Conectar el prototipo a la API (login, lecturas y formularios)     |     3      |
|  5   | Todos    | Prueba de integración completa (checklist final)                   |  1 al 4    |

> El frontend **no necesita esperar a Neon**: puede avanzar desde el día 1 contra el backend en local con SQLite (ver 3.1).

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

### Paso 2.4 — Crear los usuarios del equipo

No hay registro público. Cada persona que use la app necesita un usuario, creado desde `/admin/` → **Usuarios** → **Agregar**, o con:

```bash
python manage.py createsuperuser
```

### Paso 2.5 — Avisar al frontend

Cuando 2.3 funcione, avisar al equipo de frontend que la API está lista y entregarles **un usuario de prueba** (no el administrador).

### Paso 2.6 — Si el equipo de datos cambia el esquema

1. Ajustar `finanzas/models.py` (`db_table`, `db_column`, tipo).
2. `python manage.py makemigrations finanzas` y, en Neon, `python manage.py migrate --fake finanzas` (la tabla ya la cambió datos).
3. Actualizar el serializer si el campo sale en la API y anotarlo en la Parte 5 de `API_DOCUMENTACION.md` para que frontend se entere.
4. `verificar_esquema` y `test`.

### ✅ Checklist del equipo de Backend

- [ ] `.env` con Neon, clave secreta y CORS (2.1).
- [ ] `verificar_esquema` y `test` sin errores (2.2).
- [ ] Saldo de agosto 2022 igual a `vw_flujo_caja_mensual` (2.3).
- [ ] Usuarios del equipo creados (2.4).
- [ ] Usuario de prueba entregado al frontend (2.5).

---

## 🎨 Parte 3 — Equipo de Frontend / UX

El prototipo (`ux/prototype/cajaclara-ui`) hoy funciona con datos simulados: `dashboardMock.js`, `operationsMock.js`, `receivablesMock.js` y `monthlySummaryMock.js`. Hay que reemplazarlos por llamadas a la API.

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

### Paso 3.2 — Limpiar la rama `ux` antes de integrar

La rama `ux` tiene subidas las carpetas `node_modules/` y `dist/`, que pesan mucho y se generan solas. Agregar en `ux/prototype/cajaclara-ui/.gitignore`:

```gitignore
node_modules/
dist/
.env
```

Y sacarlas del repositorio (quedan en el computador):

```bash
git rm -r --cached ux/prototype/cajaclara-ui/node_modules ux/prototype/cajaclara-ui/dist
```

### Paso 3.3 — Proxy de Vite

En `ux/prototype/cajaclara-ui/vite.config.js`, agregar `server.proxy` para que `/api` llegue a Django sin problemas de CORS:

```js
export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: {
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
```

### Paso 3.4 — Servicio de API y login

Crear `src/services/api.js` con el código de la **sección 4.3 de `API_DOCUMENTACION.md`** (ya trae login, renovación automática del token, `apiService` con todas las consultas y la descarga de Excel).

Luego:

1. Crear una vista de **login** (`/login`) con usuario y contraseña que llame a `authService.login(usuario, clave)`.
2. En `src/router/index.js`, agregar un `beforeEach` que mande a `/login` si `authService.estaLogueado()` es `false`.
3. Escuchar el evento `sesion-expirada` para volver al login.
4. Botón **Cerrar sesión** en `AppHeader.vue` → `authService.logout()`.

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

Usar `apiService.descargarExcel({ fecha_inicio, fecha_fin })`. Un enlace `<a href>` directo **no funciona**, porque la descarga necesita el token.

### ✅ Checklist del equipo de Frontend

- [ ] Backend corriendo en local (3.1).
- [ ] `node_modules/` y `dist/` fuera del repositorio (3.2).
- [ ] Proxy de Vite (3.3).
- [ ] `api.js`, pantalla de login y protección de rutas (3.4).
- [ ] Las 4 pantallas sin mocks (3.5).
- [ ] Formularios ajustados: cliente obligatorio, gasto = producto + monto, sin anular (3.6).
- [ ] Estados de carga, error y vacío (3.7).
- [ ] Período inicial según `rango_fechas_disponible.max` (3.8).
- [ ] Exportar a Excel con `descargarExcel()` (3.9).

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
| `401` en todas las consultas                  | No se inició sesión o falta el encabezado `Authorization` | Frontend    |
| Error de CORS en la consola del navegador     | Falta el proxy de Vite (3.3) o el dominio en `CORS_ALLOWED_ORIGINS` | Frontend / Backend |
| Dashboard en cero con Neon                    | Está pidiendo el mes actual (paso 3.8)                    | Frontend    |
| Montos en `NaN` o campos vacíos               | Se usa un nombre de campo antiguo del mock (tabla del 3.5) | Frontend   |
| `400` al registrar una venta                  | Falta `id_cliente`, o el producto nunca se vendió y no se envió `precio_venta`/`costo_venta` | Frontend |

---

## 📌 Decisiones pendientes (para conversar entre los tres equipos)

- [ ] **Una regla para la fecha de corte:** las vistas de análisis de datos calculan al `2022-09-01` y la API operativa a la fecha de hoy (hoy: 6 vencidas según la vista, 8 según la API). Propuesta: lo histórico (`/metricas/`, Power BI) usa las vistas tal cual; lo operativo (`/cuentas-por-cobrar/`, `/alertas-cobro/`) usa hoy; y cada pantalla dice a qué fecha corresponde su número.
- [ ] **Fechas en Neon para la demo:** ¿se deja el período 2010–2022 (y el dashboard parte en nov. 2022) o datos desplaza las fechas al presente?
- [ ] **Gastos que no son insumos** (arriendo, flete, servicios): hoy la base no los permite. Si se quieren, datos tiene que agregar una tabla o columnas y avisar al backend.
- [ ] **Anular ventas:** la base no lo permite. Si se necesita, acordar cómo marcarlo (por ejemplo, una columna `anulada` en `venta`).
- [ ] **Pagos parciales (abonos):** hoy un pago es siempre completo.
- [ ] **Dónde se publica** la app (backend y frontend) para la presentación final. El backend ya está preparado para Render, Railway u otro servicio (ver *Publicar el backend* en el README); falta elegir y, con eso, poner la dirección del frontend en `CORS_ALLOWED_ORIGINS`.
