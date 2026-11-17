# CajaClara UI — Prototipo Vue

Documentación técnica del prototipo frontend de alta fidelidad. Para la investigación UX, el alcance del MVP y el proceso de diseño, consulta el [README de Diseño UX](../../README.md).

## Estado técnico

### Implementado

- Vistas navegables de Dashboard, Compras y ventas, Cuentas por cobrar y Resumen mensual.
- Formularios, filtros, búsqueda, detalle y confirmaciones simuladas según el módulo.
- Layout responsive y design tokens compartidos.
- Login JWT, restauración de sesión, refresh automático, perfil y logout.
- Datos mock y estado local para interacciones financieras del prototipo.

### En desarrollo

La autenticación está conectada a Backend. La integración de las vistas financieras se hará por etapas y continúa usando los mocks existentes.

### Pendiente

- Conectar las vistas financieras con los contratos de Backend acordados.
- Persistir y sincronizar operaciones entre módulos.
- Incorporar estados de carga y error en cada módulo financiero al integrarlo.
- Añadir pruebas automatizadas y completar la validación de accesibilidad.

### Fuera del alcance actual

Pagos parciales, gestión de usuarios, facturación electrónica, inventario automático y notificaciones reales por WhatsApp o correo.

> Solo la autenticación se comunica con Backend. Los datos financieros siguen siendo mocks: los cambios locales se pierden al recargar y no se sincronizan entre módulos. El deploy de demostración utiliza datos simulados y requiere configurar el Backend por entorno para habilitar login.

## Stack y versiones

Aplicación JavaScript con Vue Single File Components (`<script setup>`), Composition API, Vue Router y CSS nativo. No utiliza librería externa de gráficos ni store global.

| Dependencia | Rango en `package.json` | Versión instalada actualmente |
| --- | --- | --- |
| `vue` | `^3.5.12` | `3.5.45` |
| `vue-router` | `^4.4.5` | `4.6.4` |
| `vite` | `^5.4.10` | `5.4.21` |
| `@vitejs/plugin-vue` | `^5.1.4` | `5.2.4` |

Las versiones instaladas corresponden al entorno verificado con `npm ls --depth=0`; `package-lock.json` registra la resolución del proyecto.

## Requisitos previos

- Node.js 18 o superior, compatible con Vite 5. `package.json` no declara un campo `engines`.
- npm.
- Navegador moderno.

## Instalación y ejecución

Desde la raíz del repositorio:

```bash
cd ux/prototype/cajaclara-ui
npm install
npm run dev
```

Vite sirve la aplicación en `http://localhost:5173`.

## Scripts disponibles

Son los scripts presentes en `package.json`:

| Comando | Uso |
| --- | --- |
| `npm run dev` | Inicia el servidor de desarrollo. |
| `npm run build` | Genera el build de producción en `dist/`. |
| `npm run preview` | Sirve localmente el build generado. |

No hay scripts configurados para tests, lint o formateo.

## Estructura del proyecto

```text
cajaclara-ui/
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
├── dist/                         # Generado por npm run build
└── src/
    ├── App.vue
    ├── main.js
    ├── assets/styles/main.css
    ├── components/
    │   ├── common/
    │   ├── dashboard/
    │   ├── operations/
    │   └── receivables/
    ├── data/
    ├── composables/useAuth.js
    ├── router/index.js
    ├── services/
    │   ├── apiClient.js
    │   └── authService.js
    ├── utils/formatters.js
    └── views/
        └── LoginView.vue
```

`vite.config.js` configura el plugin de Vue, el alias `@` hacia `src/` y el puerto 5173. `dist/` es un directorio generado por el build.

## Vistas y componentes existentes

### Vistas (`src/views/`)

| Archivo | Responsabilidad |
| --- | --- |
| `DashboardView.vue` | Indicadores, acciones rápidas, flujo semanal, cobros prioritarios, movimientos recientes y productos destacados. |
| `OperationsView.vue` | Compras y ventas, filtros, búsqueda, detalle y formularios simulados. |
| `ReceivablesView.vue` | Cuentas por cobrar, estados, filtros, búsqueda, detalle y registro de pago completo simulado. |
| `MonthlySummaryView.vue` | Indicadores del periodo, gráfico semanal, desglose de gastos, ventas y operaciones principales. |
| `PlaceholderView.vue` | Componente de placeholder existente; no corresponde a una ruta activa del router. |

