# 💰 Caja Clara

**Una herramienta para que las pymes sepan, de un vistazo, cuánta plata entra, cuánta sale y cuánto les deben.**

> Proyecto del Bootcamp **Talento Digital**. Este repositorio contiene el **backend** (el "motor" que guarda los datos y hace los cálculos). La documentación técnica de cada endpoint está en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md).
>
> 🔗 **¿Cómo se juntan datos, backend y frontend?** Los pasos de cada equipo están en [`ACOPLAMIENTO.md`](./ACOPLAMIENTO.md).
>
> 🎨 El frontend Vue 3 se mantiene en [`ux/prototype/cajaclara-ui/`](./ux/prototype/cajaclara-ui/) y su estado de diseño está en [`ux/README.md`](./ux/README.md), [`ux/INTEGRACION-BACKEND.md`](./ux/INTEGRACION-BACKEND.md) y el [README técnico de Vue](./ux/prototype/cajaclara-ui/README.md). Login JWT, rutas protegidas y módulos financieros (Dashboard, Resumen, Operaciones y Cuentas por cobrar) están integrados con selección explícita entre mocks y API mediante `VITE_USE_MOCKS`.

---

## 🤔 ¿Qué problema resuelve?

Muchos negocios pequeños venden bien, pero igual les falta dinero a fin de mes. ¿Por qué? Porque no tienen claro:

- **Cuánto ganan de verdad**: no es lo mismo vender que ganar; hay que restar lo que cuesta cada producto.
- **Cuánto les deben**: ventas hechas que todavía no se cobran.
- **Cómo van en el tiempo**: si este mes fue mejor o peor que el anterior.

Caja Clara junta toda esa información y la entrega ordenada, lista para mostrarse en un panel (dashboard).

---

## ⚙️ ¿Cómo funciona?

Piensa en Caja Clara como una cadena de tres piezas:

```text
  📂 Datos del negocio  ──►  🧠 Backend (este repo)  ──►  🖥️ Pantalla (frontend)
  ventas, clientes,         guarda, calcula y           muestra gráficos,
  productos, gastos         responde preguntas          tarjetas y tablas
```

1. **Los datos entran.** Usamos el set de un supermercado que preparó el equipo de datos: unas 100 mil ventas entre 2010 y 2022, 2 mil clientes, 7 mil productos, 20 mil gastos y 15 mil cuentas por cobrar. En producción están en la base **Neon** del equipo de datos; para trabajar en local, la carpeta `data/` tiene los mismos CSV (`Etapa_4_Carga_y_Nube/datos_procesados/` de la rama `datos`).
2. **El backend los ordena y calcula.** Cada venta se conecta con su cliente, sus productos y su costo. Con eso el sistema calcula ingresos, costos, utilidad, margen y deudas pendientes.
3. **El frontend pregunta y muestra.** La pantalla le hace "preguntas" al backend (por ejemplo, _"¿cuánto vendimos en 2012 en la tienda física?"_) y recibe la respuesta lista para dibujar.

### ¿Qué información guarda?

El backend usa **las mismas 6 tablas que definió el equipo de datos** (`schema_postgresql.sql` de la rama `datos`), con los mismos nombres de tabla y de columna, sin agregar nada. La API también devuelve los campos con esos nombres (`id_factura`, `id_cliente`, `precio_venta`…).

| Tabla                  | En palabras simples                                               |
| :--------------------- | :---------------------------------------------------------------- |
| **`cliente`**          | Quién compra: nombre y contacto.                                  |
| **`producto`**         | Qué se vende y su categoría.                                      |
| **`venta`**            | Cada factura: fecha, cliente, si fue en tienda física o en línea y si fue a crédito. |
| **`detalle_venta`**    | Qué productos iban en cada factura, en qué cantidad, a qué precio y con qué costo. |
| **`cuenta_por_cobrar`**| Una por cada venta a crédito: monto, fecha límite, estado (pendiente, vencida o pagada) y fecha de pago. |
| **`gastos_insumo`**    | Compras de productos para reponer: producto, fecha y monto.       |

Los montos son enteros (pesos chilenos) y las fechas no llevan hora.

### ¿Qué puede responder hoy?

