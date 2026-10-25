# Caja Clara - Sistema de Gestión Financiera y Flujo de Caja

> **Proyecto Bootcamp Talento Digital** | Semana 2: Fundamentos de Backend & Primeros Endpoints
> Plataforma para que microempresas, pymes y personas ordenen sus finanzas, controlen ingresos/gastos y gestionen cuentas por cobrar.

## Tabla de Contenidos

1. [Sobre el Proyecto](#sobre-el-proyecto)
2. [Estado (Semana 2)](#estado-semana-2)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Estructura del Repositorio](#estructura-del-repositorio)
5. [Instalación Local](#instalación-local)
6. [Configuración y Pruebas](#configuración-y-pruebas)
7. [Modelos de Base de Datos](#modelos-de-base-de-datos)
8. [API REST](#api-rest)
9. [Guía para UX / UI & Frontend](#guía-para-ux--ui--frontend)
10. [Notas Técnicas y Decisiones Pendientes](#notas-técnicas-y-decisiones-pendientes)
11. [Flujo de Trabajo con Git](#flujo-de-trabajo-con-git)
12. [Roadmap (Semana 3)](#roadmap-semana-3)

---

## Sobre el Proyecto

Muchas pymes facturan pero no tienen liquidez, o no saben si su saldo mensual es positivo o negativo. **Caja Clara** resuelve esto con:
- Registro categorizado de ingresos y gastos en Pesos Chilenos (CLP).
- Seguimiento de cuentas por cobrar para anticipar cobros y evitar morosidad.
- Métricas instantáneas de flujo de caja.

## Estado (Semana 2)

- [x] Proyecto Django (`cajaclara`) y app de dominio (`finanzas`).
- [x] Modelos: Categorías, Movimientos y Cuentas por Cobrar.
- [x] Registro en Django Admin (`/admin/`).
- [x] CORS habilitado (solo desarrollo).
- [x] Primer endpoint: resumen financiero mensual (`/api/finanzas/resumen-mensual/`).

> Esta sección quedará obsoleta; conviene moverla a un `CHANGELOG.md` más adelante.

## Stack Tecnológico

| Capa | Tecnología | Versión |
| :--- | :--- | :--- |
| Lenguaje | Python | 3.10+ |
| Framework | Django | 6.1.2 |
| API REST | Django REST Framework | 3.18.3 |
| CORS | django-cors-headers | 4.9.0 |
| BD local | SQLite | 3 |
| BD producción | PostgreSQL (`psycopg2-binary`) | 2.9.13 |

> Las versiones deben coincidir con `requirements.txt`.

## Estructura del Repositorio

```text
TalentoDigital/
├── cajaclara/          # Configuración global (settings, urls, asgi, wsgi)
├── finanzas/           # App principal
│   ├── migrations/     # Historial del esquema de BD
│   ├── admin.py        # Modelos en el panel de control
│   ├── models.py       # Categoria, Movimiento, CuentaPorCobrar
│   ├── tests.py        # Pruebas unitarias
│   └── views.py        # Controladores de la API
├── .env.example        # Plantilla de variables de entorno
├── .gitignore          # Excluye db.sqlite3, venv/, .env
├── manage.py
├── requirements.txt
└── README.md
```

## Instalación Local

```bash
# 1. Clonar
git clone <URL_DEL_REPOSITORIO>
cd TalentoDigital

# 2. Entorno virtual
python -m venv venv
.\venv\Scripts\activate          # Windows (PowerShell)
source venv/bin/activate         # macOS / Linux

# 3. Dependencias y variables de entorno
pip install -r requirements.txt
cp .env.example .env             # Windows (cmd): copy .env.example .env

# 4. Base de datos, superusuario y servidor
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

El servidor queda en **http://127.0.0.1:8000/**. Si el entorno está activo verás `(venv)` en la terminal.

## Configuración y Pruebas

Los valores sensibles van en `.env`, nunca en Git. Plantilla `.env.example`:

```dotenv
DJANGO_SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Solo PostgreSQL (producción)
DB_NAME=cajaclara
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```

Lectura en `settings.py`:

```python
import os
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "clave-solo-para-desarrollo")
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
```

Para PostgreSQL, usa `django.db.backends.postgresql` en `DATABASES` con las variables `DB_*` y ejecuta `migrate`.

**Pruebas:** `python manage.py test` (o `python manage.py test finanzas`).

## Modelos de Base de Datos

Definidos en `finanzas/models.py`; todos se asocian al `User` de Django.

**`Categoria`**: clasifica los movimientos.
- `usuario` (FK), `nombre` (50), `tipo` (`INGRESO` | `GASTO`).
- Un usuario no puede repetir nombre + tipo.

**`Movimiento`**: cada transacción real. Su tipo (ingreso/gasto) lo define la categoría.
- `usuario` (FK), `categoria` (FK), `transaccion_id` (50, opcional), `monto` (CLP, sin decimales), `fecha`, `descripcion` (opcional), `fecha_registro` (automático).

**`CuentaPorCobrar`**: pagos pendientes de clientes.
- `usuario` (FK), `deudor` (100), `monto` (CLP), `fecha_emision`, `fecha_vencimiento`, `notas_contacto` (opcional).
- `estado`: `PENDIENTE` (por defecto) | `PAGADA` | `VENCIDA`. Es un campo almacenado: nada lo cambia solo al pasar la fecha de vencimiento (ver [Notas Técnicas](#notas-técnicas-y-decisiones-pendientes)).

## API REST

### `GET /api/finanzas/resumen-mensual/`

Local: `http://127.0.0.1:8000/api/finanzas/resumen-mensual/` · Sin autenticación (solo desarrollo).

> ⚠️ **Temporal:** el endpoint no filtra por el usuario que consulta; usa un usuario fijo (el primero en la base de datos). En la Semana 3 pasará a usar el usuario autenticado.

**Funcionamiento:** toma el mes y año actuales (`now().date()`), filtra los `Movimiento` de ese período y calcula:
- `total_ingresos`: suma de movimientos con categoría `INGRESO`.
- `total_gastos`: suma de movimientos con categoría `GASTO`.
- `flujo_caja`: `total_ingresos - total_gastos` (puede ser negativo).

**Respuesta `200 OK`:**
```json
{
  "mes": 10,
  "anio": 2026,
  "total_ingresos": 2850000,
  "total_gastos": 1420000,
  "flujo_caja": 1430000
}
```

> ⚠️ **Frontend:** DRF serializa `DecimalField` como string por defecto (`"2850000"`). Si la vista no convierte a `int`, usa `Number(...)` antes de operar. Verifica la respuesta real con Postman y ajusta este ejemplo.

**Error `400 Bad Request`** (no hay usuarios en la BD):
```json
{ "error": "No hay usuarios en la base de datos para probar." }
```
Solución: `python manage.py createsuperuser` y agregar movimientos desde `/admin/`.

## Guía para UX / UI & Frontend

Ya puedes maquetar con datos reales del resumen mensual.

**CORS:** en desarrollo `CORS_ALLOW_ALL_ORIGINS = True`, así que puedes consumir la API desde React/Vite (`localhost:5173`, `localhost:3000`), HTML/JS vanilla o Postman/Insomnia. Se restringirá antes de producción.

### Pantallas a diseñar

**A. Dashboard** (usa el endpoint actual)
- Header con mes y año (ej: *"Octubre 2026"*).
- 3 tarjetas KPI: 🟢 Total Ingresos, 🔴 Total Gastos, ⚖️ Flujo de Caja Neto (verde si es positivo, rojo si es negativo).
- Gráfico de dona o barras: Ingresos vs. Gastos.

**B. Movimientos** (endpoints pendientes; maquetar con datos de ejemplo)
- Tabla: Fecha, Categoría, Descripción, N° Transacción, Monto, con badge de color por Ingreso/Gasto.
- Formulario "Nuevo Movimiento": tipo (filtra categorías), categoría, monto en CLP, fecha, descripción y comprobante (opcionales).

**C. Cuentas por Cobrar**
- Listado con deudor, monto y fecha límite.
- Badges: 🟡 `PENDIENTE`, 🟢 `PAGADA`, 🔴 `VENCIDA`.
- Acciones rápidas: *"Registrar Pago"* y *"Contactar"*.

### Reglas de formato
- Montos en **CLP sin decimales**. Si `flujo_caja` es negativo, mostrar una alerta sugiriendo revisar gastos.

```javascript
export const formatCLP = (amount) =>
  new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    maximumFractionDigits: 0,
  }).format(Number(amount)); // Number() por si la API entrega strings
```

### Ejemplo de consumo
```javascript
async function cargarResumenMensual() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/finanzas/resumen-mensual/');
    if (!response.ok) throw new Error('Error al obtener los datos');
    const data = await response.json();
    console.log('Datos del mes:', data);
  } catch (error) {
    console.error('Error en la petición:', error);
  }
}
```

## Notas Técnicas y Decisiones Pendientes

**Seguridad (antes de producción)**
- Endpoint sin autenticación: se corrige con Token/JWT en la Semana 3.
- Reemplazar `CORS_ALLOW_ALL_ORIGINS` por `CORS_ALLOWED_ORIGINS` con los dominios del frontend.
- `DEBUG=False`, `SECRET_KEY` única y `ALLOWED_HOSTS` definido, todo desde variables de entorno.

**Zona horaria:** `now().date()` puede desfasar el cambio de mes si `TIME_ZONE` no es `America/Santiago`. Recomendado:
```python
# settings.py
TIME_ZONE = "America/Santiago"
USE_TZ = True

# views.py
from django.utils import timezone
hoy = timezone.localdate()
```

**Estado `VENCIDA` (decisión pendiente):** definir antes de crear los endpoints de `CuentaPorCobrar`:
1. *Calculado:* una cuenta `PENDIENTE` con `fecha_vencimiento` anterior a hoy se trata como vencida (siempre consistente, sin tareas programadas).
2. *Almacenado:* se actualiza con un *management command* diario.

## Flujo de Trabajo con Git

1. **No trabajes sobre `main`:** crea una rama, ej. `git checkout -b feature/crud-movimientos` o `ui/dashboard-cards`.
2. **No se suben a Git:** `db.sqlite3`, `venv/` y `.env` (cada integrante tiene los suyos).
3. **Commits claros:** `feat: agregar endpoint de resumen mensual`, `style: mejorar badges de cuentas por cobrar`, `fix: corregir cálculo de flujo de caja`.
4. **Sincroniza antes del Pull Request:**
   ```bash
   git checkout main && git pull origin main
   git checkout feature/tu-rama && git merge main
   ```

## Roadmap (Semana 3)

- [ ] Autenticación con Tokens / JWT (login y registro).
- [ ] Resumen filtrado por usuario autenticado y por `?mes=X&anio=Y`.
- [ ] CRUD completo de `Movimiento` y `Categoria`.
- [ ] Endpoints de `CuentaPorCobrar` y cambio de estado (`PAGADA`).
- [ ] Definir manejo de `VENCIDA` y configurar zona horaria `America/Santiago`.
- [ ] Restringir CORS y endurecer configuración para producción.
- [ ] Integración con el frontend del equipo de diseño.

**Licencia:** pendiente de definir.

---

*Desarrollado por el equipo de Caja Clara en el Bootcamp Talento Digital.*
