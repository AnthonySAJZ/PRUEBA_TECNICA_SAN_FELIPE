"""
PRUEBA TÉCNICA - ANALISTA DE DATOS
MÓDULO 4: genera el dashboard interactivo HTML (alternativa a Power BI).

Lee el archivo limpio del Módulo 2, lo empaqueta en formato columnar compacto y
lo inserta junto con ECharts (Apache-2.0) en dashboard/plantilla_dashboard.html.
El resultado es un único archivo que funciona sin internet:
    dashboard/Dashboard_Requerimientos.html

Uso:
    python python/generar_dashboard.py
"""

from __future__ import annotations

import html as html_mod
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
LIMPIO = RAIZ / "data" / "clean" / "RequerimientosPruebaDatos_Limpio.csv"
PLANTILLA = RAIZ / "dashboard" / "plantilla_dashboard.html"
ECHARTS = RAIZ / "dashboard" / "vendor" / "echarts.min.js"
SALIDA = RAIZ / "dashboard" / "Dashboard_Requerimientos.html"


def codificar(serie: pd.Series, orden: list[str] | None = None) -> tuple[list[str], list[int]]:
    """Convierte una columna de texto en (catálogo, índices) para reducir tamaño."""
    catalogo = orden if orden is not None else sorted(serie.unique())
    posicion = {v: i for i, v in enumerate(catalogo)}
    return catalogo, [posicion[v] for v in serie]


def main() -> None:
    df = pd.read_csv(LIMPIO, encoding="utf-8-sig")

    codigos, c = codificar(df["Codigo"])
    tipos, t = codificar(df["Tipo"])
    sistemas, s = codificar(df["SistemaCanal"])
    usuarios, u = codificar(df["Usuario"])
    acciones, a = codificar(df["Accion"])
    equipos, e = codificar(df["Equipo"])
    meses, m = codificar(df["AnioMes"])

    datos = {
        "codigos": codigos, "tipos": tipos, "sistemas": sistemas, "usuarios": usuarios,
        "acciones": acciones, "equipos": equipos, "meses": meses,
        # orden fijo de colores del anillo: tipos de mayor a menor cantidad de tickets
        "tiposOrdenColor": df.groupby("Tipo")["Codigo"].nunique().sort_values(ascending=False).index.tolist(),
        "c": c, "t": t, "s": s, "u": u, "a": a, "e": e, "m": m,
        "h": [round(float(v), 4) for v in df["Horas"]],
        "r": df["EsResuelto"].astype(int).tolist(),
    }
    resumen = (f"{len(df):,} registros · {df['Codigo'].nunique():,} tickets · "
               f"{df['FechaRegistro'].min()} a {df['FechaRegistro'].max()}")
    meses_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
    ini, fin = df["AnioMes"].min(), df["AnioMes"].max()
    periodo = (f"{meses_es[int(ini[5:7]) - 1]}–{meses_es[int(fin[5:7]) - 1]} {fin[:4]}" if ini[:4] == fin[:4]
               else f"{meses_es[int(ini[5:7]) - 1]} {ini[:4]} – {meses_es[int(fin[5:7]) - 1]} {fin[:4]}")

    html = PLANTILLA.read_text(encoding="utf-8")
    # "<" escapado: un texto con "</script>" en los datos no puede cerrar el bloque de script
    html = html.replace("__DATA__", json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c"))
    html = html.replace("__RESUMEN__", html_mod.escape(resumen))
    html = html.replace("__PERIODO__", html_mod.escape(periodo))
    html = html.replace("__ECHARTS__", ECHARTS.read_text(encoding="utf-8"))
    SALIDA.write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {SALIDA} ({SALIDA.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
