"""
PRUEBA TÉCNICA - ANALISTA DE DATOS
MÓDULO 2: Limpieza, depuración y transformación (Data Wrangling)

Lee el CSV original, aplica las reglas de negocio y exporta:
  - data/clean/RequerimientosPruebaDatos_Limpio.csv   (archivo estandarizado)
  - data/clean/RequerimientosPruebaDatos_Limpio.xlsx  (datos + diccionario + log)
  - data/clean/log_limpieza.csv                       (qué se corrigió y cuántas filas)

Uso:
    python python/limpieza.py
    python python/limpieza.py --entrada <csv_original> --salida-dir <carpeta>

Reglas de negocio (en el orden en que se ejecutan):
  0. Estructura y texto: se elimina ID (100% vacía), se renombran columnas,
     se quitan espacios duros (NBSP) y espacios sobrantes, 'NULL'/'' -> nulo.
  2. Estandarización de categorías (Código, Sistema/Canal, Acción, Estado).
  1. Remoción de duplicados: se hace DESPUÉS de estandarizar para detectar
     también duplicados "disfrazados" (p.ej. 'Cerrada' vs 'Cerrado').
  3. Normalización de fechas: dd/mm/yyyy -> ISO; fechas inválidas o vacías se
     imputan por posición (el archivo está ordenado cronológicamente).
  4. Tratamiento de anomalías en Horas: hh:mm:ss -> decimal, imputación de
     nulos por mediana de la acción, tope a valores extremos (Q3 + 3*IQR).
  5. Imputación de categorías faltantes y columnas derivadas.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA_DEF = RAIZ / "data" / "raw" / "RequerimientosPruebaDatos.csv"
SALIDA_DEF = RAIZ / "data" / "clean"
NOMBRE_SALIDA = "RequerimientosPruebaDatos_Limpio"

COLUMNAS = {
    "ID": "Id",
    "REQ": "Codigo",
    "TIPO": "Tipo",
    "SISTEMA/ CANAL": "SistemaCanal",
    "USUARIO": "Usuario",
    "ACCIÓN": "Accion",
    "FECHA": "FechaOriginal",
    "HORAS": "HorasTexto",
    "ESTADO": "Estado",
}

# --- Catálogos de estandarización (valor origen -> valor estándar) ----------
MAPA_SISTEMA = {"AGENDA PROCEDMIENTOS": "AGENDA PROCEDIMIENTOS"}  # error tipográfico

MAPA_ESTADO = {
    "Cerrada": "Cerrado",
    "Cerrado": "Cerrado",
    "Resuelta": "Resuelto",
    "Resuelto": "Resuelto",
    "Asignada a un grupo": "Asignado",
}
ESTADOS_RESUELTOS = {"Cerrado", "Resuelto"}

# Acción: se unifica sinónimo (02_Analizado) y ortografía (tildes) para que
# cada actividad tenga una sola etiqueta.
MAPA_ACCION = {"02_Analizado": "02_Analisis"}
CORRECCION_TILDES = {
    "Reunion": "Reunión",
    "Analisis": "Análisis",
    "Estimacion": "Estimación",
}

SIN_SISTEMA = "NO ESPECIFICADO"
SIN_USUARIO = "NO IDENTIFICADO"
SIN_ACCION = "00_No Especificado"
SIN_ESTADO = "Sin Estado"

PATRON_CODIGO = re.compile(r"^(REQ|INC) \d{4}-\d{6}$")
JORNADA_SOBRECARGA = 12.0  # horas/día por usuario a partir de las cuales se marca sobrecarga


class Bitacora:
    """Acumula cada corrección aplicada para el log de calidad."""

    def __init__(self) -> None:
        self.filas: list[dict] = []

    def registrar(self, regla: str, columna: str, problema: str, accion: str, filas: int) -> None:
        self.filas.append(
            {"Regla": regla, "Columna": columna, "Problema": problema,
             "Tratamiento": accion, "FilasAfectadas": int(filas)}
        )
        print(f"  [{regla}] {columna:<14} {int(filas):>5}  {problema} -> {accion}")

    def a_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.filas)


# ---------------------------------------------------------------------------
def leer_origen(ruta: Path) -> pd.DataFrame:
    """Lee el CSV tal cual (todo texto) y agrega la línea de origen."""
    df = pd.read_csv(ruta, sep=";", encoding="cp1252", dtype=str, keep_default_na=False)
    df = df.rename(columns=COLUMNAS)
    df.insert(0, "FilaOrigen", np.arange(2, len(df) + 2))  # línea 1 = cabecera
    return df


def limpiar_texto(df: pd.DataFrame, log: Bitacora) -> pd.DataFrame:
    """Regla 0: estructura y limpieza básica de texto."""
    if df["Id"].str.strip().eq("").all():
        log.registrar("0-Estructura", "ID", "Columna 100% vacía",
                      "Se elimina; se genera IdRegistro secuencial", len(df))
        df = df.drop(columns="Id")

    texto = [c for c in df.columns if c != "FilaOrigen"]
    nbsp = df[texto].apply(lambda s: s.str.contains("\xa0", regex=False)).any(axis=1).sum()
    for c in texto:
        df[c] = (df[c].str.replace("\xa0", " ", regex=False)
                      .str.replace(r"\s+", " ", regex=True)
                      .str.strip())
    log.registrar("0-Texto", "SistemaCanal", "Espacio duro (NBSP) dentro del texto",
                  "Se reemplaza por espacio normal", nbsp)

    nulos_literal = (df["Estado"].str.upper() == "NULL").sum()
    df = df.replace({"": np.nan}).replace(r"(?i)^null$", np.nan, regex=True)
    log.registrar("0-Texto", "Estado", "Texto literal 'NULL'", "Se convierte a nulo real", nulos_literal)
    return df


def estandarizar_categorias(df: pd.DataFrame, log: Bitacora) -> pd.DataFrame:
    """Regla 2: estandarización de categorías."""
    # Código: mayúsculas
    mal_caso = (df["Codigo"] != df["Codigo"].str.upper()).sum()
    df["Codigo"] = df["Codigo"].str.upper()
    log.registrar("2-Categorías", "Codigo", "Prefijo en minúsculas ('Req')", "Se pasa a mayúsculas", mal_caso)
    invalidos = (~df["Codigo"].str.match(PATRON_CODIGO)).sum()
    if invalidos:
        log.registrar("2-Categorías", "Codigo", "Código fuera de patrón 'REQ|INC AAAA-NNNNNN'",
                      "Revisar en origen", invalidos)

    # Sistema / Canal
    afectados = df["SistemaCanal"].isin(MAPA_SISTEMA.keys()).sum()
    df["SistemaCanal"] = df["SistemaCanal"].replace(MAPA_SISTEMA)
    log.registrar("2-Categorías", "SistemaCanal", "Error tipográfico 'AGENDA PROCEDMIENTOS'",
                  "Se corrige la etiqueta", afectados)

    # Acción: sinónimos y tildes
    afectados = df["Accion"].isin(MAPA_ACCION.keys()).sum()
    df["Accion"] = df["Accion"].replace(MAPA_ACCION)
    log.registrar("2-Categorías", "Accion", "Sinónimo '02_Analizado' de '02_Analisis'",
                  "Se unifica en una sola acción", afectados)
    antes = df["Accion"].copy()
    for patron, correcto in CORRECCION_TILDES.items():
        df["Accion"] = df["Accion"].str.replace(patron, correcto, regex=False)
    log.registrar("2-Categorías", "Accion", "Ortografía inconsistente (Reunion/Analisis/Estimacion sin tilde)",
                  "Se uniforma con tildes", (antes.fillna("") != df["Accion"].fillna("")).sum())

    # Estado: género y redacción. Un valor fuera del catálogo se conserva y se informa
    # (no se convierte en nulo en silencio).
    desconocidos = sorted(set(df["Estado"].dropna()) - set(MAPA_ESTADO))
    if desconocidos:
        log.registrar("2-Categorías", "Estado", f"Valor fuera de catálogo {desconocidos}",
                      "Se conserva; revisar en origen", df["Estado"].isin(desconocidos).sum())
    afectados = df["Estado"].isin([k for k, v in MAPA_ESTADO.items() if k != v]).sum()
    df["Estado"] = df["Estado"].replace(MAPA_ESTADO)
    log.registrar("2-Categorías", "Estado", "Mismo estado escrito distinto (Cerrada/Cerrado, Resuelta/Resuelto)",
                  "Se uniforma: Cerrado, Resuelto, Asignado", afectados)
    return df


def remover_duplicados(df: pd.DataFrame, log: Bitacora, exactos_origen: int) -> pd.DataFrame:
    """Regla 1: un registro de horas idéntico en todos sus campos es un duplicado."""
    clave = ["Codigo", "Tipo", "SistemaCanal", "Usuario", "Accion", "FechaOriginal", "HorasTexto", "Estado"]
    dup = df.duplicated(subset=clave, keep="first")
    log.registrar("1-Duplicados", "(todas)", "Registro idéntico byte a byte en el CSV original",
                  "Se conserva la primera aparición", exactos_origen)
    log.registrar("1-Duplicados", "(todas)", "Registro idéntico solo después de estandarizar (p.ej. Cerrada/Cerrado)",
                  "Se conserva la primera aparición", dup.sum() - exactos_origen)
    return df.loc[~dup].copy()


def normalizar_fechas(df: pd.DataFrame, log: Bitacora) -> pd.DataFrame:
    """Regla 3: fechas dd/mm/yyyy -> DATE. Inválidas/vacías se imputan por posición.

    El archivo viene ordenado cronológicamente en dos bloques (líneas 2-6,321 y
    6,322-7,159; el segundo solo tiene registros de ACARRASCO, AINGA y RRUIZ). Por eso
    un registro sin fecha válida se ubica en el día del registro válido
    inmediatamente anterior del archivo. Ninguna fecha a imputar cae al inicio de
    un bloque.
    """
    df = df.sort_values("FilaOrigen")
    fecha = pd.to_datetime(df["FechaOriginal"], format="%d/%m/%Y", errors="coerce")
    vacias = df["FechaOriginal"].isna()
    invalidas = df["FechaOriginal"].notna() & fecha.isna()

    anterior = fecha.ffill()
    siguiente = fecha.bfill()
    imputar = fecha.isna()
    mismo_dia = imputar & (anterior == siguiente)

    df["FechaRegistro"] = fecha.fillna(anterior).fillna(siguiente)
    df["FlagFechaImputada"] = imputar.astype(int)

    ejemplos = ", ".join(sorted(df.loc[invalidas, "FechaOriginal"].unique()))
    log.registrar("3-Fechas", "Fecha", f"Fecha inexistente en el calendario ({ejemplos})",
                  "Se imputa con la fecha del registro anterior (archivo cronológico)", invalidas.sum())
    log.registrar("3-Fechas", "Fecha", "Fecha vacía",
                  "Se imputa con la fecha del registro anterior (archivo cronológico)", vacias.sum())
    log.registrar("3-Fechas", "Fecha", "Fechas imputadas que estaban entre dos registros del mismo día",
                  "Informativo: imputación de confianza alta", mismo_dia.sum())
    log.registrar("3-Fechas", "Fecha", "Texto dd/mm/yyyy",
                  "Se convierte a fecha ISO (yyyy-mm-dd) + Anio, Mes, AnioMes", len(df))

    df["Anio"] = df["FechaRegistro"].dt.year
    df["Mes"] = df["FechaRegistro"].dt.month
    df["AnioMes"] = df["FechaRegistro"].dt.strftime("%Y-%m")
    return df


def tratar_horas(df: pd.DataFrame, log: Bitacora) -> pd.DataFrame:
    """Regla 4: anomalías en la métrica Horas."""
    td = pd.to_timedelta(df["HorasTexto"], errors="coerce")
    df["HorasOriginal"] = (td.dt.total_seconds() / 3600).round(4)
    log.registrar("4-Horas", "Horas", "Texto hh:mm:ss no sumable",
                  "Se convierte a horas decimales (01:30:00 -> 1.5)", len(df))

    no_validas = df["HorasOriginal"].notna() & (df["HorasOriginal"] <= 0)
    df.loc[no_validas, "HorasOriginal"] = np.nan
    log.registrar("4-Horas", "Horas", "Horas en cero o negativas", "Se tratan como nulas", no_validas.sum())

    horas = df["HorasOriginal"].copy()

    # a) Nulos -> mediana de la misma acción (si la acción falta, mediana global)
    nulos = horas.isna()
    mediana_accion = df.groupby("Accion")["HorasOriginal"].transform("median")
    horas = horas.fillna(mediana_accion).fillna(df["HorasOriginal"].median())
    df["FlagHorasImputadas"] = nulos.astype(int)
    log.registrar("4-Horas", "Horas", "Horas vacías",
                  "Se imputan con la mediana de horas de la misma acción", nulos.sum())

    # b) Extremos: cerco extremo de Tukey Q3 + 3*IQR (calculado con datos observados)
    q1, q3 = df["HorasOriginal"].quantile([0.25, 0.75])
    tope = round(q3 + 3 * (q3 - q1), 2)
    extremos = horas > tope
    df["FlagHorasAjustadas"] = extremos.astype(int)
    horas = horas.clip(upper=tope)
    log.registrar("4-Horas", "Horas",
                  f"Registro individual > {tope:.1f} h (cerco extremo Q3+3*IQR; supera una jornada de 9.5 h)",
                  f"Se acota (winsoriza) a {tope:.1f} h; el valor original queda en HorasOriginal",
                  extremos.sum())
    df["Horas"] = horas.round(4)

    # c) Carga diaria por usuario: no se modifica, se marca para análisis
    con_usuario = df["Usuario"].notna()
    carga = df[con_usuario].groupby(["Usuario", "FechaRegistro"])["Horas"].transform("sum")
    df["FlagDiaSobrecargado"] = 0
    df.loc[con_usuario, "FlagDiaSobrecargado"] = (carga > JORNADA_SOBRECARGA).astype(int)
    dias = (df[con_usuario].groupby(["Usuario", "FechaRegistro"])["Horas"].sum() > JORNADA_SOBRECARGA).sum()
    log.registrar("4-Horas", "Horas",
                  f"Usuario con más de {JORNADA_SOBRECARGA:.0f} h en un mismo día, tras acotar registros "
                  f"extremos a {tope:.0f} h ({dias} días-usuario)",
                  "Se marca FlagDiaSobrecargado (no se altera: no se sabe qué registro sobra)",
                  df["FlagDiaSobrecargado"].sum())
    return df


def imputar_categorias(df: pd.DataFrame, log: Bitacora) -> pd.DataFrame:
    """Completa categorías faltantes usando el propio ticket cuando es posible."""
    # Sistema/Canal: un ticket pertenece a un sistema -> se toma el más frecuente del ticket
    faltante = df["SistemaCanal"].isna()
    moda = df.groupby("Codigo")["SistemaCanal"].agg(
        lambda s: s.mode().iat[0] if s.notna().any() else np.nan)
    df["SistemaCanal"] = df["SistemaCanal"].fillna(df["Codigo"].map(moda))
    recuperado = faltante & df["SistemaCanal"].notna()
    df["FlagSistemaImputado"] = faltante.astype(int)
    df["SistemaCanal"] = df["SistemaCanal"].fillna(SIN_SISTEMA)
    log.registrar("5-Imputación", "SistemaCanal", "Sistema vacío; recuperado de otro registro del mismo ticket",
                  "Se usa el sistema más frecuente del ticket", recuperado.sum())
    log.registrar("5-Imputación", "SistemaCanal", "Sistema vacío sin otra referencia en el ticket",
                  f"Se etiqueta '{SIN_SISTEMA}'", (faltante & ~recuperado).sum())

    # Usuario: un ticket lo atienden varios técnicos -> no se adivina
    faltante = df["Usuario"].isna()
    df["Usuario"] = df["Usuario"].fillna(SIN_USUARIO)
    log.registrar("5-Imputación", "Usuario", "Usuario vacío (un ticket puede tener varios técnicos)",
                  f"Se etiqueta '{SIN_USUARIO}'", faltante.sum())

    faltante = df["Accion"].isna()
    df["Accion"] = df["Accion"].fillna(SIN_ACCION)
    log.registrar("5-Imputación", "Accion", "Acción vacía", f"Se etiqueta '{SIN_ACCION}'", faltante.sum())

    # Estado: es un atributo del ticket -> se toma el último estado conocido del ticket
    df = df.sort_values(["FechaRegistro", "FilaOrigen"])
    faltante = df["Estado"].isna()
    ultimo = df.dropna(subset=["Estado"]).groupby("Codigo")["Estado"].last()
    df["Estado"] = df["Estado"].fillna(df["Codigo"].map(ultimo))
    recuperado = faltante & df["Estado"].notna()
    df["FlagEstadoImputado"] = faltante.astype(int)
    df["Estado"] = df["Estado"].fillna(SIN_ESTADO)
    log.registrar("5-Imputación", "Estado", "Estado nulo; el ticket tiene estado en otro registro",
                  "Se usa el último estado conocido del ticket", recuperado.sum())
    log.registrar("5-Imputación", "Estado", "Estado nulo sin otra referencia en el ticket",
                  f"Se etiqueta '{SIN_ESTADO}' (no cuenta como resuelto)", (faltante & ~recuperado).sum())
    return df


def derivar_columnas(df: pd.DataFrame, log: Bitacora) -> pd.DataFrame:
    partes = df["Accion"].str.extract(r"^(\d+)_(.*)$")
    df["AccionCodigo"] = pd.to_numeric(partes[0], errors="coerce").astype("Int64")
    # Equipo clasifica la ACTIVIDAD (catálogo *_Datos), no a la persona: un mismo
    # técnico puede tener registros de ambos equipos.
    df["Equipo"] = np.where(df["Accion"].str.endswith("_Datos"), "Datos", "Aplicaciones")
    repetidos = df.groupby("AccionCodigo")["Accion"].nunique()
    repetidos = repetidos[repetidos > 1].index
    if len(repetidos):
        acciones = sorted(df.loc[df["AccionCodigo"].isin(repetidos), "Accion"].unique())
        log.registrar("5-Derivadas", "AccionCodigo", f"Número de actividad compartido por acciones distintas {acciones}",
                      "Se informa, no se corrige: usar Accion como clave", df["AccionCodigo"].isin(repetidos).sum())

    # Estado del ticket = estado de su último registro (el estado cambia en el tiempo:
    # un ticket puede figurar 'Asignado' y luego 'Cerrado').
    df = df.sort_values(["FechaRegistro", "FilaOrigen"])
    df["EstadoTicket"] = df.groupby("Codigo")["Estado"].transform("last")
    conflictos = (df.groupby("Codigo")["Estado"].nunique() > 1).sum()
    log.registrar("5-Derivadas", "EstadoTicket", f"Tickets con más de un estado en el periodo ({conflictos} tickets)",
                  "EstadoTicket = estado del último registro del ticket", conflictos)
    df["EsResuelto"] = df["EstadoTicket"].isin(ESTADOS_RESUELTOS).astype(int)
    return df


def exportar(df: pd.DataFrame, log: pd.DataFrame, salida: Path) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    df = df.sort_values(["FechaRegistro", "FilaOrigen"]).reset_index(drop=True)
    df.insert(0, "IdRegistro", np.arange(1, len(df) + 1))
    df["FechaRegistro"] = df["FechaRegistro"].dt.strftime("%Y-%m-%d")

    columnas = [
        "IdRegistro", "Codigo", "Tipo", "SistemaCanal", "Usuario", "Equipo",
        "AccionCodigo", "Accion", "FechaRegistro", "Anio", "Mes", "AnioMes",
        "HorasOriginal", "Horas", "Estado", "EstadoTicket", "EsResuelto",
        "FlagFechaImputada", "FlagHorasImputadas", "FlagHorasAjustadas",
        "FlagEstadoImputado", "FlagSistemaImputado", "FlagDiaSobrecargado",
        "FilaOrigen", "FechaOriginal",
    ]
    df = df[columnas]
    df.to_csv(salida / f"{NOMBRE_SALIDA}.csv", index=False, encoding="utf-8-sig", lineterminator="\n")
    log.to_csv(salida / "log_limpieza.csv", index=False, encoding="utf-8-sig", lineterminator="\n")

    # En Excel la fecha va como fecha real (en el CSV queda como texto ISO)
    datos_xl = df.assign(FechaRegistro=pd.to_datetime(df["FechaRegistro"]).dt.date)
    with pd.ExcelWriter(salida / f"{NOMBRE_SALIDA}.xlsx", engine="openpyxl", date_format="yyyy-mm-dd") as xl:
        datos_xl.to_excel(xl, sheet_name="Datos", index=False)
        diccionario().to_excel(xl, sheet_name="Diccionario", index=False)
        log.to_excel(xl, sheet_name="Log_Limpieza", index=False)
    print(f"\nArchivos generados en {salida}")


def diccionario() -> pd.DataFrame:
    filas = [
        ("IdRegistro", "Entero", "Identificador secuencial del registro limpio"),
        ("Codigo", "Texto", "Código del ticket (REQ = requerimiento, INC = incidente)"),
        ("Tipo", "Texto", "Tipo de atención: REQ, INC, EXP, PRY"),
        ("SistemaCanal", "Texto", "Sistema o canal atendido (grupo funcional)"),
        ("Usuario", "Texto", "Técnico que registró las horas"),
        ("Equipo", "Texto", "Clasifica la actividad: Datos si la acción es del catálogo *_Datos; si no, Aplicaciones"),
        ("AccionCodigo", "Entero", "Número de la actividad del catálogo (el 24 lo comparten dos acciones: usar Accion como clave)"),
        ("Accion", "Texto", "Actividad realizada (catálogo estandarizado)"),
        ("FechaRegistro", "Fecha", "Fecha del registro (yyyy-mm-dd)"),
        ("Anio", "Entero", "Año de FechaRegistro"),
        ("Mes", "Entero", "Mes de FechaRegistro (1-12)"),
        ("AnioMes", "Texto", "Año y mes de FechaRegistro (yyyy-mm)"),
        ("HorasOriginal", "Decimal", "Horas del origen en decimal (vacío si no venían)"),
        ("Horas", "Decimal", "Horas tratadas: imputadas si faltaban, acotadas si eran extremas"),
        ("Estado", "Texto", "Estado del ticket en ese registro (estandarizado)"),
        ("EstadoTicket", "Texto", "Estado del último registro del ticket"),
        ("EsResuelto", "0/1", "1 si EstadoTicket es Cerrado o Resuelto"),
        ("FlagFechaImputada", "0/1", "1 si la fecha venía vacía o inválida y se imputó por posición"),
        ("FlagHorasImputadas", "0/1", "1 si Horas venía vacía y se usó la mediana de su acción"),
        ("FlagHorasAjustadas", "0/1", "1 si HorasOriginal superaba 10 h (Q3 + 3·IQR) y se acotó a 10 h"),
        ("FlagEstadoImputado", "0/1", "1 si Estado venía nulo (se tomó del ticket o quedó 'Sin Estado')"),
        ("FlagSistemaImputado", "0/1", "1 si SistemaCanal venía vacío (se tomó del ticket o quedó 'NO ESPECIFICADO')"),
        ("FlagDiaSobrecargado", "0/1", "1 si el técnico suma más de 12 h ese día (tras acotar a 10 h); solo se marca"),
        ("FilaOrigen", "Entero", "Línea del CSV original (la 1 es la cabecera)"),
        ("FechaOriginal", "Texto", "Fecha tal como venía en el CSV"),
    ]
    return pd.DataFrame(filas, columns=["Columna", "Tipo", "Descripción"])


def resumen(antes: pd.DataFrame, despues: pd.DataFrame) -> None:
    print("\nRESUMEN ANTES vs DESPUÉS")
    print(f"  Filas: {len(antes):,} -> {len(despues):,}")
    print(f"  Tickets únicos: {antes['REQ'].nunique():,} -> {despues['Codigo'].nunique():,}")
    print(f"  Horas totales: {pd.to_timedelta(antes['HORAS'].replace('', np.nan)).dt.total_seconds().sum()/3600:,.2f}"
          f" -> {despues['Horas'].sum():,.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--entrada", type=Path, default=ENTRADA_DEF)
    parser.add_argument("--salida-dir", type=Path, default=SALIDA_DEF)
    args = parser.parse_args()

    log = Bitacora()
    print(f"Leyendo {args.entrada}")
    crudo = pd.read_csv(args.entrada, sep=";", encoding="cp1252", dtype=str, keep_default_na=False)
    df = leer_origen(args.entrada)

    df = limpiar_texto(df, log)
    df = estandarizar_categorias(df, log)
    df = remover_duplicados(df, log, exactos_origen=int(crudo.duplicated().sum()))
    df = normalizar_fechas(df, log)
    df = tratar_horas(df, log)
    df = imputar_categorias(df, log)
    df = derivar_columnas(df, log)

    exportar(df, log.a_dataframe(), args.salida_dir)
    resumen(crudo, df)


if __name__ == "__main__":
    main()
