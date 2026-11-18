# Diseño UX y Frontend — CajaClara

Este documento resume el proceso de diseño y la arquitectura de frontend de CajaClara: investigación, definición del MVP, user flows, wireframes, estado real de la integración con Backend, checklist de cierre y requerimientos de despliegue.

Para detalles de Vue, estructura del código, dependencias y ejecución local, consulta el [README técnico del prototipo](./prototype/cajaclara-ui/README.md).  
Para los contratos, adaptadores, endpoints y reglas de consumo de la API, consulta la [Guía de Integración Backend](./INTEGRACION-BACKEND.md).

---

## Producto y problema

CajaClara busca ayudar a micronegocios a registrar ventas, compras y gastos, comprender el saldo de un periodo y dar seguimiento a sus cuentas por cobrar. Tradicionalmente estas tareas se reparten entre cuadernos, conversaciones y aplicaciones bancarias, lo que dificulta revisar el estado real del negocio y recordar cobros pendientes.

La experiencia prioriza un lenguaje cotidiano, información financiera resumida y tareas frecuentes que puedan completarse con pocos pasos.

---

## Investigación y definición

### Benchmarking

El [benchmarking](./research/benchmarking.md) revisó Fintonic, Nubox, Alegra, Mercado Pago Negocios y Money Manager. Los hallazgos que guían la propuesta son:

- Priorizar pocos indicadores y evitar la sobrecarga visual.
- Combinar la simplicidad de una herramienta personal con controles útiles para un negocio.
- Hacer visibles las cuentas por cobrar como una necesidad central.
- Facilitar el registro rápido de movimientos y el uso móvil.

### User Persona

La [User Persona](./research/user-person.md) representa a Camila Muñoz, emprendedora de un micronegocio en Santiago, con conocimientos contables básicos. Usa herramientas cotidianas y necesita ver ingresos, gastos y deudas sin dedicar demasiado tiempo a tareas administrativas.

Sus principales necesidades son comprender el saldo, registrar movimientos rápidamente y recordar a quién debe cobrar.

---

## Alcance del MVP

### Incluido en la definición del MVP

- Acceso seguro mediante autenticación JWT (login, refresh rotativo, logout y protección de rutas).
- Consulta del estado financiero del negocio (Dashboard general).
- Registro de ventas pagadas al contado o ventas a crédito (cuentas por cobrar).
- Registro de compras de productos y gastos en insumos.
- Consulta detallada de operaciones con filtros por tipo, canal y periodo.
- Seguimiento de cuentas por cobrar, alertas operativas y registro de pago completo o reversión.
- Resumen mensual financiero con evolución semanal y desglose de entradas y salidas.
- Exportación autenticada a Excel del detalle de ventas del periodo.
- Selección explícita entre datos simulados (mocks) y conexión a API en vivo mediante variable de entorno.

### Fuera del alcance actual

- Pagos parciales o abonos a cuentas por cobrar.
- Inventario o stock automático en tiempo real.
- Facturación electrónica y conexión con el SII.
- Integraciones automáticas con WhatsApp o envío de correos.
- Reportes tributarios y cálculos contables avanzados de balance general o libro diario.
- Sincronización automática en tiempo real entre pantallas sin recargar o navegar entre vistas.

---

## User flows

Los [user flows](./user-flows/userflows-cajaclara.md) describen los recorridos de acceso y configuración, consulta financiera, operaciones de caja y gestión de cobros. Los diagramas facilitan su revisión en GitHub y se encuentran alineados con los wireframes y el prototipo funcional.

---

## Wireframes

Los wireframes iniciales conservan las versiones navegables en HTML/CSS y sus capturas para referencia de diseño:

- [Dashboard](./wireframes/dashboard.html) · [PNG móvil](./wireframes/dashboard.png)
- [Compras y ventas](./wireframes/movimientos.html) · [PNG móvil](./wireframes/movimientos.png)
- [Cuentas por cobrar](./wireframes/cuentas-cobrar.html) · [PNG móvil](./wireframes/cuentas-cobrar.png)
- [Estilos compartidos](./wireframes/styles.css)

---

## Estado real de la integración Frontend / Backend

El frontend Vue 3 (`ux/prototype/cajaclara-ui/`) se encuentra completamente conectado con el Backend Django (`/api/`) para todos los módulos financieros principales:

1. **Autenticación y Sesión:**
   - Inicio de sesión con credenciales (`/api/auth/login/`), persistencia JWT en `localStorage`, consulta de perfil (`/api/auth/perfil/`), refresco automático de token (`/api/auth/refresh/`), cierre de sesión invalidando refresh en servidor (`/api/auth/logout/`) y protección global de rutas en el router.
