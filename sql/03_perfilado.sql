/* ============================================================================
   PRUEBA TÉCNICA - ANALISTA DE DATOS
   MÓDULO 1.2 - Consultas de perfilado (T-SQL)
   Requisito previo: 01_creacion_tablas.sql y 02_ingesta_bulk_insert.sql

   Secciones:
     1. Conteo total de registros vs. códigos únicos
     2. Nulos o vacíos por columna (conteo y %)
     3. Rango de fechas operativo (MIN / MAX de FechaRegistro)
     4. Valores distintos de Tipo, Estado, Acción y Usuario
     5. Hallazgos adicionales que justifican la limpieza del Módulo 2
   ============================================================================ */

USE PruebaSanFelipe;
GO
SET NOCOUNT ON;
GO

/* ---------------------------------------------------------------------------
   1. CONTEO TOTAL DE REGISTROS VS. CÓDIGOS ÚNICOS
   --------------------------------------------------------------------------- */
SELECT
    COUNT(*)                                                    AS TotalRegistros,
    COUNT(DISTINCT Codigo COLLATE Latin1_General_BIN)           AS CodigosUnicos,
    COUNT(DISTINCT UPPER(LTRIM(RTRIM(Codigo))) COLLATE Latin1_General_BIN)
                                                                AS CodigosUnicosNormalizados,
    CAST(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT Codigo COLLATE Latin1_General_BIN), 0) AS DECIMAL(6, 2))
                                                                AS RegistrosPromedioPorCodigo,
    COUNT(*) - COUNT(DISTINCT Codigo COLLATE Latin1_General_BIN) AS RegistrosConCodigoRepetido
FROM dbo.Requerimientos;
/* Nota: un código se repite porque cada fila es un registro de horas (varias
   personas y actividades sobre el mismo ticket); no es en sí un duplicado.
   CodigosUnicos compara el texto exacto (collation binaria); la versión
   normalizada ignora mayúsculas/espacios ('Req 2025-...' vs 'REQ 2025-...'). */

-- Top 10 códigos con más registros
SELECT TOP (10)
    Codigo,
    COUNT(*)                     AS Registros,
    COUNT(DISTINCT Usuario)      AS Usuarios,
    CAST(SUM(HorasDecimal) AS DECIMAL(9, 2)) AS HorasTotales
FROM dbo.Requerimientos
GROUP BY Codigo
ORDER BY Registros DESC;
GO

/* ---------------------------------------------------------------------------
   2. NULOS O VACÍOS POR COLUMNA
      Se considera "vacío": NULL, cadena vacía, solo espacios (incluido el
      espacio duro CHAR(160)) o el texto literal 'NULL'.
      Para FECHA/HORAS se muestra además cuántos valores NO vacíos no se
      pudieron convertir (fechas inexistentes como 32/11/2026).
   --------------------------------------------------------------------------- */
