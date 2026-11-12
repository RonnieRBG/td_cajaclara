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
| **Facturas**           | Cada compra: fecha, cliente y si fue en tienda física o en línea. |
| **Detalle de venta**   | Qué productos iban en cada factura y en qué cantidad.             |
| **Cuentas por cobrar** | Ventas que el cliente aún no paga, con su fecha límite.           |
| **Gastos de insumo**   | Lo que el negocio gastó en reponer productos.                     |

### ¿Qué puede responder hoy?

- 📊 **Resumen financiero**: ingresos, costos, flujo de caja neto y margen, filtrando por fechas y por canal (físico u online).
- 📈 **Evolución en el tiempo**: los mismos números agrupados por día, mes, trimestre o año, ideal para gráficos.
- 🧾 **Listados con búsqueda**: clientes, productos, facturas, ventas, gastos y deudas (incluye filtro de deudas vencidas).
- 📥 **Exportar a Excel**: descarga del resumen en una planilla.
- 🎛️ **Opciones para filtros**: categorías, canales y el rango de fechas disponible, para armar los menús de la pantalla.

> El detalle de cada consulta (rutas, parámetros y ejemplos de respuesta) está en [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md).

---

## 🚀 Probarlo en tu computador

Necesitas **Python 3.10 o superior**. Son cinco pasos:

```bash
python -m venv venv                 # 1. Crear un entorno aislado
venv\Scripts\activate               # 2. Activarlo (en Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt     # 3. Instalar lo necesario
python manage.py migrate            # 4. Crear la base de datos
python manage.py importar_csv       # 5. Cargar los datos de ejemplo
```

Luego enciende el servidor con `python manage.py runserver` y abre **http://127.0.0.1:8000/api/** en el navegador. Verás el catálogo de consultas disponibles.

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
| Usuarios, login y seguridad                                      | 🔴 Pendiente                         |
| Pruebas automáticas                                              | 🔴 Pendiente                         |

---

## 📋 Lo que falta, equipo por equipo

### 🗄️ Equipo de Base de Datos

- [ ] **Elegir y crear la base de datos de producción** (se recomienda PostgreSQL) y entregar los datos de conexión al equipo backend. El sistema ya está preparado: basta con configurar unas variables, sin tocar el código.
- [ ] **Cargar los datos** en esa base con el comando de importación y **revisar que los totales coincidan** con los del notebook de la Etapa 3 (`data/Etapa_3_Elaboración_de_Tablas.ipynb`).
- [ ] **Definir respaldos**: cada cuánto se respalda la base y quién lo hace.
- [ ] **Validar la calidad de los datos**: productos sin categoría (aparecen como _"Otros / sin clasificar"_), clientes sin contacto y fechas fuera de rango.
- [ ] **Revisar la caída de ventas en 2021-2022**: de ~16 mil ventas en 2019 se pasa a 241 en 2022 (en noviembre de 2022 hay una sola), mientras los gastos se mantienen en ~1.500 al año. Por eso el mes actual del dashboard muestra muy pocas ventas y los gastos superan a las ventas.

### 🎨 Equipo de Frontend / UX

- [ ] **Reemplazar los datos de prueba** (`dashboardMock.js`) por consultas reales al backend. La Parte 3 de [`API_DOCUMENTACION.md`](./API_DOCUMENTACION.md) trae el paso a paso.
- [ ] **Ajustar el gráfico semanal**: el backend agrupa por día, mes, trimestre o año, **no por semana**. Hay que decidir si el gráfico pasa a mensual o si se pide la agrupación semanal al backend.
- [ ] **Mostrar los montos en pesos chilenos** sin decimales (ej.: `$1.250.000`). Algunos montos llegan como texto y hay que convertirlos a número.
- [ ] **Diseñar los estados de carga y error**: qué ve el usuario mientras cargan los datos o si el servidor no responde.
- [ ] **Diseñar las pantallas de login y registro**, que vendrán con la autenticación.
- [ ] **Conectar el botón "Exportar a Excel"**.

### 🧠 Equipo de Backend

- [ ] **Login y usuarios**: hoy cualquiera puede consultar la información. Se debe agregar inicio de sesión (por ejemplo, con tokens o JWT).
- [ ] **Seguridad antes de publicar**: mover la clave secreta a un archivo `.env` (y agregar ese archivo al `.gitignore`), desactivar el modo de depuración y limitar quién puede conectarse (hosts y CORS).
- [x] **Hora de Chile**: el sistema ahora usa `America/Santiago`, así los cortes de día y de mes calzan.
- [x] **Completar dependencias**: `pandas` y `openpyxl` ya están en `requirements.txt`.
- [ ] **Escribir pruebas automáticas** para los cálculos clave (ingresos, costos, margen y deudas vencidas).
- [ ] **Permitir registrar datos nuevos**: hoy la API solo permite _leer_. Falta poder crear ventas, gastos y marcar deudas como pagadas.

### 🤝 Decisiones que tomamos entre todos

- [ ] ¿Qué base de datos y qué servicio usaremos para publicar la app?
- [ ] ¿Cómo se marca una deuda como **vencida**? Hoy se calcula comparando la fecha límite con el día actual.
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

**Python** · **Django** (estructura del backend) · **Django REST Framework** (la API) · **SQLite** en desarrollo y **PostgreSQL** en producción · **pandas** (exportación a Excel).

---

_Hecho por el equipo de Caja Clara en el Bootcamp Talento Digital._
