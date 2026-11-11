# Caja Clara — Enlaces y Recursos del Módulo de Datos

Accesos directos a la documentación compartida, diagramas editables y seguimiento de tareas del equipo de datos.

---

## 1. Enlaces Rápidos

| Recurso | Plataforma | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| **Hoja de cálculo — Etapa 1** | Google Sheets | Documento principal que abarca el desarrollo y análisis de la Etapa 1. | [Abrir hoja de cálculo](https://docs.google.com/spreadsheets/d/12chBEkVJYOFP88ECwylW87ismV8wLpw1tnJFDt72-XU/edit?gid=1319745633#gid=1319745633) |
| **Diagrama MER editable** | Lucidchart | Versión editable del Modelo Entidad-Relación (exportado en `Etapas_1-2-3/Etapa_1 Diagrama_MER.svg`). | [Abrir diagrama en Lucidchart](https://lucid.app/lucidchart/769d69ba-606e-4c40-8cd4-9b672c10f0b3/edit?viewport_loc=-551%2C-271%2C3403%2C2074%2CDQNfy2d46xWYV&invitationId=inv_256da6d8-f6cf-4f76-b8f6-62b2b9d926e2) |
| **Planilla de tareas** | Google Sheets | Registro central donde se asignan y gestionan las tareas de cada integrante. | [Abrir planilla de tareas](https://docs.google.com/spreadsheets/d/1v4IA5O-WuZS_2oWIPyO_wxcNDM1rKc-884uxH0VgssI/edit?gid=0#gid=0) |

---

## 2. Estructura Local (`datos/`)

```text
datos/
├── Etapas_1-2-3/
│   ├── Etapa_1 Diagrama_MER.svg
│   ├── Etapa_2 Limpieza de datos/
│   │   ├── limpieza_datos_etapa2.ipynb
│   │   ├── resumen_limpieza_datos.md
│   │   ├── Tareas.xlsx
│   │   ├── ventas_db.ventas.csv
│   │   ├── ventas_limpias.csv
│   │   └── ventas_originales_fuente.csv
│   └── Etapa_3 Elaboracion de tablas/
│       ├── Etapa_3_Elaboración_de_Tablas.ipynb
│       ├── cliente.csv
│       ├── cuenta_por_cobrar.csv
│       ├── detalle_venta.csv
│       ├── gastos_insumo.csv
│       ├── producto.csv
│       └── venta.csv
├── Etapas_4-5-6/
├── Etapas_7-8/
├── Proyecto_FInal/
└── resumen.md
```

### Documentos de referencia local

- [Diagrama MER (SVG)](./Etapas_1-2-3/Etapa_1%20Diagrama_MER.svg): versión exportada del modelo entidad-relación de la Etapa 1.
- [Resumen de limpieza de datos](./Etapas_1-2-3/Etapa_2%20Limpieza%20de%20datos/resumen_limpieza_datos.md): auditoría de anomalías, transformaciones y criterios aplicados en la Etapa 2.
- [Notebook de limpieza (Etapa 2)](./Etapas_1-2-3/Etapa_2%20Limpieza%20de%20datos/limpieza_datos_etapa2.ipynb): flujo técnico de depuración y estandarización.
- [Notebook de elaboración de tablas (Etapa 3)](./Etapas_1-2-3/Etapa_3%20Elaboracion%20de%20tablas/Etapa_3_Elaboración_de_Tablas.ipynb): generación de las tablas relacionales en formato CSV.