2. **Dashboard y Resumen Mensual:**
   - Métricas y KPIs de saldo, ingresos y salidas obtenidos desde `/api/finanzas/resumen-mensual/`.
   - Flujo de caja semanal obtenido desde `/api/finanzas/resumen-agrupado/?agrupacion=semanas_mes`.
   - Cobros prioritarios operativos obtenidos desde `/api/finanzas/alertas-cobro/`.
   - Operaciones recientes obtenidas desde `/api/finanzas/operaciones/`.
   - Productos más vendidos obtenidos desde `/api/finanzas/productos/`.
   - Rango de fechas y opciones dinámicas obtenidas desde `/api/finanzas/opciones-filtros/`.
3. **Compras y Ventas (Operaciones):**
   - Listado, paginación, filtros de canal y periodo desde `/api/finanzas/operaciones/`.
   - Consulta de detalle de venta desde `/api/finanzas/facturas/{id_factura}/`.
   - Registro de nuevas ventas al contado o a crédito (`POST /api/finanzas/facturas/`).
   - Registro de gastos de insumos asociados a producto (`POST /api/finanzas/gastos/`).
   - Creación y selección de clientes (`POST /api/finanzas/clientes/` y `/api/finanzas/opciones/clientes/`).
4. **Cuentas por Cobrar:**
   - Listado paginado de deudas e indicadores globales desde `/api/finanzas/cuentas-por-cobrar/`.
   - Alertas operativas de cobranza y mensajes sugeridos desde `/api/finanzas/alertas-cobro/`.
   - Registro de pago completo (`POST /api/finanzas/cuentas-por-cobrar/{id}/pagar/`).
   - Reversión de pago registrado (`POST /api/finanzas/cuentas-por-cobrar/{id}/revertir-pago/`).
5. **Exportación a Excel Autenticada:**
   - Descarga de archivo `.xlsx` desde `/api/finanzas/exportar-excel/` mediante `apiClient` con Bearer token, enviando los filtros de fecha y canal activos.
6. **Selección Explícita entre Mocks y API:**
   - Controlada mediante la variable `VITE_USE_MOCKS` (`true` para modo demostración sin servidor; `false` para conexión directa y estricta a la API de Django).
   - En modo API no se realiza fallback silencioso a mocks en caso de error, garantizando trazabilidad y visualización de estados de error con opción de reintento.
