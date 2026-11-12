# 💰 Caja Clara

**Una herramienta para que las pymes sepan, de un vistazo, cuánta plata entra, cuánta sale y cuánto les deben.**

> Proyecto del Bootcamp **Talento Digital**. Este repositorio contiene el **backend** (el "motor" que guarda los datos y hace los cálculos). La documentación técnica de cada endpoint está en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md).

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

1. **Los datos entran.** Hoy usamos un set de ejemplo de un supermercado: unas 100 mil ventas entre 2010 y 2022, 2 mil clientes, 7 mil productos, 20 mil gastos y 15 mil cuentas por cobrar. Están en la carpeta `data/` como archivos CSV.
2. **El backend los ordena y calcula.** Cada venta se conecta con su cliente, sus productos y su costo. Con eso el sistema calcula ingresos, costos, utilidad, margen y deudas pendientes.
3. **El frontend pregunta y muestra.** La pantalla le hace "preguntas" al backend (por ejemplo, _"¿cuánto vendimos en 2012 en la tienda física?"_) y recibe la respuesta lista para dibujar.

### ¿Qué información guarda?

| Concepto               | En palabras simples                                               |
| :--------------------- | :---------------------------------------------------------------- |
| **Clientes**           | Quién compra: nombre y teléfono.                                  |
| **Productos**          | Qué se vende, su categoría, precio y costo.                       |
| **Facturas**           | Cada venta: fecha, cliente, si fue en tienda física o en línea, si fue a crédito y si se anuló. |
| **Detalle de venta**   | Qué productos iban en cada factura, en qué cantidad y a qué precio. |
| **Cuentas por cobrar** | Una por cada venta a crédito: monto, fecha límite y si ya se pagó (pendiente, vencida o pagada). |
| **Gastos**             | Compras de productos para reponer y otros gastos (arriendo, flete, servicios…), con categoría y proveedor. |

### ¿Qué puede responder hoy?

