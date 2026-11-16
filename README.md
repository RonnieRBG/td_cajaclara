# 💰 Caja Clara

**Una herramienta para que las pymes sepan, de un vistazo, cuánta plata entra, cuánta sale y cuánto les deben.**

> Proyecto del Bootcamp **Talento Digital**. Este repositorio contiene el **backend** (el "motor" que guarda los datos y hace los cálculos). La documentación técnica de cada endpoint está en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md).
>
> 🔗 **¿Cómo se juntan datos, backend y frontend?** Los pasos de cada equipo están en [`ACOPLAMIENTO.md`](./ACOPLAMIENTO.md).

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
| Conexión real con el frontend                                    | 🟡 Guía escrita, falta implementarla |
| Usuarios, login (JWT) y configuración segura con `.env`          | ✅ Listo                             |
| Registrar ventas, pagos y gastos desde la API                    | ✅ Listo                             |
| Flujo de caja (entradas, salidas y saldo)                        | ✅ Listo                             |
| Pruebas automáticas                                              | 🟡 Login, registros, flujo de caja, semanas, productos, esquema, importación, alertas y métricas (47 pruebas) |

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

- [ ] **Reemplazar los datos de prueba** (`dashboardMock.js`) por consultas reales al backend. La Parte 3 de [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md) trae el paso a paso, y la Parte 5 indica qué campo usar en cada tarjeta (ej.: el saldo es `flujo_caja.saldo`).
- [ ] **Conectar los formularios** de nueva venta, gasto y pago con `apiService.registrarVenta()`, `registrarGasto()` y `registrarPago()` (Parte 4.3).
- [ ] **Gráfico semanal**: el backend ya entrega las 4 semanas del mes como en el diseño (`resumen-agrupado?agrupacion=semanas_mes`) con entradas, salidas y una etiqueta corta (`"01 - 07 Oct"`). Falta conectarlo.
- [ ] **Mostrar los montos en pesos chilenos** (ej.: `$1.250.000`). La API ya los entrega como números enteros.
- [ ] **Usar los nombres de campo del esquema de datos** (`id_factura`, `id_cliente`, `id_producto`, `precio_venta`, `tipo_compra: "Física" / "En Línea"`…). La Parte 5 de [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md) trae la lista.
- [ ] **Formularios**: toda venta necesita un cliente (`id_cliente`); un gasto es siempre la compra de un producto (`id_producto` + `monto`); un cliente nuevo necesita `nombre` y `contacto`. No existe anular una venta.
- [ ] **Diseñar los estados de carga y error**: qué ve el usuario mientras cargan los datos o si el servidor no responde.
- [ ] **Pantalla de login**: la API ya exige iniciar sesión (JWT). La guía trae un `api.js` listo que guarda el token, lo renueva solo y avisa cuando la sesión expira (Parte 4.3 de [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md)). No hace falta pantalla de registro: los usuarios los crea un administrador.
- [ ] **Conectar el botón "Exportar a Excel"** con `apiService.descargarExcel()` (un enlace directo ya no sirve, porque la descarga necesita el token).

### 🧠 Equipo de Backend

- [x] **Login y usuarios**: la API exige iniciar sesión con JWT (`/api/auth/login/`, `refresh/`, `logout/` y `perfil/`), con límite de intentos.
- [x] **Seguridad**: clave secreta, modo depuración, dominios y CORS se configuran en `.env` (ver `.env.example`); `.env` está en el `.gitignore`.
- [ ] **Al publicar**: definir `DJANGO_DEBUG=False` y una `DJANGO_SECRET_KEY` propia, servir con HTTPS (y activar `SECURE_SSL_REDIRECT` y HSTS según el servidor) y configurar un servicio de correo real si se llega a enviar email.
- [x] **Hora de Chile**: el sistema ahora usa `America/Santiago`, así los cortes de día y de mes calzan.
- [x] **Completar dependencias**: `pandas` y `openpyxl` ya están en `requirements.txt`.
- [ ] **Completar las pruebas automáticas**: ya hay 47 (login, registro de ventas, pagos, gastos, flujo de caja, agrupación semanal, productos más vendidos, esquema de datos, importación, alertas de cobro y métricas). Faltan más de listados y filtros. Se ejecutan con `python manage.py test`.
- [x] **Registrar datos nuevos**: ventas (contado y crédito), pagos, gastos y clientes con `POST` (ver el endpoint 11 en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md)).
- [x] **Modelo igual al del equipo de datos**: mismas tablas, columnas y tipos que `schema_postgresql.sql`; se probó contra ese esquema en PostgreSQL con el usuario `cajaclara_app_rw`, y el flujo de caja coincide con `vw_flujo_caja_mensual`.
- [x] **Alertas de cobro (Tarea 29 de datos)**: `/alertas-cobro/`, comparado campo por campo con `vw_alertas_cobro`.
- [x] **Métricas en la plataforma (Tarea 30 de datos)**: `/metricas/…` lee las 7 vistas de la Etapa 5.
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

**Python** · **Django** (estructura del backend) · **Django REST Framework** (la API) · **Simple JWT** (login con tokens) · **SQLite** en desarrollo y **PostgreSQL** en producción · **pandas** (exportación a Excel).

---

_Hecho por el equipo de Caja Clara en el Bootcamp Talento Digital._
