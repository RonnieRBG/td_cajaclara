# User Flows - CajaClara

## Proyecto

CajaClara es una plataforma de gestión financiera para emprendedores y pequeñas empresas que permite controlar ingresos, gastos, flujo de caja y cuentas por cobrar.

---

# User Flow 1: Acceder a CajaClara y Consultar Estado Financiero

## Objetivo

Permitir que el usuario acceda a su cuenta de forma segura y visualice rápidamente la situación financiera de su negocio.

```mermaid
flowchart TD
    A[Ingresar a CajaClara] --> B[Pantalla Login]

    B --> C[Ingresar Credenciales]

    C --> D{Credenciales válidas?}

    D -->|No| E[Mostrar Error]
    E --> B

    D -->|Sí| F{Negocio configurado?}

    F -->|No| G[Ingresar Nombre del Negocio]
    G --> H[Guardar Configuración]
    H --> I[Dashboard]

    F -->|Sí| I[Dashboard]

    I --> J[Ver Nombre del Negocio]

    I --> K[Ver Total Ingresos]
    I --> L[Ver Total Gastos]
    I --> M[Ver Flujo de Caja]
    I --> N[Visualizar Gráfico Financiero]

    K --> O[Toma de Decisiones]
    L --> O
    M --> O
    N --> O
```

### Resultado esperado

El usuario accede de forma segura a la aplicación y comprende rápidamente el estado financiero de su negocio.

---

# User Flow 2: Registrar Movimiento

## Objetivo

Permitir registrar ingresos y gastos de forma rápida y sencilla.

```mermaid
flowchart TD
    A[Dashboard] --> B[Nuevo Movimiento]

    B --> C[Seleccionar Tipo]

    C --> D[Ingreso]
    C --> E[Gasto]

    D --> F[Seleccionar Categoría]
    E --> F

    F --> G[Ingresar Monto]

    G --> H[Seleccionar Fecha]

    H --> I[Agregar Descripción Opcional]

    I --> J[Guardar Movimiento]

    J --> K[Dashboard Actualizado]
```

### Resultado esperado

El movimiento queda registrado y los indicadores financieros se actualizan automáticamente.

---

# User Flow 3: Gestionar Cuenta por Cobrar

## Objetivo

Permitir gestionar pagos pendientes de clientes.

```mermaid
flowchart TD
    A[Dashboard] --> B[Cuentas por Cobrar]

    B --> C[Ver Lista de Deudores]

    C --> D[Seleccionar Cliente]

    D --> E[Detalle de Cuenta]

    E --> F[Registrar Pago]
    E --> G[Contactar Cliente]

    F --> H[Actualizar Estado]

    H --> I[Deuda Pagada]
```

### Resultado esperado

El usuario puede realizar seguimiento de clientes con pagos pendientes y actualizar el estado de sus deudas.

---

# User Flow 4: Revisar Resumen Mensual

## Objetivo

Permitir analizar el rendimiento financiero mensual del negocio.

```mermaid
flowchart TD
    A[Dashboard] --> B[Resumen Mensual]

    B --> C[Consultar Ingresos]
    B --> D[Consultar Gastos]
    B --> E[Consultar Flujo de Caja]

    C --> F[Analizar Resultados]
    D --> F
    E --> F
```

### Resultado esperado

El usuario obtiene una visión consolidada del desempeño financiero del período.

---

# User Flow General del MVP

## Objetivo

Representar el recorrido principal del usuario dentro de CajaClara.

```mermaid
flowchart TD
    A[Login] --> B[Dashboard]

    B --> C[Movimientos]
    B --> D[Cuentas por Cobrar]
    B --> E[Resumen Mensual]

    C --> B
    D --> B
    E --> B
```

### Resultado esperado

El usuario puede navegar entre las funcionalidades principales del sistema desde el Dashboard.

---

# Pantallas Relacionadas

| Pantalla | User Flow |
|-----------|------------|
| Login | Acceder a CajaClara y Consultar Estado Financiero |
| Configuración Negocio | Acceder a CajaClara y Consultar Estado Financiero |
| Dashboard | Acceder a CajaClara y Consultar Estado Financiero |
| Movimientos | Registrar Movimiento |
| Cuentas por Cobrar | Gestionar Cuenta por Cobrar |
| Detalle Deudor | Gestionar Cuenta por Cobrar |
| Resumen Mensual | Revisar Resumen Mensual |

---

# Alcance MVP

Las funcionalidades consideradas para el MVP son:

- Inicio de sesión
- Configuración del negocio
- Dashboard financiero
- Registro de ingresos
- Registro de gastos
- Cuentas por cobrar
- Gestión de deudores
- Resumen mensual
- Flujo de caja

---

# Responsable

UX Designer: Jorge Tamayo

Proyecto: CajaClara

Proyecto Colaborativo Talento Digital

https://colaboratd.cl/

Año: 2026