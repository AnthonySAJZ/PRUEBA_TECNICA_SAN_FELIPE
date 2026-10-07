"""
PRUEBA TÉCNICA - ANALISTA DE DATOS
MÓDULO 4: genera el proyecto de Power BI en formato PBIP.

    powerbi/pbip/Dashboard_Requerimientos.pbip
    powerbi/pbip/Dashboard_Requerimientos.SemanticModel/   modelo semántico en TMDL
    powerbi/pbip/Dashboard_Requerimientos.Report/          reporte en formato PBIR

El proyecto se abre con Power BI Desktop (Windows) haciendo doble clic en el
.pbip. Abre sin datos (no se versiona cache.abf): ajustar el parámetro
RutaArchivoCSV a la ruta local del CSV limpio (Transformar datos > Editar
parámetros) y pulsar Actualizar. Pasos completos en powerbi/GUIA_POWER_BI.md.

Los identificadores (lineageTag, logicalId) se derivan con uuid5 de nombres
fijos: regenerar el proyecto produce exactamente los mismos archivos.

Uso:
    python python/generar_pbip.py
    python python/generar_pbip.py --ruta-csv "D:\\Repos\\PRUEBA\\data\\clean\\RequerimientosPruebaDatos_Limpio.csv"

Al regenerar se reemplazan solo los archivos que crea este script; se conserva
lo que agrega Power BI Desktop (.pbi/cache.abf, .pbi/localSettings.json).
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "powerbi" / "pbip"
CSV_LIMPIO = RAIZ / "data" / "clean" / "RequerimientosPruebaDatos_Limpio.csv"
TEMA_BASE = RAIZ / "powerbi" / "recursos" / "CY24SU10.json"

NOMBRE = "Dashboard_Requerimientos"
RUTA_CSV_DEFECTO = r"C:\PruebaSanFelipe\data\clean\RequerimientosPruebaDatos_Limpio.csv"
ESPACIO_IDS = uuid.UUID("5f1c0f3e-2b7a-4e8e-9a54-7d0c6b1e2a90")

# Versiones de esquema: las más antiguas que cubren lo necesario (agosto 2025),
# para que abra cualquier Power BI Desktop del último año.
ESQ = "https://developer.microsoft.com/json-schemas/fabric"
ESQUEMA = {
    "pbip": f"{ESQ}/pbip/pbipProperties/1.0.0/schema.json",
    "platform": f"{ESQ}/gitIntegration/platformProperties/2.0.0/schema.json",
    "pbir": f"{ESQ}/item/report/definitionProperties/2.0.0/schema.json",
    "pbism": f"{ESQ}/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "editor": f"{ESQ}/item/semanticModel/editorSettings/1.0.0/schema.json",
    "version": f"{ESQ}/item/report/definition/versionMetadata/1.0.0/schema.json",
    "report": f"{ESQ}/item/report/definition/report/3.0.0/schema.json",
    "pages": f"{ESQ}/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "page": f"{ESQ}/item/report/definition/page/2.0.0/schema.json",
    "visual": f"{ESQ}/item/report/definition/visualContainer/2.2.0/schema.json",
}

# Colores fijos por tipo (mismos del dashboard HTML)
COLOR_TIPO = {"INC": "#2A78D6", "REQ": "#EB6834", "EXP": "#1BAF7A", "PRY": "#EDA100"}


def gid(*partes: str) -> str:
    return str(uuid.uuid5(ESPACIO_IDS, "/".join(partes)))


def escribir(ruta: Path, contenido: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8", newline="\n")


def escribir_json(ruta: Path, datos: dict) -> None:
    escribir(ruta, json.dumps(datos, ensure_ascii=False, indent=2) + "\n")


# =============================================================================
# MODELO SEMÁNTICO (TMDL)
# =============================================================================
T = "\t"

# (nombre, tipo M, tipo TMDL, patrón)  patrón: texto | id | suma | decimal | fecha
COLUMNAS_REQ = [
    ("IdRegistro", "Int64.Type", "int64", "id"),
    ("Codigo", "type text", "string", "texto"),
    ("Tipo", "type text", "string", "texto"),
    ("SistemaCanal", "type text", "string", "texto"),
    ("Usuario", "type text", "string", "texto"),
    ("Equipo", "type text", "string", "texto"),
    ("AccionCodigo", "Int64.Type", "int64", "id"),
    ("Accion", "type text", "string", "texto"),
    ("FechaRegistro", "type date", "dateTime", "fecha"),
    ("Anio", "Int64.Type", "int64", "id"),
    ("Mes", "Int64.Type", "int64", "id"),
    ("AnioMes", "type text", "string", "texto"),
    ("HorasOriginal", "type number", "double", "decimal"),
    ("Horas", "type number", "double", "decimal"),
    ("Estado", "type text", "string", "texto"),
    ("EstadoTicket", "type text", "string", "texto"),
    ("EsResuelto", "Int64.Type", "int64", "suma"),
    ("FlagFechaImputada", "Int64.Type", "int64", "suma"),
    ("FlagHorasImputadas", "Int64.Type", "int64", "suma"),
    ("FlagHorasAjustadas", "Int64.Type", "int64", "suma"),
    ("FlagEstadoImputado", "Int64.Type", "int64", "suma"),
    ("FlagSistemaImputado", "Int64.Type", "int64", "suma"),
    ("FlagDiaSobrecargado", "Int64.Type", "int64", "suma"),
    ("FilaOrigen", "Int64.Type", "int64", "id"),
    ("FechaOriginal", "type text", "string", "texto"),
]

# (nombre, DAX, formato, carpeta, descripción)
MEDIDAS = [
    ("Q Tickets", "DISTINCTCOUNT ( Requerimientos[Codigo] )", "#,0", None,
     "Conteo único de tickets atendidos: un ticket con varios registros cuenta 1."),
    ("Q Registros", "COUNTROWS ( Requerimientos )", "#,0", None,
     "Conteo total de registros de horas."),
    ("Q Horas", "SUM ( Requerimientos[Horas] )", "#,0", None,
     "Suma total de horas invertidas (horas tratadas en la limpieza)."),
    ("Promedio Horas x Ticket", "DIVIDE ( [Q Horas], [Q Tickets] )", "#,0.00", None,
     "Horas promedio dedicadas por ticket."),
    ("% Resueltos", """VAR TicketsResueltos =
    CALCULATE (
        DISTINCTCOUNT ( Requerimientos[Codigo] ),
        KEEPFILTERS ( Requerimientos[EstadoTicket] IN { "Cerrado", "Resuelto" } )
    )
