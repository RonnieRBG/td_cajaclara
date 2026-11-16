# Diseño UX y Frontend — CajaClara

Este documento resume el proceso de diseño de CajaClara: investigación, definición del MVP, user flows, wireframes y estado del prototipo de alta fidelidad.

Para detalles de Vue, estructura del código, dependencias y ejecución, consulta el [README técnico del prototipo](./prototype/cajaclara-ui/README.md).

## Producto y problema

CajaClara busca ayudar a micronegocios a registrar ventas, compras y gastos, comprender el saldo de un periodo y dar seguimiento a sus cuentas por cobrar. Hoy esas tareas suelen repartirse entre cuadernos, conversaciones y aplicaciones bancarias, lo que dificulta revisar el estado del negocio y recordar cobros pendientes.

La experiencia prioriza un lenguaje cotidiano, información financiera resumida y tareas frecuentes que puedan completarse con pocos pasos.

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

## Alcance del MVP

### Incluido en la definición del MVP

- Consulta del estado financiero del negocio.
- Registro de ventas pagadas o pendientes.
- Registro de compras y otros gastos.
- Consulta de operaciones.
- Seguimiento de cuentas por cobrar y registro de pago completo.
- Resumen mensual.

### Fuera del alcance actual

- Pagos parciales.
- Inventario o stock automático.
- Facturación electrónica.
- Integraciones reales con WhatsApp o correo.
- Reportes tributarios y cálculos contables definitivos.

El alcance del MVP describe la propuesta funcional; no significa que exista persistencia o conexión productiva. El prototipo actual trabaja con datos simulados y sus interacciones no se guardan.

## User flows

Los [user flows](./user-flows/userflows-cajaclara.md) describen recorridos de acceso y configuración, consulta financiera, registro de movimientos, cobros y resumen mensual. Los diagramas PNG facilitan su revisión en GitHub.

Los recorridos de acceso y configuración son parte de la definición UX, no rutas de autenticación implementadas en el prototipo.

## Wireframes

Los PNG exportados de los wireframes muestran la versión móvil para facilitar su revisión directamente en GitHub. Los HTML y CSS conservan las versiones navegables y responsive:

- [Dashboard](./wireframes/dashboard.html) · [PNG móvil](./wireframes/dashboard.png)
- [Compras y ventas](./wireframes/movimientos.html) · [PNG móvil](./wireframes/movimientos.png)
- [Cuentas por cobrar](./wireframes/cuentas-cobrar.html) · [PNG móvil](./wireframes/cuentas-cobrar.png)
- [Estilos compartidos](./wireframes/styles.css)

## Prototipo de alta fidelidad — Semana 3

### Estado implementado

- Dashboard.
- Compras y ventas.
- Cuentas por cobrar.
- Resumen mensual.
- Diseño responsive para escritorio, tablet y móvil.
- Ajustes de espaciado, gráficos, altura de componentes y distribución del Dashboard.
- Estados principales, feedback y confirmaciones simuladas.

El [prototipo desplegado en Vercel](https://tdcajaclara-cajaclara-eml0tsuhf-jltamayocabello-droids-projects.vercel.app/) utiliza datos simulados. Las operaciones y los pagos no persisten, no se sincronizan entre módulos y todavía no existe integración real con Backend.

La implementación técnica, las rutas y las limitaciones de cada módulo están documentadas en el [README técnico](./prototype/cajaclara-ui/README.md).

### Estado por etapa

| Etapa | Trabajo | Estado |
| --- | --- | --- |
| Semana 1 | Benchmarking, definición del problema y User Persona | Completada |
| Semana 2 | User flows y wireframes responsive | Completada |
| Semana 3 | Prototipo de alta fidelidad y ajustes responsive | Implementado; continúa como prototipo simulado |

## Alineación con Backend y Análisis de Datos

La experiencia representa las operaciones de esta forma:

- Venta pagada: entrada de dinero.
- Compra u otro gasto: salida de dinero.
- Venta pendiente: saldo asociado a una cuenta por cobrar.
- Saldo del periodo: ingresos menos compras y gastos.

UX revisó el modelo analítico compartido por Análisis de Datos (`cliente`, `producto`, `venta`, `detalle_venta`, `cuenta_por_cobrar` y `gastos_insumo`). Sus conceptos no se consideran automáticamente contratos de API.

El Backend Django dispone de modelos propios y de un endpoint de resumen mensual, pero su respuesta actual no cubre los filtros, el detalle de operaciones ni el desglose semanal que necesita la interfaz. El prototipo Vue no consume ese endpoint. Los contratos, dependencias y decisiones pendientes se detallan en la [guía de integración UX/Frontend con Backend](./INTEGRACION-BACKEND.md).

## Roadmap UX

### Semana 4 — Pruebas de usabilidad

- Probar tareas clave del Dashboard, registro de movimientos y seguimiento de cobros con emprendedores.
- Registrar éxito de tareas, dificultades, observaciones y tiempos.
- Priorizar problemas de comprensión y navegación encontrados durante las pruebas.

### Semana 5 — Iteración y cierre

- Analizar resultados y priorizar mejoras.
- Refinar el prototipo y validar los cambios.
- Documentar decisiones, resultados y propuesta final.
