# Guion para el video explicativo (8–10 minutos)

> El video debe grabarlo el postulante (p. ej. con OBS, Teams o Loom, compartiendo pantalla). Este guion ordena qué mostrar y qué decir en cada parte.

| Min | Qué se muestra | Qué se dice |
|---|---|---|
| 0:00–0:45 | `README.md` (tabla de entregables) | Presentación, objetivo de la prueba y cómo está organizado el repositorio: un entregable por módulo. |
| 0:45–2:30 | **Módulo 1** · `sql/01` a `03` en SSMS o Azure Data Studio | Diseño en dos capas: staging de texto + tabla tipada. Ejecutar `usp_CargarRequerimientos` y mostrar el resumen (7,158 filas, 22 fechas no convertibles). Recorrer el perfilado: 7,158 registros vs 3,407 códigos (3,406 normalizados), nulos por columna (ID 100%, Estado 1.47%), rango 02/01/2026 – 30/06/2026, valores distintos de Tipo, Estado, Acción y Usuario. Cerrar con la sección 5: duplicados, NBSP, fechas imposibles, horas extremas. |
| 2:30–4:15 | **Módulo 2** · `python/limpieza.py` y `docs/inconsistencias.md` | Ejecutar el script en vivo y leer la bitácora. Explicar las 4 reglas: 83 duplicados (71 exactos + 12 tras estandarizar), catálogo de estados y acciones, fechas imputadas por posición (el archivo está ordenado por fecha) y horas: nulos con la mediana de la acción, tope de 10 h por el cerco Q3 + 3·IQR. Resaltar los flags de trazabilidad. |
| 4:15–6:00 | **Módulo 3** · `notebooks/EDA_Requerimientos.ipynb` | Tabla Antes vs Después. Horas: media 2.40, mediana 1.50, moda 1.00, desviación 2.58, IQR 2.33, asimetría 1.75, curtosis 2.10 → distribución sesgada a la derecha; usar mediana. Multivariante: PRY = 0.5% de tickets y 22% de horas; mapa Grupo × Tipo; Kruskal-Wallis significativo. |
| 6:00–7:45 | **Módulo 4** · `dashboard/Dashboard_Requerimientos.html` y `powerbi/medidas_dax.dax` | Mostrar las 4 medidas DAX y sus valores (3,406 · 16,979 · 4.98 · 98.4%). Recorrer los visuales: tendencia (dos gráficos, sin doble eje), anillo por Tipo, dispersión por Usuario y matriz Acción × Usuario. Demostrar filtros cruzados: clic en PRY y luego en un técnico. Mencionar la guía para armar el `.pbix`. |
| 7:45–9:30 | **Módulo 5** · `informe/Informe_Ejecutivo.pdf` | Hallazgos: capacidad copada (9.4 h/día), menos tickets y más horas por ticket (+78% de enero a junio), 67 tickets > 40 h = 57% de las horas, backlog 2024 = 34.5% de las horas. Cuellos de botella: 3 técnicos con 68% de los tickets, proyectos que dependen de una persona, equipo de Datos. Las 3 recomendaciones con su meta. |
| 9:30–10:00 | `README.md` | Cierre: validaciones realizadas y próximos pasos. |

**Consejos:** grabar en 1080p, aumentar el zoom del editor (125–150%), tener los archivos ya abiertos en pestañas y practicar una vez con cronómetro.