- 📊 **Resumen financiero**: ventas, costos, utilidad y margen, y el **flujo de caja** (dinero que entró por ventas al contado y cobros, menos gastos en insumos), filtrando por fechas y por canal (física o en línea). Es el mismo cálculo que la vista `vw_flujo_caja_mensual` del equipo de datos.
- ✍️ **Registrar datos**: ventas al contado o a crédito, pagos de deudas (y deshacerlos), gastos en insumos y clientes.
- 📈 **Evolución en el tiempo**: los mismos números agrupados por día, semana, mes, trimestre o año, ideal para gráficos.
- 🏆 **Productos más vendidos**: unidades e ingresos por producto en cualquier período.
- 🔔 **Alertas de cobro**: cuentas vencidas o que vencen en 7 y 15 días, con prioridad y un mensaje de recordatorio. Misma lógica que la vista `vw_alertas_cobro` del equipo de datos, calculada a la fecha de hoy.
- 📐 **Métricas del equipo de datos**: margen por producto y categoría, ventas por categoría y mes, deuda por cliente, morosidad, ranking de productos y sustentabilidad. La API lee sus vistas SQL sin recalcular, así la app y Power BI muestran los mismos números.
- 🔀 **Operaciones**: ventas y gastos en una sola lista por mes, con búsqueda y totales.
- 🧾 **Listados con búsqueda**: clientes, productos, facturas, ventas, gastos y deudas (incluye filtro de deudas vencidas).
- 📥 **Exportar a Excel**: descarga del resumen en una planilla.
- 🎛️ **Opciones para filtros**: categorías, canales y el rango de fechas disponible, para armar los menús de la pantalla.

> El detalle de cada consulta (rutas, parámetros y ejemplos de respuesta) está en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md).

---

## 🚀 Probarlo en tu computador

Necesitas **Python 3.10 o superior**. Son seis pasos:

```bash
python -m venv venv                 # 1. Crear un entorno aislado
venv\Scripts\activate               # 2. Activarlo (en Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt     # 3. Instalar lo necesario
python manage.py migrate            # 4. Crear la base de datos local (las mismas 6 tablas)
python manage.py importar_csv       # 5. Cargar los CSV del equipo de datos
python manage.py createsuperuser    # 6. Crear tu usuario para iniciar sesión
```

Luego enciende el servidor con `python manage.py runserver` y abre **http://127.0.0.1:8000/api/** en el navegador. Verás el catálogo de consultas disponibles.

> 🔐 **La API pide iniciar sesión.** Para ver los datos en el navegador, entra primero a **http://127.0.0.1:8000/admin/** con el usuario del paso 6. El frontend inicia sesión con `/api/auth/login/` (detalles en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md)).
>
> ⚙️ **Configuración opcional:** copia `.env.example` como `.env` para cambiar la base de datos, la clave secreta o los dominios permitidos. Sin `.env`, el proyecto arranca en modo desarrollo con SQLite.
>
> 🗄️ **Conectarse a Neon (la base del equipo de datos):** completa las variables `DB_*` del `.env` con el usuario `cajaclara_app_rw` y `DB_SSLMODE=require`. La primera vez, el equipo de datos corre `python manage.py migrate --fake-initial` con el usuario administrador (crea las tablas de usuarios y login sin tocar las suyas). Para revisar que todo calza: `python manage.py verificar_esquema`. Detalle en la Parte 1 de [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md).
>
> ♻️ **Si ya tenías un `db.sqlite3` de antes** (con tablas `finanzas_*`), bórralo y repite los pasos 4 a 6: las tablas cambiaron para calzar con el esquema del equipo de datos.

> La carga de datos puede tardar un par de minutos, porque son más de 240 mil registros.
>
> Los CSV terminan en noviembre de 2022. Al importarlos, las fechas se desplazan para que la última venta quede en la semana actual y el dashboard muestre datos "de hoy". Para conservar las fechas originales usa `python manage.py importar_csv --fechas-originales`.

---

## ✅ Estado actual