- 📊 **Resumen financiero**: ventas, costos, utilidad y margen, y el **flujo de caja** (dinero que entró por ventas al contado y cobros, menos compras y gastos), filtrando por fechas y por canal (físico u online).
- ✍️ **Registrar datos**: ventas al contado o a crédito, pagos de deudas (y deshacerlos), anulación de ventas, compras, otros gastos y clientes.
- 📈 **Evolución en el tiempo**: los mismos números agrupados por día, mes, trimestre o año, ideal para gráficos.
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
python manage.py migrate            # 4. Crear la base de datos
python manage.py importar_csv       # 5. Cargar los datos de ejemplo
python manage.py createsuperuser    # 6. Crear tu usuario para iniciar sesión
```

Luego enciende el servidor con `python manage.py runserver` y abre **http://127.0.0.1:8000/api/** en el navegador. Verás el catálogo de consultas disponibles.

> 🔐 **La API pide iniciar sesión.** Para ver los datos en el navegador, entra primero a **http://127.0.0.1:8000/admin/** con el usuario del paso 6. El frontend inicia sesión con `/api/auth/login/` (detalles en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md)).
>
> ⚙️ **Configuración opcional:** copia `.env.example` como `.env` para cambiar la base de datos, la clave secreta o los dominios permitidos. Sin `.env`, el proyecto arranca en modo desarrollo con SQLite.

> La carga de datos puede tardar un par de minutos, porque son más de 240 mil registros.
>
> Los CSV terminan en noviembre de 2022. Al importarlos, las fechas se desplazan para que la última venta quede en la semana actual y el dashboard muestre datos "de hoy". Para conservar las fechas originales usa `python manage.py importar_csv --fechas-originales`.

---

## ✅ Estado actual

| Pieza                                                            | Estado                               |
| :--------------------------------------------------------------- | :----------------------------------- |
| Modelo de datos (clientes, productos, ventas, deudas, gastos)    | ✅ Listo                             |
| Carga automática de los CSV                                      | ✅ Listo                             |
| Consultas de resumen, evolución y listados                       | ✅ Listo                             |
| Exportación a Excel                                              | ✅ Listo                             |
| Conexión con cualquier base de datos (SQLite, PostgreSQL, MySQL) | ✅ Listo                             |
| Conexión real con el frontend                                    | 🟡 Guía escrita, falta implementarla |
| Usuarios, login (JWT) y configuración segura con `.env`          | ✅ Listo                             |
| Registrar ventas, pagos y gastos desde la API                    | ✅ Listo                             |
| Flujo de caja (entradas, salidas y saldo)                        | ✅ Listo                             |
| Pruebas automáticas                                              | 🟡 Login, registros y flujo de caja (25 pruebas) |

---

## 📋 Lo que falta, equipo por equipo

### 🗄️ Equipo de Base de Datos

- [ ] **Elegir y crear la base de datos de producción** (se recomienda PostgreSQL) y entregar los datos de conexión al equipo backend. El sistema ya está preparado: basta con configurar unas variables, sin tocar el código.
- [ ] **Cargar los datos** en esa base con el comando de importación y **revisar que los totales coincidan** con los del notebook de la Etapa 3 (`data/Etapa_3_Elaboración_de_Tablas.ipynb`).
- [ ] **Definir respaldos**: cada cuánto se respalda la base y quién lo hace.
- [ ] **Validar la calidad de los datos**: productos sin categoría (aparecen como _"Otros / sin clasificar"_), clientes sin contacto y fechas fuera de rango.
- [ ] **Revisar la caída de ventas en 2021-2022**: de ~16 mil ventas en 2019 se pasa a 241 en 2022 (en noviembre de 2022 hay una sola), mientras los gastos se mantienen en ~1.500 al año. Por eso el mes actual del dashboard muestra muy pocas ventas y los gastos superan a las ventas.

### 🎨 Equipo de Frontend / UX

- [ ] **Reemplazar los datos de prueba** (`dashboardMock.js`) por consultas reales al backend. La Parte 3 de [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md) trae el paso a paso, y la Parte 5 indica qué campo usar en cada tarjeta (ej.: el saldo es `flujo_caja.saldo`).
- [ ] **Conectar los formularios** de nueva venta, gasto y pago con `apiService.registrarVenta()`, `registrarGasto()` y `registrarPago()` (Parte 4.3).
- [ ] **Ajustar el gráfico semanal**: el backend agrupa por día, mes, trimestre o año, **no por semana**. Hay que decidir si el gráfico pasa a mensual o si se pide la agrupación semanal al backend.
- [ ] **Mostrar los montos en pesos chilenos** sin decimales (ej.: `$1.250.000`). Algunos montos llegan como texto y hay que convertirlos a número.
- [ ] **Diseñar los estados de carga y error**: qué ve el usuario mientras cargan los datos o si el servidor no responde.
- [ ] **Pantalla de login**: la API ya exige iniciar sesión (JWT). La guía trae un `api.js` listo que guarda el token, lo renueva solo y avisa cuando la sesión expira (Parte 4.3 de [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md)). No hace falta pantalla de registro: los usuarios los crea un administrador.
- [ ] **Conectar el botón "Exportar a Excel"** con `apiService.descargarExcel()` (un enlace directo ya no sirve, porque la descarga necesita el token).

### 🧠 Equipo de Backend

- [x] **Login y usuarios**: la API exige iniciar sesión con JWT (`/api/auth/login/`, `refresh/`, `logout/` y `perfil/`), con límite de intentos.
- [x] **Seguridad**: clave secreta, modo depuración, dominios y CORS se configuran en `.env` (ver `.env.example`); `.env` está en el `.gitignore`.
- [ ] **Al publicar**: definir `DJANGO_DEBUG=False` y una `DJANGO_SECRET_KEY` propia, servir con HTTPS (y activar `SECURE_SSL_REDIRECT` y HSTS según el servidor) y configurar un servicio de correo real si se llega a enviar email.
- [x] **Hora de Chile**: el sistema ahora usa `America/Santiago`, así los cortes de día y de mes calzan.
- [x] **Completar dependencias**: `pandas` y `openpyxl` ya están en `requirements.txt`.
- [ ] **Completar las pruebas automáticas**: ya hay 25 (login, registro de ventas, pagos, gastos y flujo de caja). Faltan las de los listados, filtros y la exportación a Excel. Se ejecutan con `python manage.py test`.
- [x] **Registrar datos nuevos**: ventas (contado y crédito), pagos, anulaciones, gastos y clientes con `POST` (ver el endpoint 11 en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md)).
- [x] **Flujo de caja como en el diseño**: `flujo_caja` en los resúmenes = ventas al contado + cobros − compras − otros gastos. El antiguo `flujo_caja_neto` se mantiene, pero es la utilidad bruta.

### 🤝 Decisiones que tomamos entre todos

- [ ] ¿Qué base de datos y qué servicio usaremos para publicar la app?
- [x] ¿Cómo se marca una deuda como **vencida**? Se **calcula**: es una cuenta pendiente cuya fecha límite ya pasó. No se guarda.
- [ ] **Validar estos supuestos del modelo** (se aplicaron para avanzar; se pueden cambiar):
  - Los pagos son **completos**: una cuenta pasa de pendiente a pagada de una vez (sin abonos parciales).
  - Los gastos tienen **tipo** (compra de productos u otro gasto), **categoría** y **proveedor opcional** (texto libre, sin tabla de proveedores).
  - Una venta se puede **anular** completa (no por producto).
- [ ] ¿El gráfico principal será semanal o mensual?
- [ ] Licencia del proyecto.
- [x] **Un solo negocio por ahora**: todos los usuarios ven los datos del mismo negocio. El login solo protege el acceso a la API.

---

## 🔮 Mejoras futuras

### Varios negocios en el mismo sistema (multi-pyme)

Hoy Caja Clara maneja **un solo negocio**. Si más adelante cada usuario debe ver **solo los datos de su negocio**, hay que modificar la base de datos:

- [ ] **Crear la tabla `Negocio`** (nombre, RUT, dirección, etc.) y relacionar cada usuario con su negocio.
- [ ] **Agregar el campo `negocio`** a `Cliente`, `Producto`, `Factura`, `CuentaPorCobrar` y `GastoInsumo`. `DetalleVenta` lo hereda a través de su factura.
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