WITH Base AS
(
    SELECT
        r.*,
        s.FECHA AS FechaTexto,
        s.HORAS AS HorasTexto
    FROM dbo.Requerimientos AS r
    JOIN stg.RequerimientosRaw AS s ON s.FilaOrigen = r.FilaOrigen
),
Conteo AS
(
    SELECT
        COUNT(*) AS Total,
        SUM(CASE WHEN NULLIF(NULLIF(LTRIM(RTRIM(REPLACE(Id,           NCHAR(160), N' '))), N''), N'NULL') IS NULL THEN 1 ELSE 0 END) AS Id,
        SUM(CASE WHEN NULLIF(NULLIF(LTRIM(RTRIM(REPLACE(Codigo,       NCHAR(160), N' '))), N''), N'NULL') IS NULL THEN 1 ELSE 0 END) AS Codigo,
        SUM(CASE WHEN NULLIF(NULLIF(LTRIM(RTRIM(REPLACE(Tipo,         NCHAR(160), N' '))), N''), N'NULL') IS NULL THEN 1 ELSE 0 END) AS Tipo,
        SUM(CASE WHEN NULLIF(NULLIF(LTRIM(RTRIM(REPLACE(SistemaCanal, NCHAR(160), N' '))), N''), N'NULL') IS NULL THEN 1 ELSE 0 END) AS SistemaCanal,
        SUM(CASE WHEN NULLIF(NULLIF(LTRIM(RTRIM(REPLACE(Usuario,      NCHAR(160), N' '))), N''), N'NULL') IS NULL THEN 1 ELSE 0 END) AS Usuario,
        SUM(CASE WHEN NULLIF(NULLIF(LTRIM(RTRIM(REPLACE(Accion,       NCHAR(160), N' '))), N''), N'NULL') IS NULL THEN 1 ELSE 0 END) AS Accion,
        SUM(CASE WHEN NULLIF(LTRIM(RTRIM(FechaTexto)), '') IS NULL THEN 1 ELSE 0 END)                                               AS FechaVacia,
        SUM(CASE WHEN NULLIF(LTRIM(RTRIM(FechaTexto)), '') IS NOT NULL AND FechaRegistro IS NULL THEN 1 ELSE 0 END)                 AS FechaInvalida,
        SUM(CASE WHEN NULLIF(LTRIM(RTRIM(HorasTexto)), '') IS NULL THEN 1 ELSE 0 END)                                               AS HorasVacia,
        SUM(CASE WHEN NULLIF(LTRIM(RTRIM(HorasTexto)), '') IS NOT NULL AND Horas IS NULL THEN 1 ELSE 0 END)                         AS HorasInvalida,
        SUM(CASE WHEN NULLIF(NULLIF(LTRIM(RTRIM(REPLACE(Estado,       NCHAR(160), N' '))), N''), N'NULL') IS NULL THEN 1 ELSE 0 END) AS Estado
    FROM Base
)
SELECT
    v.Orden,
    v.Columna,
    v.NulosOVacios,
    CAST(100.0 * v.NulosOVacios / c.Total AS DECIMAL(5, 2))                     AS PorcentajeNulosOVacios,
    v.NoConvertibles,
    CAST(100.0 * (v.NulosOVacios + v.NoConvertibles) / c.Total AS DECIMAL(5, 2)) AS PorcentajeSinDatoUtil
FROM Conteo AS c
CROSS APPLY (VALUES
    (1, 'ID',             c.Id,           0),
    (2, 'REQ (Codigo)',   c.Codigo,       0),
    (3, 'TIPO',           c.Tipo,         0),
    (4, 'SISTEMA/ CANAL', c.SistemaCanal, 0),
    (5, 'USUARIO',        c.Usuario,      0),
    (6, 'ACCIÓN',         c.Accion,       0),
    (7, 'FECHA',          c.FechaVacia,   c.FechaInvalida),
    (8, 'HORAS',          c.HorasVacia,   c.HorasInvalida),
    (9, 'ESTADO',         c.Estado,       0)
) AS v (Orden, Columna, NulosOVacios, NoConvertibles)
ORDER BY v.Orden;
GO

/* ---------------------------------------------------------------------------
   3. RANGO DE FECHAS OPERATIVO
   --------------------------------------------------------------------------- */
SELECT
    MIN(FechaRegistro)                                     AS FechaMinima,
    MAX(FechaRegistro)                                     AS FechaMaxima,
    DATEDIFF(DAY, MIN(FechaRegistro), MAX(FechaRegistro)) + 1 AS DiasCalendario,
    COUNT(DISTINCT FechaRegistro)                          AS DiasConRegistro,
    SUM(CASE WHEN FechaRegistro IS NULL THEN 1 ELSE 0 END) AS RegistrosSinFechaValida
FROM dbo.Requerimientos;

-- Distribución mensual (volumen y horas)
SELECT
    FORMAT(FechaRegistro, 'yyyy-MM')   AS AnioMes,
    COUNT(*)                           AS Registros,
    COUNT(DISTINCT Codigo)             AS Tickets,
    CAST(SUM(HorasDecimal) AS DECIMAL(9, 2)) AS Horas