7. **Frontend Desplegado en Vercel:**
   - Prototipo responsivo y accesible públicamente en: [https://tdcajaclara-cajaclara-ui-omega.vercel.app/](https://tdcajaclara-cajaclara-ui-omega.vercel.app/)
8. **Limitaciones Técnicas Reconocidas:**
   - Sin pagos parciales ni abonos (solo pago completo o reversión según contrato).
   - Sin control automático de inventario físico ni stock remanente.
   - Sin facturación electrónica ni boletas ante entidades fiscales.
   - Sin sincronización reactiva inmediata entre pestañas o módulos: tras registrar un movimiento o cobro, las otras vistas (Dashboard/Resumen) recuperan los totales vigentes en su siguiente carga.

---

## Checklist para Backend (Finalización de Integración)

Documentación de los pasos requeridos para cerrar el ciclo de integración entre Frontend y Backend:

- [ ] Incorporar la rama de integración actualizada.
- [ ] Resolver conflictos sin modificar el esquema de Datos.
- [ ] Conservar Django en la raíz y Vue en `ux/prototype/cajaclara-ui/`.
- [ ] Revisar `.gitignore` y confirmar que no existan secretos ni archivos `.env` versionados.
- [ ] Confirmar variables de Backend, Neon, JWT, CORS y hosts permitidos.
- [ ] Confirmar que `API_DOCUMENTACION.md` y `ACOPLAMIENTO.md` estén actualizados.
- [ ] Ejecutar solo las comprobaciones mínimas acordadas.
- [ ] Subir la rama de integración.
- [ ] Abrir Pull Request hacia `main`.
- [ ] Revisar y aprobar el PR antes del merge.
- [ ] No hacer push directo ni force push sobre `main`.

---

## Procedimiento para el paso a main

Instrucciones estandarizadas para fusionar la rama de integración en la rama principal:

1. **Actualizar la rama de integración con main:** Traer y sincronizar los últimos cambios de `origin/main` en la rama de integración local.
2. **Resolver conflictos:** En caso de discrepancias, resolverlas manteniendo la arquitectura acordada (Django en la raíz, Vue en `ux/prototype/cajaclara-ui/`) y respetando íntegramente el esquema de tablas y tipos de datos de Análisis de Datos.
3. **Hacer commit de la resolución:** Registrar un commit descriptivo y limpio con la resolución de conflictos.
4. **Subir la rama:** Publicar la rama de integración actualizada en el repositorio remoto (`git push origin <rama-integracion>`).
5. **Abrir PR con base main:** Abrir un Pull Request en GitHub seleccionando `base: main` y `compare: <rama-integracion>`.
6. **Completar la descripción del PR:** Incluir el alcance de los cambios, las variables de entorno necesarias para la ejecución, las limitaciones funcionales del MVP y el listado de documentación actualizada.
7. **Hacer el merge solo después de la aprobación del equipo:** El PR debe ser revisado y aprobado por los responsables de Backend y Frontend antes de fusionarse.

> **Regla de seguridad:** No ejecutar el merge automáticamente ni realizar `git push` directo o force push sobre `main`.

---

## Información requerida de Backend para el deploy final

Para completar el despliegue integrado y asegurar la comunicación fluida entre el frontend en Vercel y el backend Django en producción, el equipo de Backend debe proveer las siguientes definiciones técnicas:

1. **URL pública definitiva de la API:** Endpoint base productivo que responderá las peticiones (ej. `https://api.cajaclara.cl/api` o `https://cajaclara-backend.up.railway.app/api`).
2. **Estrategia elegida para desplegar Django en Vercel:** Especificar si Django se desplegará como función serverless dentro de Vercel (mediante `vercel.json` y runtime Python WSGI/ASGI) o si se publicará en una plataforma PaaS externa (como Render, Railway o AWS) manteniendo Vercel exclusivamente para el bundle estático de Vue.
3. **Configuración o archivos necesarios para WSGI/ASGI:** Entregar o definir los archivos de entrada requeridos según la estrategia adoptada (`cajaclara/wsgi.py`, `cajaclara/asgi.py`, `vercel.json`, o scripts de inicio).
4. **Variables de entorno requeridas:** Listado completo y documentado de nombres de variables para producción (tanto en Backend como en Frontend), omitiendo cualquier credencial o valor secreto sensible.
5. **Configuración de Neon:** Confirmar parámetros de conexión de la base de datos de producción (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PORT`, `DB_SSLMODE=require`).
6. **`DJANGO_ALLOWED_HOSTS`:** Lista oficial de dominios que deben incluirse en `ALLOWED_HOSTS` para permitir el tráfico en producción.
7. **`CORS_ALLOWED_ORIGINS`:** Lista oficial de orígenes de frontend autorizados para realizar peticiones cross-origin (incluyendo la URL definitiva de Vercel `https://tdcajaclara-cajaclara-ui-omega.vercel.app` y eventuales dominios personalizados).
8. **Procedimiento de migraciones:** Instrucciones claras sobre el momento y mecanismo para ejecutar `python manage.py migrate --fake-initial` contra la base de datos Neon sin alterar las tablas de datos existentes.
9. **Creación del usuario demo:** Comando o script para inicializar el usuario demostrativo o superadministrador en producción con el que se validará la aplicación.
10. **URL que debe utilizar `VITE_API_BASE_URL`:** Valor exacto que debe configurarse en las variables de entorno del proyecto frontend en el panel de Vercel.
11. **Ruta de health check:** Endpoint de verificación de estado y conectividad (ej. `GET /api/` o `GET /api/health/`) para monitorear la disponibilidad del backend.
12. **Procedimiento de rollback:** Plan de contingencia documentado en caso de fallas imprevistas en la base de datos o en el despliegue de la API.
13. **Responsable de validar Backend en producción:** Nombre o rol del integrante del equipo encargado de comprobar y dar la conformidad final a los endpoints en el entorno productivo.

> **Nota técnica sobre Vercel:** Cualquier modificación en las variables de entorno (`VITE_*`) en el panel de administración de Vercel no se aplica dinámicamente en tiempo de ejecución; **requiere un nuevo deployment** (Redeploy) para que Vite compile los valores actualizados en el bundle estático de producción.

---

## Enlaces y referencias técnicas

- [README técnico del prototipo Vue](./prototype/cajaclara-ui/README.md)
- [Guía de Integración Backend](./INTEGRACION-BACKEND.md)
- [Documentación técnica de la API Django](../API_DOCUMENTACION.md)
- [Procedimiento de acoplamiento entre equipos](../ACOPLAMIENTO.md)
- [README principal del proyecto](../README.md)
