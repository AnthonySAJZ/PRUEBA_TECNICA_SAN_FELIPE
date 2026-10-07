// ============================================================================
// PRUEBA TÉCNICA - ANALISTA DE DATOS
// MÓDULO 4 - Consulta Power Query (M) para la tabla "Requerimientos"
// Inicio > Transformar datos > Nueva consulta > Consulta en blanco >
// Editor avanzado > pegar este código. Cambiar RutaArchivoCSV por la ruta local.
// ============================================================================
let
    RutaArchivoCSV = "C:\PruebaSanFelipe\data\clean\RequerimientosPruebaDatos_Limpio.csv",

    Origen = Csv.Document(
        File.Contents(RutaArchivoCSV),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    // Los decimales del CSV usan punto: se tipan con cultura en-US para que
    // una configuración regional en español no los lea como miles.
    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"IdRegistro", Int64.Type}, {"Codigo", type text}, {"Tipo", type text},
            {"SistemaCanal", type text}, {"Usuario", type text}, {"Equipo", type text},
            {"AccionCodigo", Int64.Type}, {"Accion", type text}, {"FechaRegistro", type date},
            {"Anio", Int64.Type}, {"Mes", Int64.Type}, {"AnioMes", type text},
            {"HorasOriginal", type number}, {"Horas", type number},
            {"Estado", type text}, {"EstadoTicket", type text}, {"EsResuelto", Int64.Type},
            {"FlagFechaImputada", Int64.Type}, {"FlagHorasImputadas", Int64.Type},
            {"FlagHorasAjustadas", Int64.Type}, {"FlagEstadoImputado", Int64.Type},
            {"FlagSistemaImputado", Int64.Type}, {"FlagDiaSobrecargado", Int64.Type},
            {"FilaOrigen", Int64.Type}, {"FechaOriginal", type text}
        },
        "en-US"
    ),

    // Año de apertura del ticket, tomado del código: "REQ 2024-022552" -> 2024
    AnioTicket = Table.AddColumn(
        Tipos, "AnioTicket", each Number.FromText(Text.Middle([Codigo], 4, 4)), Int64.Type
    )
in
    AnioTicket

// ----------------------------------------------------------------------------
// Alternativa: origen SQL Server (tabla cargada con sql/04_carga_datos_limpios.sql)
// let
//     Origen = Sql.Database("localhost", "PruebaSanFelipe"),
//     Tabla  = Origen{[Schema = "dbo", Item = "RequerimientosLimpio"]}[Data],
//     AnioTicket = Table.AddColumn(Tabla, "AnioTicket",
//                    each Number.FromText(Text.Middle([Codigo], 4, 4)), Int64.Type)
// in
//     AnioTicket
// ----------------------------------------------------------------------------
