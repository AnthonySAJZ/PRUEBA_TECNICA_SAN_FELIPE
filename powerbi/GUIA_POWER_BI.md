# Módulo 4 · Dashboard en Power BI

Se entregan dos vías equivalentes:

1. **Proyecto Power BI en formato PBIP** (`powerbi/pbip/`), listo para abrir en Power BI Desktop: modelo semántico en TMDL y reporte en formato PBIR. Ver la sección 0.
2. **Dashboard HTML interactivo** (`dashboard/Dashboard_Requerimientos.html`) con las mismas medidas y visualizaciones. Abre en cualquier navegador, sin internet.

Las secciones 1 a 4 describen cómo armar el mismo `.pbix` a mano, como alternativa o para entender el modelo.

---

## 0. Abrir el proyecto PBIP (recomendado)

```
powerbi/pbip/
├── Dashboard_Requerimientos.pbip              ← abrir este archivo
├── Dashboard_Requerimientos.SemanticModel/    modelo (TMDL): tablas, relación, 18 medidas
└── Dashboard_Requerimientos.Report/           reporte (PBIR): página "Dashboard", 15 visuales
```

**Requisitos:** Power BI Desktop para Windows de **agosto de 2025 o posterior**. En versiones donde estos formatos aún eran vista previa, activar en *Archivo > Opciones y configuración > Opciones > Características en versión preliminar*: "Power BI Project (.pbip) save option", "Store semantic model using TMDL format" y "Store reports using enhanced metadata format (PBIR)" (nombres en inglés; en español aparecen traducidos). Reiniciar Desktop. Si esas opciones ya no aparecen, es que están disponibles de forma general.

**Pasos:**
1. Clonar o descargar el repositorio. Se recomienda una ruta corta (por ejemplo `C:\PruebaSanFelipe`), porque Windows tiene un límite de longitud de ruta.
2. Doble clic en `powerbi\pbip\Dashboard_Requerimientos.pbip`. El reporte **abre sin datos**: el proyecto no versiona la caché (`cache.abf`).
3. *Inicio > Transformar datos* (flecha) *> Editar parámetros* > **`RutaArchivoCSV`** = ruta absoluta de `data\clean\RequerimientosPruebaDatos_Limpio.csv` en tu equipo > *Aceptar* > *Aplicar cambios*. Si clonaste en `C:\PruebaSanFelipe`, la ruta por defecto ya es correcta.
4. *Inicio > Actualizar*.
5. Comprobar los valores de control de las secciones 3 y 5 (3,406 tickets · 16,979 horas · 4.98 · 98.4%).
6. Para entregar un `.pbix`: *Archivo > Guardar como* > tipo *Archivo de Power BI (.pbix)*.

**Qué esperar:**
- Al guardar, Desktop puede reescribir archivos del proyecto (subir la versión de `$schema`, agregar `cultures/`, `.pbi/localSettings.json`, etc.). Es normal; el `.gitignore` del proyecto ya excluye la caché y la configuración local.
- Desktop no detecta cambios hechos a los archivos mientras el proyecto está abierto: cerrar y volver a abrir.
- El proyecto se regenera con `python python/generar_pbip.py`, opcionalmente con `--ruta-csv "<ruta>"` para dejar fijado el parámetro. Se reemplazan solo los archivos que crea el script.

**Cómo se validó (sin Power BI Desktop disponible):**
- Todos los JSON del reporte y del proyecto pasan los **esquemas oficiales de Microsoft** (`microsoft/json-schemas`).
- El modelo TMDL lo lee la **librería oficial de Microsoft (TOM, `Microsoft.AnalysisServices` 19.84)**, y al volver a serializarlo sale idéntico byte a byte.
- Cada visual se comparó con reportes PBIR reales escritos por Power BI Desktop 2026. Las referencias a tablas, columnas y medidas se comprobaron contra el modelo.
- Los valores de control de las secciones 3 y 5 se recalcularon con pandas sobre el CSV limpio.

**Si algo falla:**

| Síntoma | Causa probable | Solución |
|---|---|---|
| "No se encontró el archivo" al actualizar | `RutaArchivoCSV` apunta a otra ruta | Paso 3 |
| Visuales vacíos | Falta actualizar | Paso 4 |
| Desktop dice que el formato requiere una versión más nueva o una característica en vista previa | Desktop anterior a agosto 2025 o vista previa desactivada | Actualizar Desktop o activar las opciones de vista previa |
| Las tarjetas aparecen como "tarjeta (heredada)" | Se usa la tarjeta clásica (`card`), aún soportada | Opcional: cambiar a la tarjeta nueva desde el panel de visualizaciones |

---

## 1. Cargar los datos (armado manual)
1. Power BI Desktop → **Obtener datos → Consulta en blanco → Editor avanzado**.
2. Pegar `power_query_requerimientos.m` y ajustar `RutaArchivoCSV` a la ruta local de `data/clean/RequerimientosPruebaDatos_Limpio.csv`.
3. Renombrar la consulta como **`Requerimientos`** → *Cerrar y aplicar*.
   - Alternativa: conectar a SQL Server (`dbo.RequerimientosLimpio`, cargada con `sql/04_carga_datos_limpios.sql`); el bloque comentado al final del `.m` lo hace.

