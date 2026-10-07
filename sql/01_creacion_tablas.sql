/* ============================================================================
   PRUEBA TÉCNICA - ANALISTA DE DATOS
   MÓDULO 1.1 - Creación de base de datos y tablas (DDL)
   Motor     : SQL Server 2017+ (probado en SQL Server 2022)
   Archivo   : RequerimientosPruebaDatos.csv  (separador ';', ANSI/Windows-1252, CRLF)

   Diseño en dos capas:
     stg.RequerimientosRaw  -> copia fiel del CSV (todo texto). Nada se pierde
                               ni se transforma; sirve para auditar la carga.
     dbo.Requerimientos     -> misma información con tipos de dato correctos
                               (fecha DATE, horas TIME). Los textos se guardan
                               tal cual llegan para que el perfilado muestre
                               la calidad real del origen.
   ============================================================================ */

IF DB_ID(N'PruebaSanFelipe') IS NULL
    CREATE DATABASE PruebaSanFelipe COLLATE Modern_Spanish_CI_AS;
GO

USE PruebaSanFelipe;
GO

IF SCHEMA_ID(N'stg') IS NULL
    EXEC (N'CREATE SCHEMA stg AUTHORIZATION dbo;');
GO

/* ---------------------------------------------------------------------------
   1) Tabla de staging: 1 columna por campo del CSV, todo VARCHAR.
      FilaOrigen guarda el número de línea del archivo (la línea 1 es la
      cabecera, por eso el IDENTITY empieza en 2) para trazabilidad.
   --------------------------------------------------------------------------- */
DROP VIEW  IF EXISTS stg.vw_RequerimientosRaw_Carga;
DROP TABLE IF EXISTS stg.RequerimientosRaw;
GO

CREATE TABLE stg.RequerimientosRaw
(
    FilaOrigen     INT IDENTITY(2, 1) NOT NULL,
    ID             VARCHAR(50)  NULL,
    REQ            VARCHAR(50)  NULL,
    TIPO           VARCHAR(50)  NULL,
    SISTEMA_CANAL  VARCHAR(100) NULL,
    USUARIO        VARCHAR(100) NULL,
    ACCION         VARCHAR(100) NULL,
    FECHA          VARCHAR(50)  NULL,
    HORAS          VARCHAR(50)  NULL,
    ESTADO         VARCHAR(50)  NULL,
    FechaCarga     DATETIME2(0) NOT NULL
        CONSTRAINT DF_RequerimientosRaw_FechaCarga DEFAULT (SYSDATETIME()),
    CONSTRAINT PK_RequerimientosRaw PRIMARY KEY CLUSTERED (FilaOrigen)
);
GO

/* Vista "puente" para BULK INSERT: expone solo las 9 columnas del CSV, de modo
   que FilaOrigen (IDENTITY) y FechaCarga (DEFAULT) se generen solas. */
CREATE VIEW stg.vw_RequerimientosRaw_Carga
AS
SELECT ID, REQ, TIPO, SISTEMA_CANAL, USUARIO, ACCION, FECHA, HORAS, ESTADO
FROM stg.RequerimientosRaw;
GO

/* ---------------------------------------------------------------------------
   2) Tabla tipada (fuente del perfilado del Módulo 1.2).
      - Codigo         : código del ticket (columna REQ del archivo).
      - FechaRegistro  : FECHA convertida desde dd/mm/yyyy (estilo 103).
      - Horas          : HORAS convertida desde hh:mm:ss.
      - Minutos        : duración en minutos enteros (exacto, sin redondeo).
      - HorasDecimal   : horas en formato numérico (1:30:00 -> 1.5) para sumar
                         y promediar.
   --------------------------------------------------------------------------- */
DROP TABLE IF EXISTS dbo.Requerimientos;
GO

CREATE TABLE dbo.Requerimientos
(
    IdRegistro     INT IDENTITY(1, 1) NOT NULL,
    FilaOrigen     INT           NOT NULL,
    Id             NVARCHAR(50)  NULL,          -- viene vacío en el origen
    Codigo         NVARCHAR(30)  NULL,
    Tipo           NVARCHAR(10)  NULL,
    SistemaCanal   NVARCHAR(60)  NULL,
    Usuario        NVARCHAR(30)  NULL,
    Accion         NVARCHAR(60)  NULL,
    FechaRegistro  DATE          NULL,
    Horas          TIME(0)       NULL,
    Minutos        AS (DATEPART(HOUR, Horas) * 60 + DATEPART(MINUTE, Horas)),
    HorasDecimal   AS CAST((DATEPART(HOUR, Horas) * 60 + DATEPART(MINUTE, Horas)) / 60.0 AS DECIMAL(9, 4)),
    Estado         NVARCHAR(30)  NULL,
    FechaCarga     DATETIME2(0)  NOT NULL
        CONSTRAINT DF_Requerimientos_FechaCarga DEFAULT (SYSDATETIME()),
    CONSTRAINT PK_Requerimientos PRIMARY KEY CLUSTERED (IdRegistro)
);
GO

CREATE NONCLUSTERED INDEX IX_Requerimientos_Codigo        ON dbo.Requerimientos (Codigo);
CREATE NONCLUSTERED INDEX IX_Requerimientos_FechaRegistro ON dbo.Requerimientos (FechaRegistro);
GO

/* ---------------------------------------------------------------------------
   3) Tabla para el archivo ya limpio (salida del Módulo 2). Opcional: permite
      conectar Power BI a SQL Server en lugar de al CSV.
   --------------------------------------------------------------------------- */
DROP TABLE IF EXISTS dbo.RequerimientosLimpio;
GO

CREATE TABLE dbo.RequerimientosLimpio
(   -- mismo orden de columnas que el CSV limpio (BULK INSERT asigna por posición)
    IdRegistro           INT           NOT NULL,
    Codigo               NVARCHAR(30)  NOT NULL,
    Tipo                 NVARCHAR(10)  NOT NULL,
    SistemaCanal         NVARCHAR(60)  NOT NULL,
    Usuario              NVARCHAR(30)  NOT NULL,
    Equipo               NVARCHAR(20)  NOT NULL,
    AccionCodigo         TINYINT       NULL,
    Accion               NVARCHAR(60)  NOT NULL,
    FechaRegistro        DATE          NOT NULL,
    Anio                 SMALLINT      NOT NULL,
    Mes                  TINYINT       NOT NULL,
    AnioMes              CHAR(7)       NOT NULL,
    HorasOriginal        DECIMAL(9, 4) NULL,
    Horas                DECIMAL(9, 4) NOT NULL,
    Estado               NVARCHAR(30)  NOT NULL,
    EstadoTicket         NVARCHAR(30)  NOT NULL,
    EsResuelto           BIT           NOT NULL,
    FlagFechaImputada    BIT           NOT NULL,
    FlagHorasImputadas   BIT           NOT NULL,
    FlagHorasAjustadas   BIT           NOT NULL,
    FlagEstadoImputado   BIT           NOT NULL,
    FlagSistemaImputado  BIT           NOT NULL,
    FlagDiaSobrecargado  BIT           NOT NULL,
    FilaOrigen           INT           NOT NULL,
    FechaOriginal        VARCHAR(20)   NULL,
    CONSTRAINT PK_RequerimientosLimpio PRIMARY KEY CLUSTERED (IdRegistro)
);
GO

PRINT 'Objetos creados: stg.RequerimientosRaw, stg.vw_RequerimientosRaw_Carga, dbo.Requerimientos, dbo.RequerimientosLimpio';
GO
