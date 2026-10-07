# Prueba Técnica · Analista de Datos

Resolución de la prueba con el archivo `RequerimientosPruebaDatos.csv`: el ciclo completo del dato, desde la ingesta en SQL Server hasta el informe ejecutivo.

| | Antes | Después |
|---|---:|---:|
| Registros | 7,158 | **7,075** (83 duplicados retirados) |
| Tickets únicos | 3,407 | **3,406** |
| Celdas nulas o vacías (sin contar `ID`) | 304 | **0** |
| Horas totales | 17,208.9 | **16,978.8** |

**Medidas:** Q Tickets **3,406** · Q Horas **16,979** · Promedio Horas x Ticket **4.98** · % Resueltos **98.4%**

---

## Entregables

| # | Lo que pide la prueba | Dónde está |
|---|---|---|
| 1 | Archivo de datos limpios | [`data/clean/RequerimientosPruebaDatos_Limpio.csv`](data/clean/RequerimientosPruebaDatos_Limpio.csv) · versión [`.xlsx`](data/clean/RequerimientosPruebaDatos_Limpio.xlsx) con diccionario y bitácora |
| 2 | Scripts SQL de carga e inspección | [`sql/`](sql/) (01 DDL · 02 BULK INSERT · 03 perfilado · 04 carga del limpio) · salidas en [`docs/evidencias/`](docs/evidencias/) |
| 3 | Script / cuaderno de limpieza y EDA | [`python/limpieza.py`](python/limpieza.py) · [`notebooks/EDA_Requerimientos.ipynb`](notebooks/EDA_Requerimientos.ipynb) (ya ejecutado, con resultados) |
| 4 | Archivo de Power BI u otra herramienta de visualización | Proyecto **Power BI PBIP** en [`powerbi/pbip/`](powerbi/pbip/) (abrir `Dashboard_Requerimientos.pbip`; pasos en [`powerbi/GUIA_POWER_BI.md`](powerbi/GUIA_POWER_BI.md)) · dashboard HTML [`dashboard/Dashboard_Requerimientos.html`](dashboard/Dashboard_Requerimientos.html) · DAX en [`powerbi/medidas_dax.dax`](powerbi/medidas_dax.dax) |
| 5 | Informe ejecutivo en PDF | [`informe/Informe_Ejecutivo.pdf`](informe/Informe_Ejecutivo.pdf) (2 páginas) |
| 6 | Video explicativo | Guion en [`docs/GUION_VIDEO.md`](docs/GUION_VIDEO.md) (la grabación la hace el postulante) |
| – | Correo de envío | Borrador en [`docs/CORREO_ENVIO.md`](docs/CORREO_ENVIO.md) |

## Estructura

```
├── data/
│   ├── raw/RequerimientosPruebaDatos.csv          # original, sin modificar
│   └── clean/                                     # salida del Módulo 2 (.csv, .xlsx, log)
├── sql/
│   ├── 01_creacion_tablas.sql                     # BD, staging y tablas tipadas
│   ├── 02_ingesta_bulk_insert.sql                 # procedimiento de carga con BULK INSERT
│   ├── 03_perfilado.sql                           # consultas de perfilado (Módulo 1.2)
│   └── 04_carga_datos_limpios.sql                 # carga del limpio + Antes vs Después
├── python/
│   ├── limpieza.py                                # Módulo 2
│   ├── generar_dashboard.py                       # Módulo 4 (HTML)
│   ├── generar_pbip.py                            # Módulo 4 (proyecto Power BI PBIP)
│   └── generar_informe.py                         # Módulo 5 (PDF)
├── notebooks/EDA_Requerimientos.ipynb             # Módulo 3
├── powerbi/
│   ├── pbip/Dashboard_Requerimientos.pbip         # proyecto Power BI (modelo TMDL + reporte PBIR)
│   ├── medidas_dax.dax                            # medidas requeridas + apoyo + Calendario
│   ├── power_query_requerimientos.m               # consulta de carga
│   └── GUIA_POWER_BI.md                           # abrir el PBIP, armado manual y valores de control
├── dashboard/                                     # dashboard HTML (abre sin internet)
├── informe/                                       # informe ejecutivo (.pdf y .html)
└── docs/                                          # inconsistencias, evidencias, guion, correo
```

## Cómo reproducir

```bash
pip install -r requirements.txt
```

1. **SQL Server (Módulo 1):** ejecutar en orden `sql/01`, `sql/02` y `sql/03` (SSMS o `sqlcmd`). En `02`, ajustar la ruta del CSV a una carpeta que lea el servicio de SQL Server.
2. **Limpieza (Módulo 2):** `python python/limpieza.py` → genera `data/clean/` e imprime la bitácora.
3. **EDA (Módulo 3):** abrir `notebooks/EDA_Requerimientos.ipynb` y ejecutar todo (o `jupyter nbconvert --to notebook --execute notebooks/EDA_Requerimientos.ipynb`).
4. **Dashboard (Módulo 4):**
   - Power BI: abrir `powerbi/pbip/Dashboard_Requerimientos.pbip` en Power BI Desktop (Windows, agosto 2025 o posterior), ajustar el parámetro `RutaArchivoCSV` y pulsar *Actualizar* (sección 0 de [`powerbi/GUIA_POWER_BI.md`](powerbi/GUIA_POWER_BI.md)). Para regenerarlo: `python python/generar_pbip.py`.
   - HTML: abrir `dashboard/Dashboard_Requerimientos.html` en el navegador. Para regenerarlo: `python python/generar_dashboard.py`.
