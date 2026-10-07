# Módulo 2 · Inconsistencias detectadas y tratamiento aplicado

Script: [`python/limpieza.py`](../python/limpieza.py) · Bitácora generada: [`data/clean/log_limpieza.csv`](../data/clean/log_limpieza.csv)
Archivo estandarizado: [`data/clean/RequerimientosPruebaDatos_Limpio.csv`](../data/clean/RequerimientosPruebaDatos_Limpio.csv) (también en `.xlsx` con diccionario y bitácora).

**Resultado:** 7,158 → **7,075 filas**, 0 nulos en las columnas de análisis, categorías únicas y una columna `Flag*` por cada corrección (trazabilidad completa; los valores originales se conservan en `HorasOriginal`, `FechaOriginal` y `FilaOrigen`, que por eso mantienen sus vacíos de origen).

## Hallazgos del perfilado que originan la limpieza

| # | Inconsistencia | Columna | Ejemplo | Filas | Regla | Tratamiento |
|---|---|---|---|---:|---|---|
| 1 | Columna sin datos | `ID` | 100% vacía | 7,158 | Estructura | Se elimina y se crea `IdRegistro` secuencial |
| 2 | Registros duplicados exactos | todas | misma fila repetida | 71 | 1. Duplicados | Se conserva la primera aparición |
| 3 | Duplicados "disfrazados" (iguales tras estandarizar) | todas | `Cerrada` vs `Cerrado` en filas idénticas | 12 | 1. Duplicados | Se conserva la primera aparición |
| 4 | Mismo estado con distinto género o redacción | `ESTADO` | `Cerrada`/`Cerrado`, `Resuelta`/`Resuelto`, `Asignada a un grupo` | 6,216 | 2. Categorías | Catálogo: `Cerrado`, `Resuelto`, `Asignado` |
| 5 | Texto literal `NULL` en lugar de nulo | `ESTADO` | `NULL` | 105 | 0. Texto | Nulo real → se imputa desde el ticket (55) o `Sin Estado` (49)* |
| 6 | Sinónimo de una acción | `ACCIÓN` | `02_Analizado` = `02_Analisis` | 12 | 2. Categorías | Se unifica en `02_Análisis` |
| 7 | Ortografía inconsistente del catálogo | `ACCIÓN` | `03_Estimación…` vs `26_Estimacion…_Datos`; `Reunion`, `Analisis` | 4,217 | 2. Categorías | Se uniforman las tildes |
| 8 | Espacio duro (NBSP, `CHAR(160)`) | `SISTEMA/ CANAL` | `PORTAL PROVEEDORES` con NBSP (se veía como un 2.º valor) | 29 | 0. Texto | Se reemplaza por espacio normal |
| 9 | Error tipográfico | `SISTEMA/ CANAL` | `AGENDA PROCEDMIENTOS` | 15 | 2. Categorías | `AGENDA PROCEDIMIENTOS` |
| 10 | Prefijo en minúsculas | `REQ` (Código) | `Req 2024-006886` | 1 | 2. Categorías | Mayúsculas (3,407 → 3,406 códigos únicos) |
| 11 | Fecha que no existe en el calendario | `FECHA` | `32/11/2026`, `24/16/2026`, `03/21/2026`, `18/13/2026`, `33/03/2026`, `35/01/2026` | 22 | 3. Fechas | Imputación por posición (ver nota) |
| 12 | Fecha vacía | `FECHA` | — | 33 (32 tras quitar duplicados) | 3. Fechas | Imputación por posición (ver nota) |
| 13 | Fecha como texto `dd/mm/yyyy` | `FECHA` | `02/01/2026` | todas | 3. Fechas | `FechaRegistro` ISO `yyyy-mm-dd` + `Anio`, `Mes`, `AnioMes` |
| 14 | Horas como texto no sumable | `HORAS` | `01:30:00` | todas | 4. Horas | Horas decimales (`1.5`) |
| 15 | Horas vacías | `HORAS` | — | 45 | 4. Horas | Mediana de la misma acción · `FlagHorasImputadas` |
| 16 | Horas extremas en un registro | `HORAS` | 10:20 a 16:00 h | 55 | 4. Horas | Acotadas a 10 h (cerco extremo de Tukey Q3 + 3·IQR) · original en `HorasOriginal` · `FlagHorasAjustadas` |
| 17 | Técnico con > 12 h en un día | `HORAS` | YSUYCO 19 h el 02/02/2026 | Origen: 195 filas / 39 días-técnico. Tras quitar duplicados y acotar registros a 10 h: 176 / 28 | 4. Horas | Solo se marca `FlagDiaSobrecargado`, calculado sobre las horas ya acotadas (no se sabe qué registro sobra) |
| 18 | Sistema vacío | `SISTEMA/ CANAL` | — | 36 | Imputación | 15 desde otro registro del mismo ticket · 21 `NO ESPECIFICADO` |
| 19 | Usuario vacío | `USUARIO` | todos del 16 y 17/04/2026 | 39 | Imputación | `NO IDENTIFICADO` (un ticket tiene varios técnicos: no se adivina) |
| 20 | Acción vacía | `ACCIÓN` | — | 24 | Imputación | `00_No Especificado` |
| 21 | Ticket con varios estados en el periodo | `ESTADO` | `Asignado` y luego `Cerrado` | 15 tickets | Derivada | `EstadoTicket` = estado del último registro (base de `% Resueltos`) |
| 22 | Número de actividad compartido por dos acciones | `ACCIÓN` | `24_Validaciones QA` y `24_Análisis_Datos` | 72 (8 + 64) | Derivada | Se informa, no se corrige: `AccionCodigo` no identifica la actividad; usar `Accion` como clave |

