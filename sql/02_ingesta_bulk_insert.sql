/* ============================================================================
   PRUEBA TÉCNICA - ANALISTA DE DATOS
   MÓDULO 1.1 - Ingesta automatizada del CSV con BULK INSERT
   Requisito previo: haber ejecutado 01_creacion_tablas.sql

   El procedimiento dbo.usp_CargarRequerimientos deja el proceso parametrizado
   y repetible (se puede programar en un Job del SQL Server Agent):
     1. Vacía el staging.
     2. BULK INSERT del archivo completo a stg.RequerimientosRaw.
     3. Inserta en dbo.Requerimientos convirtiendo FECHA y HORAS a su tipo.
     4. Devuelve un resumen de control (filas leídas / cargadas / sin convertir).

   Nota: la ruta es la del SERVIDOR SQL (no la de la PC cliente). La cuenta del
   servicio de SQL Server necesita permiso de lectura sobre esa carpeta.
   ============================================================================ */

USE PruebaSanFelipe;
GO

CREATE OR ALTER PROCEDURE dbo.usp_CargarRequerimientos
    @RutaArchivo NVARCHAR(400),
    @CodePage    VARCHAR(10) = '1252'   -- archivo ANSI (Windows-1252). En SQL Server sobre Linux usar 'RAW'.
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @sql NVARCHAR(MAX);

    BEGIN TRY
        BEGIN TRANSACTION;

        /* 1) Reinicio de staging (TRUNCATE también reinicia el IDENTITY a 2) */
        TRUNCATE TABLE stg.RequerimientosRaw;

        /* 2) Carga masiva. Se arma dinámicamente porque BULK INSERT no acepta
              variables en FROM ni en CODEPAGE. QUOTENAME evita inyección. */
        SET @sql = N'
            BULK INSERT stg.vw_RequerimientosRaw_Carga
            FROM ' + QUOTENAME(@RutaArchivo, '''') + N'
            WITH (
                FORMAT          = ''CSV'',
                FIRSTROW        = 2,          -- salta la cabecera
                FIELDTERMINATOR = '';'',
                ROWTERMINATOR   = ''0x0d0a'', -- CRLF
                CODEPAGE        = ' + QUOTENAME(@CodePage, '''') + N',
                KEEPNULLS,                    -- los campos vacíos no toman DEFAULT
                TABLOCK
            );';
        EXEC sys.sp_executesql @sql;

        /* 3) Paso a la tabla tipada. Solo se convierten tipos: los textos se
              conservan tal cual para perfilar la calidad del origen. */
        TRUNCATE TABLE dbo.Requerimientos;

        INSERT INTO dbo.Requerimientos
               (FilaOrigen, Id, Codigo, Tipo, SistemaCanal, Usuario, Accion,
                FechaRegistro, Horas, Estado)
        SELECT  r.FilaOrigen,
                r.ID,
                r.REQ,
                r.TIPO,
                r.SISTEMA_CANAL,
                r.USUARIO,
                r.ACCION,
                TRY_CONVERT(DATE,    NULLIF(LTRIM(RTRIM(r.FECHA)), ''), 103),  -- dd/mm/yyyy
                TRY_CONVERT(TIME(0), NULLIF(LTRIM(RTRIM(r.HORAS)), '')),       -- hh:mm:ss
                r.ESTADO
        FROM stg.RequerimientosRaw AS r
        ORDER BY r.FilaOrigen;

        COMMIT TRANSACTION;

        /* 4) Resumen de control de la carga */
        SELECT
            (SELECT COUNT(*) FROM stg.RequerimientosRaw)                               AS FilasLeidasCSV,
            (SELECT COUNT(*) FROM dbo.Requerimientos)                                  AS FilasCargadas,
            (SELECT COUNT(*) FROM stg.RequerimientosRaw
              WHERE NULLIF(LTRIM(RTRIM(FECHA)), '') IS NOT NULL
                AND TRY_CONVERT(DATE, FECHA, 103) IS NULL)                             AS FechasNoConvertibles,
            (SELECT COUNT(*) FROM stg.RequerimientosRaw
              WHERE NULLIF(LTRIM(RTRIM(HORAS)), '') IS NOT NULL
                AND TRY_CONVERT(TIME(0), HORAS) IS NULL)                               AS HorasNoConvertibles;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

/* ---------------------------------------------------------------------------
   Ejecución (ajustar la ruta a la ubicación del archivo en el servidor)
   --------------------------------------------------------------------------- */
-- Windows:
EXEC dbo.usp_CargarRequerimientos
     @RutaArchivo = N'C:\PruebaSanFelipe\data\raw\RequerimientosPruebaDatos.csv';

-- SQL Server en Linux / Docker (CODEPAGE solo admite 'RAW'; con columnas VARCHAR
-- y collation Modern_Spanish_CI_AS los bytes Windows-1252 se leen correctamente):
-- EXEC dbo.usp_CargarRequerimientos
--      @RutaArchivo = N'/data/RequerimientosPruebaDatos.csv',
--      @CodePage    = 'RAW';
GO

/* Verificación rápida */
SELECT TOP (10) * FROM dbo.Requerimientos ORDER BY IdRegistro;
GO