### Componentes

- `common/`: `AppHeader`, `AppSidebar`, `AppBottomNav`, `BadgeStatus`, `QuickActions` y `StatCard`.
- `dashboard/`: `CashChart`, `NewOperationModal`, `OperationsSummary`, `PriorityCollections`, `RecentOperations` y `TopProducts`.
- `operations/`: `OperationFormModal` y `OperationDetailModal`.
- `receivables/`: `PaymentModal` y `ReceivableDetailModal`.

## Rutas

Definidas en `src/router/index.js` con `createWebHistory`:

| Ruta | Vista | Estado |
| --- | --- | --- |
| `/login` | Inicio de sesión | Pública |
| `/` | Dashboard | Protegida por JWT; datos mock |
| `/operaciones` | Compras y ventas | Protegida por JWT; datos mock |
| `/cobros` | Cuentas por cobrar | Protegida por JWT; datos mock |
| `/resumen` | Resumen mensual | Protegida por JWT; datos mock |
| `/dashboard` | Redirección a `/` | Activa |
| Ruta desconocida | Redirección a `/` | Activa |

Una visita no autenticada a una ruta protegida se envía a `/login`; después del login se recupera la ruta solicitada. Una sesión válida que abre `/login` va al Dashboard. El layout de login no muestra header, sidebar ni navegación inferior.

## Datos mock y comportamiento local

| Archivo | Contenido usado por el prototipo |
| --- | --- |
| `src/data/dashboardMock.js` | Negocio y periodo de ejemplo, KPI, flujo semanal, cobros prioritarios, operaciones recientes y productos destacados. |
| `src/data/operationsMock.js` | Operaciones, clientes, catálogo de productos, proveedores y categorías de gastos. |
| `src/data/receivablesMock.js` | Cuentas por cobrar y datos de detalle asociados. |
| `src/data/monthlySummaryMock.js` | Datos del resumen por periodo, incluidos indicadores, desglose y actividad. |

Las vistas de operaciones y cobros copian sus mocks a estado local para simular altas y pagos. No escriben en almacenamiento del navegador, no persisten entre recargas y no actualizan de forma compartida los otros módulos. Los pagos disponibles son completos; no hay pagos parciales.

## Design tokens y responsive

`src/assets/styles/main.css` define variables CSS compartidas para colores de marca y estados, superficies, tipografía, radios, sombras, espacios (`--space-*`) y layout (`--layout-*`). El gráfico añade tokens como `--chart-min-height`, `--chart-bar-width`, `--chart-series-gap`, `--chart-group-gap` y `--chart-axis-width`. Los componentes complementan estos valores con estilos scoped.

El responsive está implementado mediante media queries distribuidas entre el layout, las vistas y los componentes:

- El Dashboard usa dos columnas a partir de 1280 px y se apila por debajo.
- El sidebar se convierte en drawer hasta 1023 px.
- La navegación inferior se muestra hasta 767 px.
- Operaciones, cobros, resumen y modales ajustan sus grillas y controles en breakpoints propios.
- En pantallas estrechas, el desplazamiento horizontal de contenido se limita a componentes que lo requieren, como el gráfico.

## Accesibilidad

Hay medidas puntuales implementadas: skip link al contenido principal, landmarks y etiquetas ARIA en áreas relevantes, estados de foco visible, anuncios `aria-live` para feedback, controles de teclado en diálogos y soporte de movimiento reducido en el gráfico.

Esto **no representa cumplimiento completo de accesibilidad**. No se ha documentado una auditoría formal, validación integral con lectores de pantalla ni verificación de todos los criterios WCAG.

## Variables de entorno

La URL del Backend se configura con Vite. Crea un `.env.local` a partir de `.env.example`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Reinicia Vite después de cambiar variables `VITE_*`. No guardes `.env.local` en Git. La URL base se lee en `src/services/apiClient.js`; los componentes no contienen URLs de Backend.

### Contrato JWT integrado

Se usan únicamente estas rutas documentadas:

