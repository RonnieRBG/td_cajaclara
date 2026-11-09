# Diseño UX - CajaClara

Documentación del proceso de diseño UX de **CajaClara**, una aplicación de caja y gestión financiera sencilla para micronegocios.

**Proyecto:** Proyecto Colaborativo Talento Digital  
**Área:** Diseño UX y Frontend  
**Estado:** Semana 3, prototipo de alta fidelidad y ajustes de interfaz  
**Rama de trabajo:** [`ux`](https://github.com/RonnieRBG/td_cajaclara/tree/ux)

---

## Tabla de contenidos

- [Descripción del proyecto](#descripción-del-proyecto)
- [Estado actual - Semana 3](#estado-actual---semana-3)
- [Problema de diseño](#problema-de-diseño)
- [Usuario principal](#usuario-principal)
- [Principios UX](#principios-ux)
- [Alcance del MVP](#alcance-del-mvp)
- [Investigación y definición](#investigación-y-definición)
- [User flows](#user-flows)
- [Wireframes](#wireframes)
- [Prototipo de alta fidelidad](#prototipo-de-alta-fidelidad)
- [Alineación con Backend y Análisis de Datos](#alineación-con-backend-y-análisis-de-datos)
- [Estructura de la carpeta UX](#estructura-de-la-carpeta-ux)
- [Roadmap UX](#roadmap-ux)
- [Decisiones pendientes](#decisiones-pendientes)
- [Responsable](#responsable)

---

## Descripción del proyecto

**CajaClara** está diseñada para pequeños comercios que necesitan registrar ventas, compras y otros gastos, conocer el saldo del periodo y controlar el dinero pendiente de cobro sin utilizar conceptos contables complejos.

La aplicación adopta el modelo mental de una **caja registradora digital sencilla**:

```text
Comprar mercadería
        ↓
Registrar una salida de dinero
        ↓
Vender productos
        ↓
Registrar una entrada de dinero
        ↓
Controlar ventas pendientes
        ↓
Registrar cobros
```

El objetivo UX es que una persona pueda responder rápidamente:

1. ¿Cuánto vendí?
2. ¿Cuánto gasté?
3. ¿Cuál es el saldo del periodo?
4. ¿Quién me debe dinero?
5. ¿Qué cobros requieren atención?

---

## Estado actual - Semana 3

### Completado

- Benchmarking competitivo.
- User Persona principal.
- Definición del problema y objetivos UX.
- Alcance del MVP.
- User flows actualizados en Markdown y Mermaid.
- Exportación de los user flows a PNG.
- Wireframes responsive en HTML y CSS.
- Navegación entre los wireframes principales.
- Revisión de la información entregada por Backend.
- Revisión del modelo relacional y de las seis tablas de Análisis de Datos.
- Definición inicial del sistema visual.
- **Dashboard de alta fidelidad desarrollado con Vue 3 y Vite.**
- **Compras y ventas** implementada en `/operaciones`, con operaciones simuladas y formularios locales.
- **Cuentas por cobrar** implementada en `/cobros`, con búsqueda, filtros, orden por vencimiento, detalle y registro de pago completo simulado.
- Dashboard y módulos operativos adaptados a escritorio, tablet y móvil.

### En desarrollo durante la Semana 3

- Ajustes de interfaz y consistencia visual.
- Resumen mensual, que continúa como placeholder.
- Estados de error y carga para una futura integración con Backend.
- Pruebas de usabilidad y refinamiento a partir de sus resultados.
- Preparación del prototipo navegable para las pruebas de usabilidad.

---

## Problema de diseño

Muchos micronegocios utilizan cuadernos, mensajes, memoria personal o aplicaciones bancarias para controlar sus finanzas. Esto provoca dificultades para:

- Diferenciar ventas, compras y otros gastos.
- Comprender cuánto dinero queda disponible.
- Recordar qué clientes tienen pagos pendientes.
- Revisar rápidamente el estado del negocio.
- Tomar decisiones basadas en información organizada.

CajaClara busca reducir esta complejidad mediante una interfaz clara, rápida y cercana.

---

## Usuario principal

La User Persona principal representa a una persona responsable de un micronegocio que:

- Tiene conocimientos contables básicos o informales.
- Utiliza herramientas como cuadernos, WhatsApp y aplicaciones bancarias.
- Dedica la mayor parte del tiempo a vender, producir o atender clientes.
- Necesita registrar una operación en pocos pasos.
- Quiere separar el dinero personal del dinero del negocio.
- Necesita saber quién le debe dinero y cuándo debería pagar.

### Necesidades principales

- Dashboard comprensible en pocos segundos.
- Registro rápido de ventas y gastos.
- Seguimiento de cuentas por cobrar.
- Lenguaje cotidiano.
- Interfaz accesible y responsive.

---

## Principios UX

### Claridad

La información financiera principal debe ser visible y entendible sin conocimientos contables avanzados.

### Simplicidad

La interfaz utiliza términos como **Venta**, **Compra**, **Otro gasto**, **Saldo del periodo** y **Dinero pendiente**.

### Rapidez

Las acciones frecuentes deben requerir pocos pasos y presentar valores preseleccionados cuando sea razonable.

### Control

El usuario debe distinguir fácilmente entradas, salidas y cobros pendientes.

### Consistencia

Los nombres, estados, colores y patrones de interacción deben mantenerse en todas las pantallas.

### Accesibilidad

Los estados no deben depender solamente del color. La interfaz debe mantener foco visible, contraste suficiente, etiquetas claras y navegación por teclado.

---

## Alcance del MVP

### Incluido

- Acceso a CajaClara.
- Identificación del negocio.
- Dashboard financiero.
- Registro de ventas.
- Venta física o en línea.
- Venta pagada o pendiente.
- Ventas con uno o varios productos.
- Registro de compras o gastos de insumo.
- Registro de otros gastos.
- Consulta y filtrado de operaciones.
- Gestión de cuentas por cobrar.
- Registro de pago completo.
- Resumen mensual.

### Fuera del alcance actual

- Inventario automático.
- Control de stock en tiempo real.
- Gestión avanzada de proveedores.
- Pagos parciales.
- Facturación electrónica.
- Integración real con WhatsApp o correo.
- Reportes tributarios.
- Cálculo contable definitivo de margen o rentabilidad.

---

## Investigación y definición

### Benchmarking

Se analizaron soluciones financieras y de gestión para identificar patrones útiles, problemas recurrentes y oportunidades para CajaClara.

Hallazgos principales:

- Los dashboards simples facilitan la comprensión del negocio.
- Las herramientas contables tradicionales pueden resultar técnicas para micronegocios.
- Registrar operaciones debe ser rápido.
- Las cuentas por cobrar son una funcionalidad relevante para diferenciar la propuesta.
- El lenguaje debe describir acciones cotidianas, no conceptos contables.

### User Persona

La documentación de la User Persona se encuentra dentro de:

```text
ux/research/
```

---

## User flows

Los flujos actuales cubren:

- Acceso y llegada al Dashboard.
- Configuración del negocio.
- Consulta del estado financiero.
- Registro de ventas, compras y otros gastos.
- Gestión de cuentas por cobrar.
- Registro de pago completo.
- Consulta del resumen mensual.

Archivos principales:

```text
ux/user-flows/
├── userflows-cajaclara.md
├── flow-login-dashboard.png
├── flow-configurar-negocio.png
├── flow-estado-financiero.png
├── flow-movimientos.png
├── flow-cobros.png
└── flow-resumen-mensual.png
```

El archivo `userflows-cajaclara.md` es la fuente editable. Los PNG facilitan la revisión visual desde GitHub.

---

## Wireframes

Los wireframes se desarrollaron en HTML y CSS para conservar la navegación y permitir la revisión de los recorridos antes de pasar a alta fidelidad.

Pantallas principales:

- Dashboard.
- Compras y ventas.
- Cuentas por cobrar.
- Acceso y configuración.
- Resumen mensual.

### Aclaración sobre los PNG

> **Importante:** los archivos PNG de los wireframes representan la versión móvil y se publican para facilitar su revisión visual en GitHub. La versión funcional y responsive se conserva en los archivos HTML y CSS. El prototipo de alta fidelidad prioriza escritorio.

Los **wireframes exportados en PNG corresponden a la versión móvil** de las pantallas. Se incluyen para que el equipo pueda revisarlos rápidamente desde GitHub sin necesidad de abrir o ejecutar los archivos HTML.

Los archivos HTML y CSS siguen siendo la fuente navegable y responsive de los wireframes.

```text
ux/wireframes/
├── dashboard.html
├── movimientos.html
├── cuentas-cobrar.html
├── styles.css
└── *.png              # Versión móvil para revisión rápida
```

Aunque los PNG muestran la versión móvil, el proyecto completo está planteado como responsive.

---

## Prototipo de alta fidelidad

### Dashboard completado

El prototipo de alta fidelidad se desarrolla con **Vue 3**, **Vite** y componentes reutilizables. Incluye Dashboard, Compras y ventas y Cuentas por cobrar; el resumen mensual permanece como placeholder.

El Dashboard prioriza escritorio y organiza el contenido en filas independientes: flujo de caja junto a cobros prioritarios, movimientos recientes a ancho completo y resumen de actividad junto a productos más vendidos. En tablet y móvil las secciones se reorganizan en una columna.

El Dashboard incluye:

- Nombre del negocio.
- Periodo consultado.
- Acciones rápidas.
- Ventas del mes.
- Compras y gastos.
- Saldo del periodo.
- Pendiente por cobrar.
- Gráfico de entradas y salidas.
- Resumen de operaciones.
- Operaciones recientes.
- Cobros prioritarios.

### Compras y ventas y Cuentas por cobrar

- **Compras y ventas (`/operaciones`):** búsqueda, filtros, indicadores, detalle y registro local de ventas, compras y gastos.
- **Cuentas por cobrar (`/cobros`):** estados pendiente, vencida y pagada; indicadores, filtros, búsqueda, orden por vencimiento, detalle y pago completo.
- Los mocks son exclusivos del prototipo. Las altas y pagos se mantienen en el estado local de cada vista, no se persisten ni se sincronizan entre módulos, y no llaman al Backend.

Para detalles técnicos, estructura de componentes y rutas consulta el [README del prototipo Vue](./prototype/cajaclara-ui/README.md).

### Sistema visual inicial

- Paleta principal verde, asociada a orden, control y confianza.
- Escala de colores neutros.
- Colores semánticos para estados de éxito, advertencia, error e información.
- Tipografía Plus Jakarta Sans y fuentes del sistema.
- Escala de espaciado basada en múltiplos de cuatro.
- Botones, tarjetas KPI, badges, navegación y controles reutilizables.

### Datos del prototipo

Los valores visibles en el Dashboard son simulados y se utilizan únicamente para demostrar la experiencia. No representan resultados reales del dataset ni respuestas actuales de la API.

---

## Alineación con Backend y Análisis de Datos

### Correspondencia UX con Backend

```text
Venta pagada
= Entrada de dinero

Compra o gasto de insumo
= Salida de dinero

Otro gasto
= Salida de dinero

Venta pendiente
= Factura relacionada con una cuenta por cobrar

Saldo del periodo
= Ventas - Compras y gastos
```

### Modelo analítico revisado

El equipo de Análisis de Datos entregó seis tablas:

- `cliente`
- `producto`
- `venta`
- `detalle_venta`
- `cuenta_por_cobrar`
- `gastos_insumo`

Implicaciones para UX:

- Una venta puede incluir varios productos.
- Los productos deben identificarse por nombre, código y categoría cuando sea necesario.
- Las ventas pueden ser físicas o en línea.
- Una venta pendiente se asocia a un cliente, una factura, un monto y una fecha de vencimiento.
- Los gastos de insumo disponen de producto, fecha y monto.
- Cantidad comprada, proveedor y documento de compra no están confirmados para el MVP.
- `unidad_negocio` no se utiliza como filtro principal porque actualmente solo contiene un valor.

---

## Estructura de la carpeta UX

```text
ux/
├── research/
│   ├── benchmarking.md
│   └── user-persona.md
├── user-flows/
│   ├── userflows-cajaclara.md
│   └── *.png
├── wireframes/
│   ├── dashboard.html
│   ├── movimientos.html
│   ├── cuentas-cobrar.html
│   ├── styles.css
│   └── *.png
├── prototype/
│   └── cajaclara-ui/          # Prototipo Vue 3 de alta fidelidad
└── README.md
```

La ubicación concreta del proyecto Vue debe conservar la estructura existente en la rama `ux` si difiere del ejemplo anterior.

---

## Roadmap UX

### Semana 1 - Investigación

- Benchmarking.
- Hallazgos UX.
- User Persona.

**Estado:** completado.

### Semana 2 - Definición y wireframes

- User flows.
- Wireframes.
- Conectividad entre pantallas.
- Preparación del sistema visual.

**Estado:** completado.

### Semana 3 - Alta fidelidad y estados de interfaz

- Dashboard de alta fidelidad.
- Extensión del sistema visual.
- Compras y ventas en alta fidelidad.
- Cuentas por cobrar en alta fidelidad.
- Estados vacíos y confirmaciones principales.
- Estados de error.
- Revisión responsive.

**Estado:** en progreso. Dashboard, Compras y ventas y Cuentas por cobrar ya están implementados en el prototipo; errores y carga siguen pendientes.

### Semana 4 - Test de usabilidad

Prueba con cinco emprendedores.

Tareas previstas:

- Consultar el Dashboard.
- Registrar una venta.
- Registrar un gasto.
- Consultar una cuenta por cobrar.
- Registrar un pago.

Se documentarán éxito, dificultades, observaciones y tiempos.

### Semana 5 - Iteración final

- Análisis de resultados.
- Priorización de hallazgos.
- Mejoras del prototipo.
- Prototipo final.
- Documentación de resultados y decisiones.

---

## Decisiones pendientes

### Backend y datos

- Confirmar los endpoints de clientes, productos, ventas y detalle de venta.
- Confirmar la creación automática de una cuenta por cobrar desde una venta pendiente.
- Definir si el estado `VENCIDA` será calculado o almacenado.
- Confirmar cómo se registrará el pago completo.
- Aclarar o renombrar el campo `fecha_cobro` como fecha esperada de pago o vencimiento.
- Confirmar si los clientes podrán crearse durante una venta.
- Confirmar si el canal físico o en línea será obligatorio.
- Definir si las compras incluirán cantidad, proveedor y documento.

### Diseño

- Completar las siguientes pantallas de alta fidelidad.
- Diseñar estados vacíos, de error, carga y éxito.
- Validar accesibilidad y navegación por teclado.
- Preparar el prototipo navegable para los tests.
- Revisar el sistema visual con el equipo antes de la prueba de usabilidad.

---

## Responsable

**UX Designer:** Jorge Tamayo  
**Proyecto:** CajaClara  
**Iniciativa:** Proyecto Colaborativo Talento Digital  
**Año:** 2026