\* Una de las 105 filas con `NULL` era duplicada, por eso 55 + 49 = 104.

## Decisiones y supuestos

- **Orden de ejecución:** primero se limpia el texto y se estandarizan categorías, luego se quitan duplicados. Así se detectan los 12 duplicados que solo aparecen después de uniformar (`Cerrada` = `Cerrado`).
- **Imputación de fechas por posición:** el CSV está ordenado cronológicamente en dos bloques (líneas 2–6,321 y 6,322–7,159; el segundo solo tiene registros de ACARRASCO, AINGA y RRUIZ, y dentro de él hay tres tramos ordenados). Ninguna fecha a imputar cae al inicio de un bloque o tramo. Un registro sin fecha válida recibe la fecha del registro válido anterior. En 33 de los 54 casos los registros vecinos tienen el mismo día (confianza alta); en el resto el error máximo es de un día. No se usa la inversión día/mes para `03/21/2026` porque los registros vecinos son del 03/03 y del 04/05, no del 21/03.
- **Tope de horas en 10 h:** coincide con el cerco extremo estadístico (Q3 = 3 h, IQR = 2.33 h → 3 + 3 × 2.33 = 10 h) y con la jornada observada (mediana de 9.5 h por técnico y día). Los registros de 6.5 a 10 h (atípicos moderados) **no** se tocan: son jornadas completas dedicadas a proyectos.
- **Lo que no se corrige:** el `Tipo` no siempre coincide con el prefijo del código (p. ej. 490 registros con código `INC` tienen Tipo `EXP` y 37 con código `REQ` tienen Tipo `INC`). No hay una regla de negocio que diga cuál es el correcto, así que se informa en el perfilado (`sql/03_perfilado.sql`, sección 5.6) y se respeta el `Tipo`.
- **Grupo:** el archivo no tiene una columna llamada *Grupo*; se usa `SISTEMA/ CANAL` como grupo funcional y se agrega `Equipo` (Datos / Aplicaciones), derivado de las acciones `*_Datos`. `Equipo` clasifica la **actividad**, no a la persona: un mismo técnico puede tener registros de ambos equipos.
- **Estado:** es una foto al momento de la extracción (el 99% de los registros figura `Cerrado`, incluso en tickets que siguieron recibiendo horas hasta junio), por lo que `% Resueltos` puede sobreestimar los cierres reales.