| Pieza                                                            | Estado                               |
| :--------------------------------------------------------------- | :----------------------------------- |
| Modelo de datos igual al esquema del equipo de datos (Neon)      | ✅ Listo                             |
| Carga automática de los CSV                                      | ✅ Listo                             |
| Consultas de resumen, evolución y listados                       | ✅ Listo                             |
| Exportación a Excel                                              | ✅ Listo                             |
| Conexión con cualquier base de datos (SQLite, PostgreSQL, MySQL) | ✅ Listo                             |
| Conexión con el frontend                                         | ✅ Listo (JWT, Dashboard, Resumen, Operaciones y Cobros conectados; exportación Excel y selección entre mocks y API vía `VITE_USE_MOCKS`; ver [`ux/INTEGRACION-BACKEND.md`](./ux/INTEGRACION-BACKEND.md)) |
| Usuarios, login (JWT) y configuración segura con `.env`          | ✅ Listo                             |
| Registrar ventas, pagos y gastos desde la API                    | ✅ Listo                             |
| Flujo de caja (entradas, salidas y saldo)                        | ✅ Listo                             |
| Listo para publicar (`gunicorn`, `whitenoise`, `build.sh`, `Procfile`) | ✅ Publicado en Render (`cajaclara-api.onrender.com`) |
| Pruebas automáticas en GitHub (cada push a `backend`)            | ✅ Listo                             |
| Pruebas automáticas                                              | 🟡 Login, registros, flujo de caja, semanas, productos, esquema, importación, alertas, métricas y operaciones (51 pruebas) |

---

## 📋 Lo que falta, equipo por equipo

### 🗄️ Equipo de Base de Datos

- [x] **Base de producción**: Neon (PostgreSQL), con el esquema, los datos, los roles y las vistas de las Etapas 4 a 6.
- [ ] **Entregar al equipo backend** las credenciales de `cajaclara_app_rw` por un canal seguro.
- [ ] **Una sola vez**, con `neondb_owner`: `python manage.py migrate --fake-initial` y `python manage.py createsuperuser` (crea las tablas de usuarios y login de Django sin tocar las 6 tablas).
- [ ] **Avisar al equipo backend antes de cambiar una tabla o columna**: el backend usa exactamente el esquema de `schema_postgresql.sql`. `python manage.py verificar_esquema` muestra si algo dejó de calzar.
- [ ] **Fechas de la demo**: en Neon los datos llegan hasta noviembre de 2022, así que "el mes actual" del dashboard sale vacío (ver P13 en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md)).
- [ ] **Revisar la caída de ventas en 2021-2022**: de ~16 mil ventas en 2019 se pasa a 241 en 2022 (en noviembre de 2022 hay una sola), mientras los gastos se mantienen en ~1.500 al año. Por eso el mes actual del dashboard muestra muy pocas ventas y los gastos superan a las ventas.

### 🎨 Equipo de Frontend / UX

- [x] **Conectar las vistas financieras a los endpoints confirmados**: Dashboard, Operaciones, Cobros y Resumen conectados con selección explícita mediante `VITE_USE_MOCKS`. Detalle en [`ux/INTEGRACION-BACKEND.md`](./ux/INTEGRACION-BACKEND.md).
- [x] **Gráfico semanal y formularios financieros**: parámetros, respuestas y estados de error validados con contratos reales de venta, gasto y pago.
- [x] **Mostrar los montos en pesos chilenos** (ej.: `$1.250.000` sin decimales).
- [x] **Usar los nombres de campo del esquema de datos** (`id_factura`, `id_cliente`, `id_producto`, `precio_venta`, `tipo_compra: "Física" / "En Línea"`).
- [x] **Formularios integrados**: venta con cliente (`id_cliente`), gasto asociado a insumo/producto (`id_producto` + `monto`) y alta de cliente con feedback de error.
- [x] **Estados de carga, error y vacío**: implementados en todas las vistas con botón de reintento.
- [x] **Pantalla de login JWT y rutas protegidas**: login, refresh, logout y perfil con persistencia en cliente.
- [x] **Conectar el botón "Exportar a Excel"**: descarga de archivo `.xlsx` autenticada con Bearer token y filtros activos del periodo.
- [ ] **Sincronización automática entre vistas**: actualización reactiva sin requerir navegación o nueva carga.

### 🧠 Equipo de Backend

