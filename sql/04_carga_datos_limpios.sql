/* ============================================================================
   PRUEBA TÉCNICA - ANALISTA DE DATOS
   Carga del archivo LIMPIO (salida del Módulo 2) y comparación Antes vs Después
   Requisito previo: 01, 02 y haber ejecutado python/limpieza.py

   El CSV limpio está en UTF-8, separado por comas, con cabecera.
   dbo.RequerimientosLimpio puede usarse como origen del dashboard de Power BI.

   SQL Server sobre Linux/Docker no admite CODEPAGE = '65001'. Ahí se guarda el
   CSV en UTF-16 y se reemplaza CODEPAGE por DATAFILETYPE = 'widechar' con
   ROWTERMINATOR = '\n' (validado en SQL Server 2022 para Linux).
   ============================================================================ */

USE PruebaSanFelipe;
GO

TRUNCATE TABLE dbo.RequerimientosLimpio;

-- Windows (ajustar ruta en el servidor):
BULK INSERT dbo.RequerimientosLimpio
FROM 'C:\PruebaSanFelipe\data\clean\RequerimientosPruebaDatos_Limpio.csv'
WITH (
    FORMAT          = 'CSV',
    FIRSTROW        = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR   = '0x0a',
    CODEPAGE        = '65001',   -- UTF-8
    TABLOCK
);
GO

/* ---------------------------------------------------------------------------
   Control de calidad: Antes (dbo.Requerimientos) vs Después (limpio)
   --------------------------------------------------------------------------- */
WITH Antes AS
(
    SELECT
        COUNT(*)                                                       AS Filas,
        COUNT(DISTINCT Codigo COLLATE Latin1_General_BIN)              AS Tickets,
        SUM(CASE WHEN FechaRegistro IS NULL THEN 1 ELSE 0 END)         AS SinFechaValida,
        SUM(CASE WHEN Horas IS NULL THEN 1 ELSE 0 END)                 AS SinHoras,
        SUM(CASE WHEN NULLIF(LTRIM(RTRIM(Usuario)), N'') IS NULL THEN 1 ELSE 0 END)          AS SinUsuario,
        SUM(CASE WHEN NULLIF(NULLIF(Estado, N''), N'NULL') IS NULL THEN 1 ELSE 0 END)        AS SinEstado,
        COUNT(DISTINCT Estado)                                         AS ValoresEstado,
        COUNT(DISTINCT Accion)                                         AS ValoresAccion,
        CAST(SUM(HorasDecimal) AS DECIMAL(10, 2))                      AS HorasTotales,
        CAST(MAX(HorasDecimal) AS DECIMAL(10, 2))                      AS HorasMaxRegistro
    FROM dbo.Requerimientos
),
Despues (Filas, Tickets, SinFechaValida, SinHoras, SinUsuario, SinEstado,
         ValoresEstado, ValoresAccion, HorasTotales, HorasMaxRegistro) AS
(
    SELECT
        COUNT(*),
        COUNT(DISTINCT Codigo),
        SUM(CAST(FlagFechaImputada AS INT)),          -- ya no hay nulos: se muestran los imputados
        SUM(CAST(FlagHorasImputadas AS INT)),
        SUM(CASE WHEN Usuario = N'NO IDENTIFICADO' THEN 1 ELSE 0 END),
        SUM(CASE WHEN Estado  = N'Sin Estado'      THEN 1 ELSE 0 END),
        COUNT(DISTINCT Estado),
        COUNT(DISTINCT Accion),
        CAST(SUM(Horas) AS DECIMAL(10, 2)),
        CAST(MAX(Horas) AS DECIMAL(10, 2))
    FROM dbo.RequerimientosLimpio
)
SELECT m.Metrica, m.Antes, m.Despues, m.Despues - m.Antes AS Diferencia
FROM Antes AS a
CROSS JOIN Despues AS d
CROSS APPLY (VALUES
    ('Filas',                                   CAST(a.Filas AS DECIMAL(10, 2)),          CAST(d.Filas AS DECIMAL(10, 2))),
    ('Tickets únicos',                          a.Tickets,          d.Tickets),
    ('Fecha nula/ inválida -> imputada',        a.SinFechaValida,   d.SinFechaValida),
    ('Horas nulas -> imputadas',                a.SinHoras,         d.SinHoras),
    ('Usuario vacío -> NO IDENTIFICADO',        a.SinUsuario,       d.SinUsuario),
    ('Estado nulo -> Sin Estado (tras imputar)', a.SinEstado,        d.SinEstado),
    ('Valores distintos de Estado',             a.ValoresEstado,    d.ValoresEstado),
    ('Valores distintos de Acción',             a.ValoresAccion,    d.ValoresAccion),
    ('Horas totales',                           a.HorasTotales,     d.HorasTotales),
    ('Horas máximas en un registro',            a.HorasMaxRegistro, d.HorasMaxRegistro)
) AS m (Metrica, Antes, Despues);
GO
