# Instructivo de Producción — Etapa 4: Subir la Base a la Nube, Accesos y Respaldos (Tareas 20 y 21)

> **Alcance:** Guía paso a paso sin programación para desplegar el modelo relacional validado de **Caja Clara** en la nube, habilitar el acceso seguro para todo el equipo (Datos, Backend Python/Django y BI) y configurar respaldos automatizados como prototipo de producción.

---

## 1. Elección del Motor y Proveedor en la Nube (Tarea 20)

Antes de subir los datos, se evaluaron 4 alternativas gratuitas o de bajo costo considerando los requisitos reales del proyecto (`Tareas.csv` y `README.md` del repositorio):

1. **Tamaño real de la base de datos:** Las 6 tablas suman **247.972 filas** (~12,5 MB en CSV; ~35–45 MB en disco con índices).
2. **Compatibilidad con el Backend del equipo:** `requirements.txt` y `README.md` ya exigen **PostgreSQL** (`psycopg2-binary==2.9.13`) para Django REST Framework.
3. **Integridad transaccional y vistas:** Las etapas 6 y 7 requieren `PRIMARY KEY`, `FOREIGN KEY`, restricciones `CHECK`, vistas SQL reutilizables y escritura (`INSERT`/`UPDATE`) desde formularios web.

### Matriz comparativa

| Criterio | **Neon (PostgreSQL Serverless)** ✅ Elegido | **Supabase (PostgreSQL)** | **Google BigQuery** | **Cloud SQL / AWS RDS** |
| :--- | :--- | :--- | :--- | :--- |
| **Motor SQL y compatibilidad Django** | PostgreSQL nativo (100% compatible con `psycopg2-binary` y Django ORM) | PostgreSQL nativo | Data Warehouse columnar OLAP (no soporta Django ORM ni escritura OLTP por formulario) | PostgreSQL nativo |
| **Capa gratuita permanente** | **1 GB** por proyecto, **100 CU-horas/mes**, hasta **2 CU (~8 GB RAM)**, **5 GB** transferencia/mes, sin tarjeta de crédito | **500 MB** de BD, 500 MB RAM, 2 proyectos | 10 GB almacenamiento y 1 TB consultas/mes (solo lectura analítica) | Solo prueba temporal (90 días / 12 meses) y exige tarjeta |
| **Disponibilidad sin intervención** | Escala a cero tras 5 min de inactividad y **despierta automáticamente en milisegundos** con cualquier consulta | **Se pausa tras 7 días** sin actividad y exige reactivación manual en el panel web | Siempre activo | Pago por hora tras período de prueba |
| **Integridad relacional (`PK`/`FK`/`CHECK`)** | Total, aplicada al insertar/actualizar | Total | No aplica PK/FK en escritura (solo informativas) | Total |
| **Respaldos / Recuperación** | **10 ramas (branches) copy-on-write** + historial de **restauración instantánea de 6 horas** gratis + `pg_dump` | **Sin respaldos automáticos** en el plan Free (solo manual / `pg_dump`) | Snapshots / time travel analítico | Backups automáticos (de pago) |

### ¿Por qué elegimos **Neon (PostgreSQL Serverless)**?
* **Sobra capacidad en la capa gratuita:** Nuestra base completa (~40 MB con índices) ocupa menos del **5% del 1 GB gratuito** de Neon; incluso si en el futuro se cargara el dataset completo de 1 millón de filas (~150 MB), seguiría cabiendo holgadamente.
* **Cero bloqueos para el equipo:** A diferencia de Supabase Free (que congela el proyecto a los 7 días de inactividad y corta la demo hasta entrar al dashboard), Neon despierta solo en milisegundos cuando Django o Power BI consultan.
* **Única fuente de datos para Datos, Python y BI:** Soporta simultáneamente las vistas SQL de Etapa 5/6, Power BI Desktop y las operaciones `INSERT`/`UPDATE` del backend Django de Etapa 7 usando el mismo motor que `requirements.txt`.
* **Ramas de base de datos gratuitas (`Branching`):** Permite crear ramas aisladas (ej. `dev-python`, `qa-datos`) sin duplicar almacenamiento antes de tocar `main`.

---

## 2. Paso a Paso: Crear la Base de Datos en la Nube (Neon)