5. **Informe (Módulo 5):** `python python/generar_informe.py --autor "Apellidos y Nombres"` (para el PDF hace falta `playwright install chromium`).
6. *(Opcional)* `sql/04_carga_datos_limpios.sql` carga el archivo limpio en SQL Server y compara Antes vs Después.

## Resumen por módulo

**Módulo 1 · Ingesta y perfilado (SQL Server).** Carga en dos capas: `stg.RequerimientosRaw` guarda el CSV tal cual (con número de línea de origen) y `dbo.Requerimientos` lo tipa (`DATE`, `TIME`, minutos y horas decimales). El procedimiento `dbo.usp_CargarRequerimientos` parametriza la ruta, corre en una transacción y devuelve un resumen de control. El perfilado responde los cuatro puntos pedidos y agrega una sección de hallazgos (duplicados, espacios duros, fechas imposibles, horas extremas, sobrecarga diaria).

**Módulo 2 · Limpieza.** 21 inconsistencias detalladas en [`docs/inconsistencias.md`](docs/inconsistencias.md). Reglas: duplicados (71 exactos + 12 que aparecen al estandarizar), categorías (estado, acción, sistema, código), fechas (22 imposibles + 32 vacías imputadas por posición cronológica) y horas (45 nulos imputados con la mediana de su acción, 55 extremos acotados a 10 h según el cerco Q3 + 3·IQR). Cada corrección deja un `Flag*` y los valores originales.

**Módulo 3 · EDA.** Horas por registro: media 2.40 · mediana 1.50 · moda 1.00 · desviación 2.58 · varianza 6.66 · IQR 2.33 · asimetría 1.75 · curtosis 2.10 → distribución sesgada a la derecha y leptocúrtica. Los proyectos son el 0.5% de los tickets y el 22% de las horas; las diferencias por tipo y por grupo son significativas (Kruskal-Wallis, p < 0.001).

**Módulo 4 · Dashboard.** Medidas DAX `[Q Tickets]`, `[Q Horas]`, `[Promedio Horas x Ticket]` y `[% Resueltos]` más medidas de apoyo. Visuales: tendencia mensual, anillo por Tipo, dispersión por Usuario y matriz Acción × Usuario, con filtros y filtrado cruzado. Se entrega como proyecto Power BI (PBIP: modelo `Requerimientos` + `Calendario` + `_Medidas`, página *Dashboard* con 15 visuales) y como dashboard HTML equivalente.

**Módulo 5 · Informe.** Capacidad copada (9.4 h por técnico y día), menos tickets y más horas por ticket (+78% de enero a junio), 67 tickets de más de 40 h que explican el 57% de las horas y un backlog anterior a 2026 que consume el 34.5%. Tres recomendaciones con meta medible.

## Supuestos

- **Grupo:** el archivo no tiene una columna *Grupo*; se usa `SISTEMA/ CANAL` como grupo funcional y se deriva `Equipo` (Datos / Aplicaciones) del catálogo de acciones.
- **Código = columna `REQ`.** Una fila es un registro de horas, por eso un código se repite sin ser duplicado.
- **% Resueltos** se calcula por ticket con su último estado (`EstadoTicket` ∈ {Cerrado, Resuelto}).
- **Power BI:** se entrega en formato de proyecto **PBIP** (texto, versionable en Git), que Power BI Desktop abre directamente y puede guardar como `.pbix`. El proyecto no incluye la caché de datos: al abrirlo hay que apuntar el parámetro `RutaArchivoCSV` al CSV limpio y actualizar.

## Validación realizada

- Scripts SQL ejecutados de principio a fin en **SQL Server 2022** (Docker); salidas en [`docs/evidencias/`](docs/evidencias/). Los cálculos de SQL y Python coinciden (7,075 filas, 3,406 tickets, 16,978.75 h, 55 extremos).
- Notebook ejecutado sin errores con los resultados guardados.
- Dashboard probado en Chromium (escritorio y móvil, tema claro y oscuro, filtros cruzados); sin errores en la consola.
- Proyecto PBIP (no hay Power BI Desktop en el entorno de generación, así que no se abrió en Desktop): sus JSON pasan los esquemas oficiales de Microsoft, el TMDL lo lee la librería oficial TOM y se re-serializa idéntico, y cada visual se contrastó con reportes PBIR reales escritos por Power BI Desktop 2026. Una revisión adversarial independiente no encontró bloqueos; sus hallazgos confirmados se corrigieron.