- [x] **Login y usuarios**: la API exige iniciar sesión con JWT (`/api/auth/login/`, `refresh/`, `logout/` y `perfil/`), con límite de intentos.
- [x] **Seguridad**: clave secreta, modo depuración, dominios y CORS se configuran en `.env` (ver `.env.example`); `.env` está en el `.gitignore`.
- [x] **Preparado para publicar**: `gunicorn` (servidor), `whitenoise` (estáticos del `/admin/`), `build.sh`, `Procfile` y redirección a HTTPS. Ver [Publicar el backend](#-publicar-el-backend).
- [x] **Pruebas en GitHub**: `.github/workflows/pruebas-backend.yml` corre las pruebas en SQLite y PostgreSQL, y revisa la configuración de producción, en cada push o pull request a `backend`.
- [x] **Publicado en Render** (17/11/2026): **`https://cajaclara-api.onrender.com/api`**, conectado a Neon, desde la rama `backend`. Cada push a `backend` lo vuelve a publicar.
- [ ] **Usuarios en producción**: crear el administrador y el usuario `demo` cuando el equipo de datos haga el paso 1.4 de [`ACOPLAMIENTO.md`](./ACOPLAMIENTO.md).
- [x] **Hora de Chile**: el sistema ahora usa `America/Santiago`, así los cortes de día y de mes calzan.
- [x] **Completar dependencias**: `pandas` y `openpyxl` ya están en `requirements.txt`.
- [ ] **Completar las pruebas automáticas**: ya hay 51 (login, registro de ventas, pagos, gastos, flujo de caja, agrupación semanal, productos más vendidos, esquema de datos, importación, alertas de cobro, métricas y operaciones). Faltan más de listados y filtros. Se ejecutan con `python manage.py test`.
- [x] **Registrar datos nuevos**: ventas (contado y crédito), pagos, gastos y clientes con `POST` (ver el endpoint 11 en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md)).
- [x] **Modelo igual al del equipo de datos**: mismas tablas, columnas y tipos que `schema_postgresql.sql`; se probó contra ese esquema en PostgreSQL con el usuario `cajaclara_app_rw`, y el flujo de caja coincide con `vw_flujo_caja_mensual`.
- [x] **Alertas de cobro (Tarea 29 de datos)**: `/alertas-cobro/`, comparado campo por campo con `vw_alertas_cobro`.
- [x] **Métricas en la plataforma (Tarea 30 de datos)**: `/metricas/…` lee las 7 vistas de la Etapa 5.
- [x] **Lo que piden las pantallas de UX**: `/operaciones/` (ventas y gastos en una lista), ventas por canal en el resumen, orden por total de venta y por deuda, y listas livianas para los selectores con el último precio de cada producto (`/opciones/…`).
- [x] **Contrato de los formularios (Tareas 34 a 36 de datos)**: campos, obligatorios y validaciones documentados en el endpoint 16 de [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md).
- [x] **Lo que pide el dashboard**: agrupación semanal (`semanal` y `semanas_mes`) y productos más vendidos (`/productos/?ordering=-total_vendido`, con unidades e ingresos por período).
- [x] **Flujo de caja como en el diseño**: `flujo_caja` en los resúmenes = ventas al contado + cobros − gastos en insumos.

### 🤝 Decisiones que tomamos entre todos

- [x] **Base de datos**: Neon (PostgreSQL) del equipo de datos. El backend se adapta a su esquema, no al revés.
- [ ] ¿Qué servicio usaremos para publicar la app?
- [x] ¿Cómo se marca una deuda como **vencida**? El equipo de datos la guarda como `VENCIDA`; además, la API muestra como vencida (`estado_actual`) toda cuenta pendiente cuya fecha límite ya pasó.
- [x] **Lo que no existe en el esquema de datos se quitó del backend**: anular ventas, ventas sin cliente, precio de catálogo, y tipo/categoría/proveedor de los gastos. Si se necesita algo de eso, el equipo de datos agrega la columna primero.
- [ ] **Validar este supuesto**: los pagos son **completos** (una cuenta pasa de pendiente a pagada de una vez, sin abonos parciales).
- [ ] ¿El gráfico principal será semanal o mensual?
- [ ] Licencia del proyecto.
- [x] **Un solo negocio por ahora**: todos los usuarios ven los datos del mismo negocio. El login solo protege el acceso a la API.

---

## 🌐 Publicar el backend

✅ **Publicado en Render:** **`https://cajaclara-api.onrender.com/api`** (servicio `cajaclara-api`, rama `backend`). En el plan gratuito se duerme tras 15 minutos sin uso: la primera visita puede tardar cerca de un minuto.