## 2. Modelo
1. **Modelado → Nueva tabla** → pegar la tabla `Calendario` (sección 4 de `medidas_dax.dax`). Cubre del primer al último mes con datos y escribe los meses en español ("Ene 2026"), sin depender de la configuración regional.
2. Marcar `Calendario` como tabla de fechas (columna `Fecha`).
3. Relación `Calendario[Fecha]` (1) → `Requerimientos[FechaRegistro]` (*), dirección simple.
4. En `Calendario`, ordenar `NombreMes` por `AnioMes`.
5. Recomendado: ocultar en `Requerimientos` las columnas `FechaRegistro`, `Anio`, `Mes` y `AnioMes`, para que los visuales usen siempre `Calendario` (las medidas de mes anterior lo necesitan).

```
Calendario (1) ────────< Requerimientos (*)
  Fecha                    FechaRegistro
```

## 3. Medidas
Crear una tabla vacía `_Medidas` (Especificar datos → Cargar) y pegar cada medida de `medidas_dax.dax`.

| Medida | Formato | Valor esperado (sin filtros) |
|---|---|---|
| `[Q Tickets]` | Entero, separador de miles | **3,406** |
| `[Q Registros]` | Entero | 7,075 |
| `[Q Horas]` | Decimal, 0 decimales | **16,979** (16,978.75) |
| `[Promedio Horas x Ticket]` | Decimal, 2 decimales | **4.98** |
| `[% Resueltos]` | Porcentaje, 1 decimal | **98.4%** (3,351 / 3,406) |
| `[% Horas Backlog]` | Porcentaje | 34.5% |
| `[Horas x Usuario Dia]` | Decimal, 2 decimales | 9.41 |
| `[Q Dias Sobrecargados]` | Entero | 28 |

Si los valores coinciden, el modelo está bien armado. Las medidas de mes anterior devuelven vacío sin un único mes en contexto (a propósito).

## 4. Página del dashboard

Así está construida la página del PBIP: vertical de 1280 × 1500 px, en modo *Ajustar al ancho*. Para armarla a mano, replicar esta tabla.

| Zona | Visual | Configuración |
|---|---|---|
| Fila superior | 5 **segmentaciones** (lista desplegable) | `Calendario[NombreMes]` (encabezado "Mes"), `Tipo`, `SistemaCanal` (encabezado "Grupo (Sistema/Canal)"), `Usuario`, `Equipo`. Todas afectan a todos los visuales. |
| KPIs | 4 **tarjetas** | `[Q Tickets]`, `[Q Horas]`, `[Promedio Horas x Ticket]`, `[% Resueltos]`; unidades de visualización "Ninguna". |
| Tendencia | 2 **gráficos de líneas** | Eje X `Calendario[NombreMes]` (orden ascendente = cronológico); Y `[Q Tickets]` en uno y `[Q Horas]` en otro. Etiquetas de datos en los 6 puntos con unidades "Ninguna". **No** usar un combinado de doble eje: sus escalas (500–700 vs 2,400–3,400) son arbitrarias entre sí y sugieren correlaciones que no existen. |
| Distribución | **Gráfico de anillos** | Leyenda `Tipo`, Valores `[Q Tickets]`. Etiquetas: categoría, valor y % del total (unidades "Ninguna"). Colores fijos: INC azul, REQ naranja, EXP verde agua, PRY amarillo. |
| Eficiencia | **Gráfico de dispersión** | Valores (detalle) `Usuario`; Eje X `[Q Tickets]`; Eje Y `[Q Horas]`; Información sobre herramientas `[Promedio Horas x Ticket]`; etiquetas de categoría activadas. |
| Matriz de trabajo | **Matriz** con formato condicional | Filas `Accion`, Columnas `Usuario`, Valores `[Q Horas]`. Formato condicional → Color de fondo → degradado de blanco a azul. Filas ordenadas por `[Q Horas]` descendente; las columnas quedan en orden alfabético. |

**Interacciones:** un clic en el anillo, un punto de la dispersión o una celda **filtra** el resto de visuales, igual que el dashboard HTML. El PBIP ya lo trae configurado. Para armado manual: *Archivo > Opciones y configuración > Opciones > Archivo actual > Configuración del informe* > "Cambiar la interacción visual predeterminada de resaltado cruzado a filtrado cruzado".

## 5. Valores de control por mes

| Mes | Q Tickets | Q Horas | Promedio Horas x Ticket |
|---|---:|---:|---:|
| Ene 2026 | 645 | 2,378.42 | 3.69 |
| Feb 2026 | 679 | 2,448.00 | 3.61 |
| Mar 2026 | 706 | 3,106.92 | 4.40 |
| Abr 2026 | 603 | 2,774.83 | 4.60 |
| May 2026 | 522 | 2,840.42 | 5.44 |
| Jun 2026 | 524 | 3,430.17 | 6.55 |

Q Tickets por Tipo: INC 1,414 · REQ 1,223 · EXP 752 · PRY 17.

> La suma de los tickets mensuales (3,679) es mayor que 3,406 porque un mismo ticket puede tener horas en varios meses. Es el comportamiento correcto de `DISTINCTCOUNT`.