1. Ingresa a [https://neon.tech](https://neon.tech) y crea una cuenta gratuita (puedes usar GitHub o Google; **no pide tarjeta de crédito**).
2. Haz clic en **New Project**:
   - **Project name:** `cajaclara-prod-mvp`
   - **Postgres version:** `16` (o `17`, ambas compatibles con `schema_postgresql.sql`).
   - **Cloud provider & Region:** AWS — **South America (São Paulo) `sa-east-1`** si está disponible para menor latencia desde Chile, o **US East (N. Virginia / Ohio)**.
3. Al crearse el proyecto, Neon muestra la pantalla **Connection Details**. Copia el **Connection String** (formato `postgresql://...sslmode=require`), por ejemplo:
   ```text
   postgresql://neondb_owner:TU_PASSWORD@ep-xxxx.aws.neon.tech/neondb?sslmode=require
   ```
   > ⚠️ **Seguridad:** Nunca subas esta cadena de conexión ni contraseñas a GitHub (`.env` está excluido en `.gitignore`).

---

## 3. Paso a Paso: Subir el Esquema y los Datos Limpios a Neon (Tarea 18 + 20)

Los CSV definitivos (ya con los tipos corregidos del MER y con `estado` y `fecha_pago` generados en la Tarea 19) están listos en `datos/Etapas_4-5-6/Etapa_4_Carga_y_Nube/datos_procesados/`.

### Opción A — Usando `psql` (sin escribir código Python, método recomendado para producción)
1. Instala **PostgreSQL Client Tools** (incluye `psql` y `pg_dump`): en Windows puedes descargar el instalador oficial de EDB o instalar vía `winget install PostgreSQL.PostgreSQL.16` (desmarcando el servidor local si solo deseas las herramientas de línea de comandos).
2. Abre PowerShell en la carpeta `datos\Etapas_4-5-6\Etapa_4_Carga_y_Nube` y define temporalmente la variable de conexión en tu sesión:
   ```powershell
   $env:DATABASE_URL = "postgresql://neondb_owner:TU_PASSWORD@ep-xxxx.aws.neon.tech/neondb?sslmode=require"
   ```
3. Crea las 6 tablas, restricciones `CHECK` e índices ejecutando el DDL oficial:
   ```powershell
   psql "$env:DATABASE_URL" -f schema_postgresql.sql
   ```
4. Carga los 6 archivos CSV en orden respetando las claves foráneas (`cliente` → `producto` → `venta` → `detalle_venta` → `cuenta_por_cobrar` → `gastos_insumo`):
   ```powershell
   psql "$env:DATABASE_URL" -c "\copy cliente (id_cliente,nombre,contacto) FROM 'datos_procesados/cliente.csv' WITH (FORMAT csv, HEADER true)"
   psql "$env:DATABASE_URL" -c "\copy producto (id_producto,categoria,producto,unidad_negocio) FROM 'datos_procesados/producto.csv' WITH (FORMAT csv, HEADER true)"
   psql "$env:DATABASE_URL" -c "\copy venta (id_factura,id_cliente,fecha,tipo_compra,por_cobrar) FROM 'datos_procesados/venta.csv' WITH (FORMAT csv, HEADER true)"
   psql "$env:DATABASE_URL" -c "\copy detalle_venta (id_detalle,id_factura,id_producto,cantidad,precio_venta,costo_venta) FROM 'datos_procesados/detalle_venta.csv' WITH (FORMAT csv, HEADER true)"
   psql "$env:DATABASE_URL" -c "\copy cuenta_por_cobrar (id_cuenta,id_factura,id_cliente,monto,fecha_vencimiento,estado,fecha_pago) FROM 'datos_procesados/cuenta_por_cobrar.csv' WITH (FORMAT csv, HEADER true, NULL '')"
   psql "$env:DATABASE_URL" -c "\copy gastos_insumo (id_gasto,id_producto,fecha,monto) FROM 'datos_procesados/gastos_insumo.csv' WITH (FORMAT csv, HEADER true)"
   ```

### Opción B — Carga directa en un comando con Python (`etl_etapa4.py`)
Si prefieres ejecutar la carga desde el entorno virtual del proyecto (donde ya está `psycopg2-binary`):
```powershell
python datos/Etapas_4-5-6/Etapa_4_Carga_y_Nube/etl_etapa4.py --target postgres --database-url "$env:DATABASE_URL"
```

### Verificación obligatoria en Neon SQL Editor
Entra al **SQL Editor** en el dashboard web de Neon y ejecuta esta consulta para confirmar que los totales en la nube coinciden al 100% con el archivo origen (`ventas_originales_fuente.csv`):
```sql
SELECT
    (SELECT COUNT(*) FROM cliente) AS clientes,
    (SELECT COUNT(*) FROM producto) AS productos,
    (SELECT COUNT(*) FROM venta) AS ventas,
    (SELECT COUNT(*) FROM detalle_venta) AS lineas_detalle,
    (SELECT SUM(cantidad) FROM detalle_venta) AS unidades_totales,
    (SELECT SUM(cantidad::bigint * precio_venta) FROM detalle_venta) AS ingreso_total,
    (SELECT SUM(cantidad::bigint * costo_venta) FROM detalle_venta) AS costo_total,
    (SELECT COUNT(*) FROM cuenta_por_cobrar) AS cuentas_por_cobrar,
    (SELECT SUM(monto) FROM cuenta_por_cobrar) AS monto_cxc,
    (SELECT COUNT(*) FROM gastos_insumo) AS gastos_insumo,
    (SELECT SUM(monto) FROM gastos_insumo) AS monto_gastos;
```
**Valores esperados exactos:**
* `clientes`: `2.000` | `productos`: `7.488` | `ventas`: `100.067` | `lineas_detalle`: `103.489`
* `unidades_totales`: `357.708` | `ingreso_total`: `403.521.023` | `costo_total`: `312.160.447`
* `cuentas_por_cobrar`: `14.928` | `monto_cxc`: `57.339.252`
* `gastos_insumo`: `20.000` | `monto_gastos`: `24.484.481`

---

## 4. Configurar Accesos y Permisos por Rol (Tarea 21 — Seguridad)

Nunca entregues el usuario administrador (`neondb_owner`) a herramientas de visualización ni a la API en producción. Aplica el principio de **mínimo privilegio**:

| Rol / Usuario | Quién lo usa | Permisos otorgados | Restricciones |
| :--- | :--- | :--- | :--- |
| `neondb_owner` (Admin) | Solo responsable de Datos (migraciones DDL) | Control total | No usar en Power BI ni en Django prod |
| `cajaclara_app_rw` | Backend Python / Django (`cajaclara`) | `SELECT, INSERT, UPDATE` en tablas y secuencias | No puede borrar tablas (`DROP`), truncar (`TRUNCATE`) ni alterar esquema |
| `cajaclara_lectura_bi` | Power BI Desktop / Analítica | Solo `SELECT` en tablas y vistas | No puede insertar, editar ni borrar registros |

### Pasos para aplicar los roles:
1. Abre `datos/Etapas_4-5-6/Etapa_4_Carga_y_Nube/roles_y_permisos_postgresql.sql`.
2. Reemplaza `REEMPLAZAR_CLAVE_SEGURA_BI` y `REEMPLAZAR_CLAVE_SEGURA_APP` por contraseñas aleatorias de al menos 20 caracteres (guárdalas en un gestor de claves del equipo, nunca en Git).
3. Ejecuta el script en el **SQL Editor** de Neon o con:
   ```powershell
   psql "$env:DATABASE_URL" -f roles_y_permisos_postgresql.sql
   ```
4. **Habilitar SSL obligatorio:** Neon exige `sslmode=require` en todas las conexiones.
5. **Conexión para el equipo Python (Django `.env`):** Comparte de forma privada con el equipo backend los parámetros para su archivo `.env` local (usando el rol `cajaclara_app_rw`):
   ```dotenv
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=neondb
   DB_USER=cajaclara_app_rw
   DB_PASSWORD=<CLAVE_APP>
   DB_HOST=ep-xxxx.aws.neon.tech
   DB_PORT=5432
   DB_SSLMODE=require
   ```
6. **Conexión para Analítica / Power BI:** Comparte con el área de visualización el usuario `cajaclara_lectura_bi` (solo lectura).

---

## 5. Configurar Copias de Seguridad Automatizadas (Tarea 21 — Respaldos)

En un prototipo de producción, combinamos **dos capas de respaldo** (regla 3-2-1 adaptada a capa gratuita):

### Capa 1: Recuperación instantánea en la nube (Neon)
* Neon mantiene por defecto en el plan gratuito un **historial de cambios de 6 horas (Instant Restore)** y permite crear **branches de respaldo** en un clic (`Dashboard → Branches → Create branch`) antes de cualquier cambio masivo o prueba de Etapa 7.

### Capa 2: Respaldo lógico diario fuera de la nube (`pg_dump` comprimido)
Se incluye el script `respaldo_postgres.ps1`, que genera archivos binarios comprimidos `.dump` (con retención automática de 30 días).

#### Cómo programarlo en Windows (Programador de Tareas — 3 minutos, sin código):
1. Abre el menú Inicio y busca **Programador de tareas** (*Task Scheduler*).
2. En el panel derecho haz clic en **Crear tarea básica...**:
   - **Nombre:** `Respaldo Diario BD Caja Clara`
   - **Desencadenador:** `Diariamente` (ej. `02:00` hrs).
   - **Acción:** `Iniciar un programa`.
   - **Programa o script:** `powershell.exe`
   - **Agregar argumentos:**
     ```text
     -NoProfile -ExecutionPolicy Bypass -Command "$env:DATABASE_URL='postgresql://cajaclara_lectura_bi:CLAVE@ep-xxxx.neon.tech/neondb?sslmode=require'; & 'C:\Users\Asus\Documents\GitHub\td_cajaclara\datos\Etapas_4-5-6\Etapa_4_Carga_y_Nube\respaldo_postgres.ps1'"
     ```
3. Prueba manualmente ejecutando la tarea una vez desde el Programador de Tareas y verifica que aparezca el archivo `cajaclara_backup_YYYYMMDD_HHMMSS.dump` dentro de `backups/`.
4. *(Opcional recomendado para equipos remotos)*: Si deseas respaldos automáticos en la nube sin depender de un PC encendido, configura un workflow en **GitHub Actions** con `schedule: cron: '0 6 * * *'`, guardando `NEON_DATABASE_URL` como GitHub Secret y subiendo el `.dump` como *Artifact* con retención de 30 días.

#### Prueba de restauración (obligatoria para validar un respaldo)
Un respaldo solo sirve si se ha probado restaurarlo. Para restaurar en una rama de prueba de Neon:
```powershell
pg_restore --dbname="postgresql://neondb_owner:CLAVE@ep-rama-prueba.neon.tech/neondb?sslmode=require" --clean --if-exists backups\cajaclara_backup_YYYYMMDD_HHMMSS.dump
```