El proyecto trae lo necesario para Render, Railway u otro servicio que ejecute Python:

| Archivo           | Para qué sirve                                                                                  |
| :---------------- | :---------------------------------------------------------------------------------------------- |
| `build.sh`        | Instala las dependencias y junta los archivos estáticos (`collectstatic`).                       |
| `Procfile`        | Comando para iniciar: `gunicorn cajaclara.wsgi` en el puerto que entrega el servicio (`$PORT`). |
| `.python-version` | Versión de Python (3.13).                                                                       |

**En el servicio:**

1. Crear un servicio web desde el repositorio, rama **`backend`**.
2. **Build command:** `./build.sh` · **Start command:** el del `Procfile` (Render y Railway lo leen solos; si no, copiarlo).
3. **Variables de entorno** (en el panel del servicio, nunca en el repositorio):

| Variable                | Valor                                                                    |
| :---------------------- | :----------------------------------------------------------------------- |
| `DJANGO_DEBUG`          | `False`                                                                  |
| `DJANGO_SECRET_KEY`     | Una clave nueva y larga (no la de desarrollo)                            |
| `DJANGO_ALLOWED_HOSTS`  | El dominio del servicio (Render y Railway lo agregan solos)              |
| `CORS_ALLOWED_ORIGINS`  | La dirección donde se publique el frontend, ej. `https://cajaclara.vercel.app` |
| `CSRF_TRUSTED_ORIGINS`  | La dirección del backend con `https://` (para entrar al `/admin/`)       |
| `DB_*` y `DB_SSLMODE`   | Los de Neon, con el usuario `cajaclara_app_rw` (ver `.env.example`)      |

4. **No hace falta correr migraciones al publicar**: en Neon las tablas de datos son del equipo de datos y las de usuarios se crean una sola vez (paso 1.4 de [`ACOPLAMIENTO.md`](./ACOPLAMIENTO.md)).
5. Probar `https://<dominio>/api/` y `https://<dominio>/admin/`.

> Con `DJANGO_DEBUG=False` el backend redirige `http` a `https`. Si el servicio ya lo hace y aparece un bucle de redirecciones, definir `DJANGO_SSL_REDIRECT=False`.
>
> HSTS (`SECURE_HSTS_SECONDS`) se deja sin activar a propósito: obliga a los navegadores a usar siempre HTTPS en ese dominio y no se puede deshacer fácilmente. Se activa cuando el dominio final esté decidido.

---

## 🔮 Mejoras futuras

### Varios negocios en el mismo sistema (multi-pyme)

Hoy Caja Clara maneja **un solo negocio**. Si más adelante cada usuario debe ver **solo los datos de su negocio**, hay que modificar la base de datos:

- [ ] **Crear la tabla `Negocio`** (nombre, RUT, dirección, etc.) y relacionar cada usuario con su negocio.
- [ ] **Agregar la columna `id_negocio`** (acordada con el equipo de datos) a `cliente`, `producto`, `venta`, `cuenta_por_cobrar` y `gastos_insumo`. `detalle_venta` la hereda a través de su venta.
- [ ] **Filtrar todas las consultas** de la API por el negocio del usuario que inició sesión, para que nadie vea datos de otro negocio.
- [ ] **Revisar los identificadores**: hoy el código de producto (ej. `P100055`) es único en todo el sistema. Con varios negocios, dos almacenes podrían usar el mismo código, así que debe ser único **por negocio**.
- [ ] **Migrar los datos actuales** con una migración que cree un negocio "por defecto" y le asigne todo lo existente.
- [ ] **Agregar pruebas** que verifiquen que un usuario no puede ver ni modificar datos de otro negocio.

---

- **Mensajes de commit claros**, por ejemplo: `feat: agregar login`, `fix: corregir cálculo de margen`, `docs: actualizar README`.

---

## 🛠️ Tecnologías

**Python** · **Django** (estructura del backend) · **Django REST Framework** (la API) · **Simple JWT** (login con tokens) · **SQLite** en desarrollo y **PostgreSQL** (Neon) en producción · **pandas** (exportación a Excel) · **gunicorn** y **whitenoise** (publicación) · **GitHub Actions** (pruebas automáticas).

---

_Hecho por el equipo de Caja Clara en el Bootcamp Talento Digital._