RETURN
    DIVIDE ( TicketsResueltos, [Q Tickets] )""", "0.0%", None,
     "Proporción de tickets cerrados o resueltos (según el último estado del ticket) sobre el total."),
    ("Q Tickets Resueltos", """CALCULATE (
    DISTINCTCOUNT ( Requerimientos[Codigo] ),
    KEEPFILTERS ( Requerimientos[EstadoTicket] IN { "Cerrado", "Resuelto" } )
)""", "#,0", "Apoyo", None),
    ("Q Tickets Pendientes", "[Q Tickets] - [Q Tickets Resueltos]", "#,0", "Apoyo", None),
    ("Promedio Horas x Registro", "AVERAGE ( Requerimientos[Horas] )", "#,0.00", "Apoyo", None),
    ("Mediana Horas x Registro", "MEDIAN ( Requerimientos[Horas] )", "#,0.00", "Apoyo", None),
    ("Horas x Usuario Dia", """DIVIDE (
    [Q Horas],
    COUNTROWS ( SUMMARIZE ( Requerimientos, Requerimientos[Usuario], Requerimientos[FechaRegistro] ) )
)""", "#,0.00", "Apoyo", "Horas promedio por técnico y día trabajado (la jornada observada es ~9.5 h)."),
    ("Q Dias Sobrecargados", """COUNTROWS (
    FILTER (
        SUMMARIZE ( Requerimientos, Requerimientos[Usuario], Requerimientos[FechaRegistro] ),
        Requerimientos[Usuario] <> "NO IDENTIFICADO"
            && CALCULATE ( SUM ( Requerimientos[Horas] ) ) > 12
    )
)""", "#,0", "Apoyo", "Días-técnico con más de 12 h registradas (se excluye NO IDENTIFICADO)."),
    ("% Horas del Total", "DIVIDE ( [Q Horas], CALCULATE ( [Q Horas], ALLSELECTED ( Requerimientos ) ) )",
     "0.0%", "Apoyo", None),
    ("Q Horas Backlog Anterior 2026", """CALCULATE (
    [Q Horas],
    KEEPFILTERS ( Requerimientos[AnioTicket] < 2026 )
)""", "#,0", "Apoyo", "Horas registradas en tickets abiertos antes de 2026."),
    ("% Horas Backlog", "DIVIDE ( [Q Horas Backlog Anterior 2026], [Q Horas] )", "0.0%", "Apoyo", None),
    ("Q Tickets Mes Anterior", """IF (
    HASONEVALUE ( Calendario[AnioMes] ),
    CALCULATE ( [Q Tickets], DATEADD ( Calendario[Fecha], -1, MONTH ) )
)""", "#,0", "Inteligencia de tiempo", "Tickets del mes anterior; solo tiene sentido con un único mes en contexto."),
    ("Var % Q Tickets MoM", "DIVIDE ( [Q Tickets] - [Q Tickets Mes Anterior], [Q Tickets Mes Anterior] )",
     "0.0%", "Inteligencia de tiempo", None),
    ("Q Horas Mes Anterior", """IF (
    HASONEVALUE ( Calendario[AnioMes] ),
    CALCULATE ( [Q Horas], DATEADD ( Calendario[Fecha], -1, MONTH ) )
)""", "#,0", "Inteligencia de tiempo", "Horas del mes anterior; solo tiene sentido con un único mes en contexto."),
    ("Var % Q Horas MoM", "DIVIDE ( [Q Horas] - [Q Horas Mes Anterior], [Q Horas Mes Anterior] )",
     "0.0%", "Inteligencia de tiempo", None),
]

DAX_CALENDARIO = """VAR FechaMin = MIN ( Requerimientos[FechaRegistro] )
VAR FechaMax = MAX ( Requerimientos[FechaRegistro] )
RETURN
    SELECTCOLUMNS (
        CALENDAR ( DATE ( YEAR ( FechaMin ), MONTH ( FechaMin ), 1 ), EOMONTH ( FechaMax, 0 ) ),
        "Fecha", [Date],
        "Anio", YEAR ( [Date] ),
        "Mes", MONTH ( [Date] ),
        "AnioMes", FORMAT ( [Date], "yyyy-mm" ),
        "NombreMes",
            SWITCH (
                MONTH ( [Date] ),
                1, "Ene", 2, "Feb", 3, "Mar", 4, "Abr", 5, "May", 6, "Jun",
                7, "Jul", 8, "Ago", 9, "Set", 10, "Oct", 11, "Nov", 12, "Dic"
            ) & " " & YEAR ( [Date] ),
        "DiaSemana", WEEKDAY ( [Date], 2 )
    )"""


def m_requerimientos() -> str:
    tipos = ",\n".join(f'        {{"{n}", {tm}}}' for n, tm, _, _ in COLUMNAS_REQ)
    return f"""let
    Origen = Csv.Document(File.Contents(RutaArchivoCSV), [Delimiter = ",", Columns = {len(COLUMNAS_REQ)}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    // Los decimales del CSV usan punto: se tipan con cultura en-US
    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {{
{tipos}
        }},
        "en-US"
    ),
    // Año de apertura del ticket tomado del código: "REQ 2024-022552" -> 2024
    AnioTicket = Table.AddColumn(Tipos, "AnioTicket", each Number.FromText(Text.Middle([Codigo], 4, 4)), Int64.Type)
in
    AnioTicket"""


def nombre_tmdl(nombre: str) -> str:
    """Pone comillas simples a los nombres que no son identificadores simples."""
    simple = nombre.replace("_", "a").isalnum() and not nombre[0].isdigit()
    return nombre if simple else "'" + nombre.replace("'", "''") + "'"


def indentar(texto: str, tabs: int) -> str:
    return "\n".join((T * tabs + linea) if linea else "" for linea in texto.split("\n"))


def bloque_columna(tabla: str, nombre: str, tipo: str, patron: str, calculada: bool = False,
                   sort_by: str | None = None, es_clave: bool = False, oculta: bool = False) -> str:
    lineas = [f"{T}column {nombre_tmdl(nombre)}", f"{T*2}dataType: {tipo}"]
    if es_clave:
        lineas.append(f"{T*2}isKey")
    if oculta:
        lineas.append(f"{T*2}isHidden")
    formato = {"id": "0", "suma": "0", "decimal": "#,0.00", "fecha": "dd/mm/yyyy"}.get(patron)
    if formato:
        lineas.append(f"{T*2}formatString: {formato}")
    lineas.append(f"{T*2}lineageTag: {gid('col', tabla, nombre)}")
    lineas.append(f"{T*2}summarizeBy: {'sum' if patron in ('suma', 'decimal') else 'none'}")
    if calculada:
        lineas += [f"{T*2}isNameInferred", f"{T*2}isDataTypeInferred", f"{T*2}sourceColumn: [{nombre}]"]
    else:
        lineas.append(f"{T*2}sourceColumn: {nombre}")
    if sort_by:
        lineas.append(f"{T*2}sortByColumn: {sort_by}")
    lineas.append("")
    cambios = []
    if patron in ("decimal", "fecha"):
        cambios.append("FormatString")
    if sort_by:
        cambios.append("SortByColumn")
    if oculta:
        cambios.append("IsHidden")
    for c in cambios:
        lineas += [f"{T*2}changedProperty = {c}", ""]
    origen = "User" if patron == "id" else "Automatic"
    lineas += [f"{T*2}annotation SummarizationSetBy = {origen}", ""]
    if patron == "fecha":
        lineas += [f"{T*2}annotation UnderlyingDateTimeDataType = Date", ""]
        lineas += [f'{T*2}annotation PBI_FormatHint = {{"isDateTimeCustom":true}}', ""]
    return "\n".join(lineas)


def tmdl_requerimientos() -> str:
    partes = [f"table Requerimientos\n{T}lineageTag: {gid('tabla', 'Requerimientos')}\n"]
    # Las columnas de fecha de la tabla de hechos se ocultan: los visuales y las
    # medidas de tiempo deben usar Calendario (siguen disponibles para DAX).
    ocultas = {"FechaRegistro", "Anio", "Mes", "AnioMes"}
    for nombre, _, tipo, patron in COLUMNAS_REQ + [("AnioTicket", "Int64.Type", "int64", "id")]:
        partes.append(bloque_columna("Requerimientos", nombre, tipo, patron, oculta=nombre in ocultas))
    partes.append(f"{T}partition Requerimientos = m\n{T*2}mode: import\n{T*2}source =\n"
                  f"{indentar(m_requerimientos(), 4)}\n")
    partes.append(f"{T}annotation PBI_ResultType = Table\n")
    return "\n".join(partes) + "\n"


def tmdl_calendario() -> str:
    partes = [f"table Calendario\n{T}lineageTag: {gid('tabla', 'Calendario')}\n{T}dataCategory: Time\n"]
    partes.append(bloque_columna("Calendario", "Fecha", "dateTime", "fecha", calculada=True, es_clave=True))
    partes.append(bloque_columna("Calendario", "Anio", "int64", "id", calculada=True))
    partes.append(bloque_columna("Calendario", "Mes", "int64", "id", calculada=True))
    partes.append(bloque_columna("Calendario", "AnioMes", "string", "texto", calculada=True))
    partes.append(bloque_columna("Calendario", "NombreMes", "string", "texto", calculada=True, sort_by="AnioMes"))
    partes.append(bloque_columna("Calendario", "DiaSemana", "int64", "id", calculada=True))
    partes.append(f"{T}partition Calendario = calculated\n{T*2}mode: import\n{T*2}source =\n"
                  f"{indentar(DAX_CALENDARIO, 4)}\n")
    return "\n".join(partes) + "\n"


def tmdl_medidas() -> str:
    partes = [f"table _Medidas\n{T}lineageTag: {gid('tabla', '_Medidas')}\n"]
    for nombre, dax, formato, carpeta, descripcion in MEDIDAS:
        lineas = []
        if descripcion:
            lineas.append(f"{T}/// {descripcion}")
        if "\n" in dax:
            lineas.append(f"{T}measure {nombre_tmdl(nombre)} =")
            lineas.append(indentar(dax, 3))
        else:
            lineas.append(f"{T}measure {nombre_tmdl(nombre)} = {dax}")
        lineas.append(f"{T*2}formatString: {formato}")
        if carpeta:
            lineas.append(f"{T*2}displayFolder: {carpeta}")
        lineas.append(f"{T*2}lineageTag: {gid('medida', nombre)}")
        partes.append("\n".join(lineas) + "\n")
    partes.append(bloque_columna("_Medidas", "Columna1", "string", "texto", oculta=True))
    m_vacia = ('let\n'
               '    Origen = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i44FAA==", '
               'BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta '
               '[Serialized.Text = true]) in type table [Columna1 = _t]),\n'
               '    #"Tipo cambiado" = Table.TransformColumnTypes(Origen,{{"Columna1", type text}})\n'
               'in\n'
               '    #"Tipo cambiado"')
    partes.append(f"{T}partition _Medidas = m\n{T*2}mode: import\n{T*2}source =\n{indentar(m_vacia, 4)}\n")
    partes.append(f"{T}annotation PBI_NavigationStepName = Navigation\n")
    partes.append(f"{T}annotation PBI_ResultType = Table\n")
    return "\n".join(partes) + "\n"


def generar_modelo(base: Path, ruta_csv: str) -> None:
    d = base / "definition"
    escribir(d / "database.tmdl", f"database\n{T}compatibilityLevel: 1601\n{T}compatibilityMode: powerBI\n\n")
    escribir(d / "model.tmdl", "\n".join([
        "model Model",
        f"{T}culture: en-US",
        f"{T}defaultPowerBIDataSourceVersion: powerBI_V3",
        f"{T}sourceQueryCulture: en-US",
        f"{T}dataAccessOptions",
        f"{T*2}legacyRedirects",
        f"{T*2}returnErrorValuesAsNull",
        "",
        'annotation PBI_QueryOrder = ["RutaArchivoCSV","Requerimientos","_Medidas"]',
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        "annotation PBIDesktopVersion = 2.140.679.0 (25.02)",
        "",
        'annotation PBI_ProTooling = ["DevMode"]',
        "",
        "ref table Requerimientos",
        "ref table Calendario",
        "ref table _Medidas",
        "",
        "ref cultureInfo en-US",
        "", "",
    ]))
    escribir(d / "expressions.tmdl",
             f'expression RutaArchivoCSV = "{ruta_csv}" meta [IsParameterQuery=true, Type="Text", '
             f'IsParameterQueryRequired=true]\n{T}lineageTag: {gid("expresion", "RutaArchivoCSV")}\n\n'
             f"{T}annotation PBI_ResultType = Text\n\n")
    escribir(d / "relationships.tmdl",
             f"relationship {gid('relacion', 'Requerimientos.FechaRegistro', 'Calendario.Fecha')}\n"
             f"{T}fromColumn: Requerimientos.FechaRegistro\n{T}toColumn: Calendario.Fecha\n\n")
    escribir(d / "cultures" / "en-US.tmdl",
             f'cultureInfo en-US\n\n{T}linguisticMetadata =\n{T*3}{{\n{T*3}  "Version": "1.0.0",\n'
             f'{T*3}  "Language": "en-US"\n{T*3}}}\n{T*2}contentType: json\n\n')
    escribir(d / "tables" / "Requerimientos.tmdl", tmdl_requerimientos())
    escribir(d / "tables" / "Calendario.tmdl", tmdl_calendario())
    escribir(d / "tables" / "_Medidas.tmdl", tmdl_medidas())

    escribir_json(base / "definition.pbism", {"$schema": ESQUEMA["pbism"], "version": "4.0", "settings": {}})
    escribir_json(base / ".platform", {
        "$schema": ESQUEMA["platform"],
        "metadata": {"type": "SemanticModel", "displayName": NOMBRE},
        "config": {"version": "2.0", "logicalId": gid("item", "SemanticModel")},
    })
    escribir_json(base / ".pbi" / "editorSettings.json", {
        "$schema": ESQUEMA["editor"],
        "autodetectRelationships": False,
        "parallelQueryLoading": True,
        "typeDetectionEnabled": True,
        "relationshipImportEnabled": False,
        "shouldNotifyUserOfNameConflictResolution": True,
    })
    nodos = [("Requerimientos", 40, 20, 620), ("Calendario", 400, 20, 260), ("_Medidas", 400, 320, 360)]
    escribir_json(base / "diagramLayout.json", {
        "version": "1.1.0",
        "diagrams": [{
            "ordinal": 0,
            "scrollPosition": {"x": 0, "y": 0},
            "nodes": [{"location": {"x": x, "y": y}, "nodeIndex": t, "nodeLineageTag": gid("tabla", t),
                       "size": {"height": h, "width": 260}, "zIndex": i}
                      for i, (t, x, y, h) in enumerate(nodos)],
            "name": "All tables",
            "zoomValue": 100,
            "pinKeyFieldsToTop": False,
            "showExtraHeaderInfo": False,
            "hideKeyFieldsWhenCollapsed": False,
            "tablesLocked": False,
        }],
        "selectedDiagram": "All tables",
        "defaultDiagram": "All tables",
    })


# =============================================================================
# REPORTE (PBIR)
# =============================================================================
def lit(valor: str) -> dict:
    return {"expr": {"Literal": {"Value": valor}}}


def texto_lit(texto: str) -> dict:
    return lit("'" + texto.replace("'", "''") + "'")


def columna(tabla: str, nombre: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabla}}, "Property": nombre}}


def medida(nombre: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Medidas"}}, "Property": nombre}}


def proyeccion(campo: dict, activo: bool = False, etiqueta: str | None = None) -> dict:
    tipo = "Column" if "Column" in campo else "Measure"
    entidad = campo[tipo]["Expression"]["SourceRef"]["Entity"]
    propiedad = campo[tipo]["Property"]
    p = {"field": campo, "queryRef": f"{entidad}.{propiedad}", "nativeQueryRef": etiqueta or propiedad}
    if etiqueta:
        p["displayName"] = etiqueta
    if activo:
        p["active"] = True
    return p


def rol(*proyecciones: dict) -> dict:
    return {"projections": list(proyecciones)}


def titulo_visual(texto: str) -> dict:
    return {"title": [{"properties": {"show": lit("true"), "text": texto_lit(texto)}}]}


def contenedor(nombre: str, orden: int, x: int, y: int, w: int, h: int, visual: dict) -> dict:
    return {
        "$schema": ESQUEMA["visual"],
        "name": nombre,
        "position": {"x": x, "y": y, "z": orden * 1000, "height": h, "width": w, "tabOrder": orden * 1000},
        "visual": visual,
    }


def visual_titulo() -> dict:
    return {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{
            "textRuns": [
                {"value": "Gestión de requerimientos TI · Ene–Jun 2026",
                 "textStyle": {"fontWeight": "bold", "fontSize": "18pt", "color": "#252423"}},
                {"value": "   Tickets y horas por mes, tipo, sistema, usuario y equipo",
                 "textStyle": {"fontSize": "11pt", "color": "#605E5C"}},
            ],
            "horizontalTextAlignment": "left",
        }]}}]},
        "visualContainerObjects": {"background": [{"properties": {"show": lit("false")}}]},
    }


def visual_segmentacion(campo: dict, etiqueta: str | None) -> dict:
    return {
        "visualType": "slicer",
        "query": {"queryState": {"Values": rol(proyeccion(campo, activo=True, etiqueta=etiqueta))}},
        "objects": {
            "data": [{"properties": {"mode": texto_lit("Dropdown")}}],
            "header": [{"properties": {"show": lit("true")}}],
            "selection": [{"properties": {"selectAllCheckboxEnabled": lit("true")}}],
        },
        "drillFilterOtherVisuals": True,
    }


def visual_tarjeta(nombre_medida: str) -> dict:
    return {
        "visualType": "card",
        "query": {"queryState": {"Values": rol(proyeccion(medida(nombre_medida)))}},
        "objects": {
            "labels": [{"properties": {"fontSize": lit("24D"), "labelDisplayUnits": lit("1D")}}],
            "categoryLabels": [{"properties": {"show": lit("true"), "fontSize": lit("11D")}}],
        },
        "drillFilterOtherVisuals": True,
    }


def visual_linea(nombre_medida: str, titulo: str) -> dict:
    eje = columna("Calendario", "NombreMes")
    return {
        "visualType": "lineChart",
        "query": {
            "queryState": {"Category": rol(proyeccion(eje, activo=True)), "Y": rol(proyeccion(medida(nombre_medida)))},
            "sortDefinition": {"sort": [{"field": eje, "direction": "Ascending"}]},
        },
        "objects": {
            # Unidades "ninguna": con Auto, 2,378 h se mostraría como "2K"
            "labels": [{"properties": {"show": lit("true"), "labelDisplayUnits": lit("1D"),
                                       "labelPrecision": lit("0L")}}],
            "lineStyles": [{"properties": {"showMarker": lit("true")}}],
            "categoryAxis": [{"properties": {"showAxisTitle": lit("false")}}],
            "valueAxis": [{"properties": {"showAxisTitle": lit("false")}}],
        },
        "visualContainerObjects": titulo_visual(titulo),
        "drillFilterOtherVisuals": True,
    }


def visual_anillo() -> dict:
    tipo = columna("Requerimientos", "Tipo")
    colores = [{
        "properties": {"fill": {"solid": {"color": texto_lit(color)}}},
        "selector": {"data": [{"scopeId": {"Comparison": {
            "ComparisonKind": 0, "Left": tipo, "Right": {"Literal": {"Value": f"'{valor}'"}}}}}]},
    } for valor, color in COLOR_TIPO.items()]
    return {
        "visualType": "donutChart",
        "query": {
            "queryState": {"Category": rol(proyeccion(tipo, activo=True)), "Y": rol(proyeccion(medida("Q Tickets")))},
            "sortDefinition": {"sort": [{"field": medida("Q Tickets"), "direction": "Descending"}]},
        },
        "objects": {
            "legend": [{"properties": {"show": lit("true"), "position": texto_lit("Bottom")}}],
            "labels": [{"properties": {"show": lit("true"),
                                       "labelStyle": texto_lit("Category, data value, percent of total"),
                                       "labelDisplayUnits": lit("1D"),
                                       "percentageLabelPrecision": lit("1L")}}],
            "dataPoint": colores,
        },
        "visualContainerObjects": titulo_visual("Q Tickets por tipo"),
        "drillFilterOtherVisuals": True,
    }


def visual_dispersion() -> dict:
    return {
        "visualType": "scatterChart",
        "query": {"queryState": {
            "Category": rol(proyeccion(columna("Requerimientos", "Usuario"), activo=True)),
            "X": rol(proyeccion(medida("Q Tickets"), activo=True)),
            "Y": rol(proyeccion(medida("Q Horas"))),
            "Tooltips": rol(proyeccion(medida("Promedio Horas x Ticket"))),
        }},
        "objects": {
            "categoryLabels": [{"properties": {"show": lit("true")}}],
            "categoryAxis": [{"properties": {"showAxisTitle": lit("true")}}],
            "valueAxis": [{"properties": {"showAxisTitle": lit("true")}}],
        },
        "visualContainerObjects": titulo_visual("Eficiencia: Q Tickets vs Q Horas por usuario"),
        "drillFilterOtherVisuals": True,
    }


def visual_matriz() -> dict:
    horas = medida("Q Horas")
    return {
        "visualType": "pivotTable",
        "query": {
            "queryState": {
                "Rows": rol(proyeccion(columna("Requerimientos", "Accion"), activo=True)),
                "Columns": rol(proyeccion(columna("Requerimientos", "Usuario"), activo=True)),
                "Values": rol(proyeccion(horas)),
            },
            "sortDefinition": {"sort": [{"field": horas, "direction": "Descending"}]},
        },
        "objects": {"values": [{
            "properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
                "Input": horas,
                "FillRule": {"linearGradient2": {
                    "min": {"color": {"Literal": {"Value": "'#FFFFFF'"}}},
                    "max": {"color": {"Literal": {"Value": "'#3987E5'"}}},
                    "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}},
                }},
            }}}}}},
            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "_Medidas.Q Horas"},
        }]},
        "visualContainerObjects": titulo_visual("Matriz de trabajo: Q Horas por acción y usuario"),
        "drillFilterOtherVisuals": True,
    }


ANCHO_PAGINA, ALTO_PAGINA = 1280, 1500  # página vertical, "Ajustar al ancho"


def visuales_dashboard() -> list[dict]:
    v = [contenedor("titulo", 0, 16, 8, 1248, 44, visual_titulo())]
    segmentaciones = [
        ("slicerMes", columna("Calendario", "NombreMes"), "Mes"),
        ("slicerTipo", columna("Requerimientos", "Tipo"), None),
        ("slicerSistemaCanal", columna("Requerimientos", "SistemaCanal"), "Grupo (Sistema/Canal)"),
        ("slicerUsuario", columna("Requerimientos", "Usuario"), None),
        ("slicerEquipo", columna("Requerimientos", "Equipo"), None),
    ]
    for i, (nombre, campo, etiqueta) in enumerate(segmentaciones):
        v.append(contenedor(nombre, 1 + i, 16 + i * 252, 60, 240, 70, visual_segmentacion(campo, etiqueta)))
    tarjetas = [("cardQTickets", "Q Tickets"), ("cardQHoras", "Q Horas"),
                ("cardPromHorasTicket", "Promedio Horas x Ticket"), ("cardPctResueltos", "% Resueltos")]
    for i, (nombre, med) in enumerate(tarjetas):
        v.append(contenedor(nombre, 6 + i, 16 + i * 315, 142, 303, 96, visual_tarjeta(med)))
    v.append(contenedor("lineaTicketsMes", 10, 16, 250, 618, 250, visual_linea("Q Tickets", "Tendencia: Q Tickets por mes")))
    v.append(contenedor("lineaHorasMes", 11, 646, 250, 618, 250, visual_linea("Q Horas", "Tendencia: Q Horas por mes")))
    v.append(contenedor("anilloTicketsTipo", 12, 16, 512, 420, 300, visual_anillo()))
    v.append(contenedor("dispersionUsuarios", 13, 448, 512, 816, 300, visual_dispersion()))
    v.append(contenedor("matrizAccionUsuario", 14, 16, 824, 1248, 660, visual_matriz()))
    return v


def generar_reporte(base: Path) -> None:
    escribir_json(base / ".platform", {
        "$schema": ESQUEMA["platform"],
        "metadata": {"type": "Report", "displayName": NOMBRE},
        "config": {"version": "2.0", "logicalId": gid("item", "Report")},
    })
    escribir_json(base / "definition.pbir", {
        "$schema": ESQUEMA["pbir"],
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NOMBRE}.SemanticModel"}},
    })
    d = base / "definition"
    escribir_json(d / "version.json", {"$schema": ESQUEMA["version"], "version": "2.0.0"})
    escribir_json(d / "report.json", {
        "$schema": ESQUEMA["report"],
        "themeCollection": {"baseTheme": {
            "name": "CY24SU10",
            "reportVersionAtImport": {"visual": "2.2.0", "report": "3.0.0", "page": "2.0.0"},
            "type": "SharedResources",
        }},
        "objects": {"section": [{"properties": {"verticalAlignment": texto_lit("Top")}}]},
        "resourcePackages": [{
            "name": "SharedResources",
            "type": "SharedResources",
            "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}],
        }],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            # clic en un visual = filtrar los demás (no resaltar), igual que el dashboard HTML
            "defaultFilterActionIsDataFilter": True,
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
            "useDefaultAggregateDisplayName": True,
        },
    })
    escribir_json(d / "pages" / "pages.json",
                  {"$schema": ESQUEMA["pages"], "pageOrder": ["Dashboard"], "activePageName": "Dashboard"})
    pagina = d / "pages" / "Dashboard"
    escribir_json(pagina / "page.json", {
        "$schema": ESQUEMA["page"],
        "name": "Dashboard",
        "displayName": "Dashboard",
        "displayOption": "FitToWidth",
        "height": ALTO_PAGINA,
        "width": ANCHO_PAGINA,
    })
    for v in visuales_dashboard():
        escribir_json(pagina / "visuals" / v["name"] / "visual.json", v)
    tema = base / "StaticResources" / "SharedResources" / "BaseThemes" / "CY24SU10.json"
    tema.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMA_BASE, tema)


LEEME = """# Proyecto Power BI (PBIP)

Abrir `Dashboard_Requerimientos.pbip` con Power BI Desktop (agosto 2025 o posterior).

1. El reporte abre **sin datos** (el proyecto no versiona `cache.abf`).
2. Inicio > Transformar datos (flecha) > **Editar parámetros** > `RutaArchivoCSV` = ruta
   absoluta de `data\\clean\\RequerimientosPruebaDatos_Limpio.csv` en tu equipo > Aceptar > Aplicar cambios.
3. Inicio > **Actualizar**.
4. Comprobar los valores de control: Q Tickets 3,406 · Q Horas 16,979 · Promedio Horas x Ticket 4.98 · % Resueltos 98.4%.

Detalle, requisitos y solución de problemas: `../GUIA_POWER_BI.md`.
Este proyecto lo genera `python/generar_pbip.py`; no editar a mano lo que se vaya a regenerar.
"""


def verificar_encabezado_csv() -> None:
    """El M fija 25 columnas por nombre: si el CSV limpio cambia, fallar aquí y no en Desktop."""
    if not CSV_LIMPIO.exists():
        print(f"Aviso: no existe {CSV_LIMPIO}; no se verificó el encabezado.")
        return
    with CSV_LIMPIO.open(encoding="utf-8-sig", newline="") as f:
        encabezado = next(csv.reader(f))
    esperado = [c[0] for c in COLUMNAS_REQ]
    if encabezado != esperado:
        raise SystemExit(f"El encabezado del CSV no coincide con COLUMNAS_REQ.\nCSV:      {encabezado}\nEsperado: {esperado}")


def limpiar_salida() -> None:
    """Borra solo lo generado; conserva .pbi/cache.abf y .pbi/localSettings.json de Desktop."""
    for sub in (f"{NOMBRE}.Report/definition", f"{NOMBRE}.SemanticModel/definition",
                f"{NOMBRE}.Report/StaticResources"):
        if (SALIDA / sub).exists():
            shutil.rmtree(SALIDA / sub)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el proyecto PBIP del dashboard.")
    parser.add_argument("--ruta-csv", default=RUTA_CSV_DEFECTO,
                        help="Valor inicial del parámetro RutaArchivoCSV (ruta absoluta en Windows).")
    args = parser.parse_args()

    verificar_encabezado_csv()
    limpiar_salida()
    generar_modelo(SALIDA / f"{NOMBRE}.SemanticModel", args.ruta_csv)
    generar_reporte(SALIDA / f"{NOMBRE}.Report")
    escribir_json(SALIDA / f"{NOMBRE}.pbip", {
        "$schema": ESQUEMA["pbip"],
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NOMBRE}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    })
    escribir(SALIDA / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    escribir(SALIDA / "LEEME.md", LEEME)
    archivos = sorted(p for p in SALIDA.rglob("*") if p.is_file())
    print(f"Proyecto PBIP generado en {SALIDA} ({len(archivos)} archivos)")
    print(f"Parámetro RutaArchivoCSV = {args.ruta_csv}")
    print("Al abrir en Power BI Desktop: Transformar datos > Editar parámetros (si la ruta difiere) > Actualizar.")


if __name__ == "__main__":
    main()