| Método | Ruta | Contrato |
| --- | --- | --- |
| `POST` | `/api/auth/login/` | Request `{ "username": "...", "password": "..." }`; respuesta `{ "access": "...", "refresh": "...", "usuario": { "id", "username", "nombre", "email", "es_admin" } }`. |
| `POST` | `/api/auth/refresh/` | Request `{ "refresh": "..." }`; respuesta con `access` y un `refresh` rotado. |
| `POST` | `/api/auth/logout/` | Request `{ "refresh": "..." }`; invalida el refresh. Backend confirma `200`; el cliente limpia ambos tokens incluso si la llamada falla. |
| `GET` | `/api/auth/perfil/` | Requiere `Authorization: Bearer <access>` y devuelve `id`, `username`, `nombre`, `email` y `es_admin`. |

No existe registro público; las cuentas las crea un administrador. Los errores documentados son `401` para credenciales inválidas y `429` al superar 10 intentos de login por minuto. El mensaje de credenciales inválidas es “Usuario o contraseña incorrectos.”. Los errores de refresh inválido se manejan como sesión expirada sin mostrar respuestas sensibles.

### Almacenamiento y expiración

El Backend recomienda `localStorage`: access en `cc_access` y refresh en `cc_refresh`. El access dura 30 minutos y el refresh 7 días por defecto (configurables en Backend). Al recibir `401` en una petición protegida, el cliente comparte un único refresh concurrente, guarda el par rotado y reintenta esa petición una sola vez. Si refresh falla, se eliminan ambos tokens, se redirige al login y se conserva la ruta solicitada como contexto.

El logout invalida el refresh en Backend y elimina ambos valores locales. `localStorage` persiste tras recargar, pero es accesible desde JavaScript; un XSS podría robar tokens. No son cookies `HttpOnly`, no se registran en consola y no se muestran en mensajes de error. Esta estrategia debe revisarse antes de producción.

### CORS

Backend permite por defecto `http://localhost:5173` y `http://127.0.0.1:5173`. Al publicar el frontend en otro origen, ese origen debe agregarse a `CORS_ALLOWED_ORIGINS` en Backend. La API usa JSON y no depende de cookies.

## Deploy en Vercel

[Ver prototipo desplegado en Vercel](https://tdcajaclara-cajaclara-eml0tsuhf-jltamayocabello-droids-projects.vercel.app/)

El deploy es una demostración con datos simulados; no persiste cambios ni se conecta al Backend.

## Integración futura con Backend

La autenticación ya consume Backend; las vistas financieras todavía no realizan solicitudes. El Dashboard, Operaciones, Cobros y Resumen conservan sus mocks.

Antes de conectar esos módulos se deben respetar sus contratos de periodo, operaciones, cobros, estados y errores. La [guía de integración UX/Frontend con Backend](../../INTEGRACION-BACKEND.md) detalla las limitaciones y dependencias conocidas. Actualmente todos los usuarios autenticados acceden al mismo negocio; Backend no filtra por negocio individual.

Pasos técnicos previstos:

1. Acordar los contratos financieros y formatos con Backend y Análisis de Datos.
2. Sustituir los mocks gradualmente y adaptar respuestas a los modelos de vista.
3. Persistir y sincronizar cambios, con estados de carga, error y vacío.
4. Validar formularios, permisos y flujos financieros conectados.

## Pruebas y calidad

No hay suite de pruebas automatizadas, comandos de lint ni formateo en `package.json`. El build disponible es:

```bash
npm run build
```

El build se ejecutó correctamente al actualizar esta documentación.

## Limitaciones

- Solo autenticación tiene conexión con Backend; los módulos financieros siguen simulados.
- Los mocks de cada módulo son independientes y no se sincronizan.
- La autenticación JWT usa `localStorage` y no se ha hecho una auditoría de seguridad de producción.
- No hay pagos parciales.
- No se ha completado una auditoría de accesibilidad.
- `PlaceholderView.vue` existe, pero no está asociado a una ruta activa.

## Roadmap técnico

1. Definir y validar los contratos financieros de API.
2. Conectar gradualmente resumen, operaciones y cuentas por cobrar.
3. Añadir persistencia, sincronización y manejo de errores/carga.
4. Incorporar pruebas automatizadas para rutas, autenticación y flujos críticos.
5. Completar validación de accesibilidad y revisar almacenamiento de tokens para producción.