FROM dbo.Requerimientos
WHERE FechaRegistro IS NOT NULL
GROUP BY FORMAT(FechaRegistro, 'yyyy-MM')
ORDER BY AnioMes;
GO

/* ---------------------------------------------------------------------------
   4. VALORES DISTINTOS DE LAS VARIABLES CATEGÓRICAS
      El valor se muestra entre corchetes para evidenciar espacios ocultos.
   --------------------------------------------------------------------------- */
-- 4.1 Resumen: cuántos valores distintos tiene cada variable
SELECT 'Tipo'    AS Variable, COUNT(DISTINCT Tipo)    AS ValoresDistintos FROM dbo.Requerimientos UNION ALL
SELECT 'Estado',              COUNT(DISTINCT Estado)                      FROM dbo.Requerimientos UNION ALL
SELECT 'Accion',              COUNT(DISTINCT Accion)                      FROM dbo.Requerimientos UNION ALL
SELECT 'Usuario',             COUNT(DISTINCT Usuario)                     FROM dbo.Requerimientos;

-- 4.2 Detalle de valores con frecuencia y porcentaje
WITH Valores AS
(
    SELECT 'Tipo'    AS Variable, Tipo    AS Valor FROM dbo.Requerimientos UNION ALL
    SELECT 'Estado',              Estado           FROM dbo.Requerimientos UNION ALL
    SELECT 'Accion',              Accion           FROM dbo.Requerimientos UNION ALL
    SELECT 'Usuario',             Usuario          FROM dbo.Requerimientos
)
SELECT
    Variable,
    N'[' + ISNULL(Valor, N'<NULL>') + N']'                                         AS Valor,
    COUNT(*)                                                                        AS Registros,
    CAST(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY Variable) AS DECIMAL(5, 2)) AS Porcentaje
FROM Valores
GROUP BY Variable, Valor
ORDER BY Variable, Registros DESC;
GO

/* ---------------------------------------------------------------------------
   5. HALLAZGOS ADICIONALES (insumo para el Módulo 2)
   --------------------------------------------------------------------------- */
-- 5.1 Filas duplicadas exactas (las 9 columnas del archivo idénticas, comparación binaria)
SELECT
    COUNT(*)                AS GruposDuplicados,
    SUM(Repeticiones - 1)   AS FilasDuplicadasSobrantes
FROM
(
    SELECT COUNT(*) AS Repeticiones
    FROM stg.RequerimientosRaw
    GROUP BY ID            COLLATE Latin1_General_BIN,
             REQ           COLLATE Latin1_General_BIN,
             TIPO          COLLATE Latin1_General_BIN,
             SISTEMA_CANAL COLLATE Latin1_General_BIN,
             USUARIO       COLLATE Latin1_General_BIN,
             ACCION        COLLATE Latin1_General_BIN,
             FECHA         COLLATE Latin1_General_BIN,
             HORAS         COLLATE Latin1_General_BIN,
             ESTADO        COLLATE Latin1_General_BIN
    HAVING COUNT(*) > 1
) AS d;

-- 5.2 Variantes de escritura de una misma categoría
SELECT 'Estado con distinto género'   AS Hallazgo, Estado AS Valor, COUNT(*) AS Registros
FROM dbo.Requerimientos WHERE Estado IN (N'Cerrada', N'Cerrado', N'Resuelta', N'Resuelto')
GROUP BY Estado
UNION ALL
SELECT 'Estado con texto literal NULL', Estado, COUNT(*)
FROM dbo.Requerimientos WHERE Estado = N'NULL' GROUP BY Estado
UNION ALL
SELECT 'Acción sinónima de 02_Analisis', Accion, COUNT(*)
FROM dbo.Requerimientos WHERE Accion IN (N'02_Analisis', N'02_Analizado') GROUP BY Accion
UNION ALL
SELECT 'Sistema con espacio duro (CHAR 160)', REPLACE(SistemaCanal, NCHAR(160), N'·'), COUNT(*)
FROM dbo.Requerimientos WHERE SistemaCanal LIKE N'%' + NCHAR(160) + N'%' GROUP BY SistemaCanal
UNION ALL
SELECT 'Sistema con error tipográfico', SistemaCanal, COUNT(*)
FROM dbo.Requerimientos WHERE SistemaCanal = N'AGENDA PROCEDMIENTOS' GROUP BY SistemaCanal
UNION ALL
SELECT 'Código con prefijo en minúsculas', Codigo, COUNT(*)
FROM dbo.Requerimientos WHERE Codigo COLLATE Latin1_General_CS_AS <> UPPER(Codigo) GROUP BY Codigo;

