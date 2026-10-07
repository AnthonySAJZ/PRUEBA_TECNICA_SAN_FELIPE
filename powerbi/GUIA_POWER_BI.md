# Módulo 4 · Guía para armar el dashboard en Power BI

> **Por qué no se adjunta un `.pbix` generado:** Power BI Desktop solo corre en Windows y el `.pbix` es un archivo binario que no se puede construir ni validar fuera de esa herramienta.
> Como el enunciado permite "u otras herramientas de visualización", se entrega:
> 1. `dashboard/Dashboard_Requerimientos.html`: dashboard **interactivo** con las mismas medidas y visualizaciones (abre en cualquier navegador, sin internet).
> 2. Esta guía, el código DAX (`medidas_dax.dax`) y la consulta Power Query (`power_query_requerimientos.m`) para reproducir el `.pbix` en ~15 minutos.

---

## 1. Cargar los datos
1. Power BI Desktop → **Obtener datos → Consulta en blanco → Editor avanzado**.
2. Pegar `power_query_requerimientos.m` y ajustar `RutaCSV` a la ruta local de `data/clean/RequerimientosPruebaDatos_Limpio.csv`.
3. Renombrar la consulta como **`Requerimientos`** → *Cerrar y aplicar*.
   - Alternativa: conectar a SQL Server (`dbo.RequerimientosLimpio`, cargada con `sql/04_carga_datos_limpios.sql`); el bloque comentado al final del `.m` lo hace.

## 2. Modelo
1. **Modelado → Nueva tabla** → pegar la tabla `Calendario` (sección 4 de `medidas_dax.dax`).
2. Marcar `Calendario` como tabla de fechas (columna `Fecha`).
3. Relación `Calendario[Fecha]` (1) → `Requerimientos[FechaRegistro]` (*), dirección simple.
4. En `Calendario`, ordenar `NombreMes` por `AnioMes`.

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

Si los valores coinciden, el modelo está bien armado.

## 4. Página del dashboard (lienzo 16:9)

| Zona | Visual | Configuración |
|---|---|---|
| Fila superior | 5 **segmentaciones** | `Calendario[NombreMes]` (lista o rango), `Tipo`, `SistemaCanal` (Grupo), `Usuario`, `Equipo`. Todas afectan a todos los visuales. |
| KPIs | 4 **tarjetas** | `[Q Tickets]`, `[Q Horas]`, `[Promedio Horas x Ticket]`, `[% Resueltos]` |
| Tendencia | 2 **gráficos de líneas** | Eje X `Calendario[NombreMes]`; Y `[Q Tickets]` en uno y `[Q Horas]` en otro. Se recomienda **no** usar un combinado de doble eje: sus escalas (500–700 vs 2,400–3,400) son arbitrarias entre sí y sugieren correlaciones que no existen. Etiqueta de datos solo en el último punto. |
| Distribución | **Gráfico de anillos** | Leyenda `Tipo`, Valores `[Q Tickets]`. Etiquetas: categoría, valor y % del total. Colores fijos por tipo. |
| Eficiencia | **Gráfico de dispersión** | Valores (detalle) `Usuario`; Eje X `[Q Tickets]`; Eje Y `[Q Horas]`; Información sobre herramientas `[Promedio Horas x Ticket]`. Opcional: líneas de promedio X/Y (panel Análisis) para formar cuadrantes. |
| Matriz de trabajo | **Matriz** con formato condicional | Filas `Accion`, Columnas `Usuario`, Valores `[Q Horas]`. Formato condicional → Color de fondo → escala de un solo color (blanco → azul oscuro). Ordenar columnas por `[Q Horas]` descendente. |

Interacciones: dejar el filtrado cruzado por defecto (clic en un sector del anillo o en un punto de la dispersión filtra el resto), igual que en el dashboard HTML.

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