-- 5.3 Fechas que no existen en el calendario
SELECT s.FECHA AS FechaTexto, COUNT(*) AS Registros
FROM stg.RequerimientosRaw AS s
WHERE NULLIF(LTRIM(RTRIM(s.FECHA)), '') IS NOT NULL
  AND TRY_CONVERT(DATE, s.FECHA, 103) IS NULL
GROUP BY s.FECHA
ORDER BY Registros DESC;

-- 5.4 Horas: estadísticos y valores extremos (regla de Tukey sobre el IQR).
--     Se calcula en minutos enteros para no arrastrar redondeos (40 min = 0.6667 h).
WITH Cuartiles AS
(
    SELECT DISTINCT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY Minutos) OVER () AS Q1,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY Minutos) OVER () AS Mediana,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY Minutos) OVER () AS Q3
    FROM dbo.Requerimientos
    WHERE Minutos IS NOT NULL
),
Cercos AS
(
    SELECT Q1, Mediana, Q3,
           Q3 - Q1                   AS IQR,
           Q3 + 1.5 * (Q3 - Q1)      AS CercoModerado,
           Q3 + 3.0 * (Q3 - Q1)      AS CercoExtremo
    FROM Cuartiles
)
SELECT
    CAST(c.Q1            / 60 AS DECIMAL(6, 2))                          AS Q1_Horas,
    CAST(c.Mediana       / 60 AS DECIMAL(6, 2))                          AS Mediana_Horas,
    CAST(c.Q3            / 60 AS DECIMAL(6, 2))                          AS Q3_Horas,
    CAST(c.IQR           / 60 AS DECIMAL(6, 2))                          AS IQR_Horas,
    CAST(c.CercoModerado / 60 AS DECIMAL(6, 2))                          AS CercoModerado_Horas,
    CAST(c.CercoExtremo  / 60 AS DECIMAL(6, 2))                          AS CercoExtremo_Horas,
    (SELECT MIN(HorasDecimal) FROM dbo.Requerimientos)                   AS Minimo_Horas,
    (SELECT MAX(HorasDecimal) FROM dbo.Requerimientos)                   AS Maximo_Horas,
    (SELECT COUNT(*) FROM dbo.Requerimientos WHERE Minutos > c.CercoModerado) AS AtipicosModerados,
    (SELECT COUNT(*) FROM dbo.Requerimientos WHERE Minutos > c.CercoExtremo)  AS AtipicosExtremos
FROM Cercos AS c;

-- 5.5 Carga diaria por usuario superior a 12 horas (posible doble registro)
SELECT TOP (15)
    Usuario,
    FechaRegistro,
    COUNT(*)          AS Registros,
    CAST(SUM(Minutos) / 60.0 AS DECIMAL(6, 2)) AS HorasDia
FROM dbo.Requerimientos
WHERE NULLIF(LTRIM(RTRIM(Usuario)), N'') IS NOT NULL
  AND FechaRegistro IS NOT NULL
GROUP BY Usuario, FechaRegistro
HAVING SUM(Minutos) > 12 * 60
ORDER BY HorasDia DESC;

-- 5.6 Coherencia Tipo vs. prefijo del código (solo se informa: no hay regla para corregir)
SELECT LEFT(UPPER(Codigo), 3) AS PrefijoCodigo, Tipo, COUNT(*) AS Registros
FROM dbo.Requerimientos
GROUP BY LEFT(UPPER(Codigo), 3), Tipo
ORDER BY PrefijoCodigo, Tipo;
GO
