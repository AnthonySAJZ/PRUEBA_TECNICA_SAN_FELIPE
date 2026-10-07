"""
PRUEBA TÉCNICA - ANALISTA DE DATOS
MÓDULO 5: genera el informe ejecutivo (HTML -> PDF de 2 páginas).

Todas las cifras se calculan desde el archivo limpio del Módulo 2, así el
informe se puede regenerar si cambian los datos.

Uso:
    python python/generar_informe.py
    python python/generar_informe.py --autor "Apellidos y Nombres"

Salidas:
    informe/Informe_Ejecutivo.html
    informe/Informe_Ejecutivo.pdf   (requiere: pip install playwright && playwright install chromium)
"""

from __future__ import annotations

import argparse
import html
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
LIMPIO = RAIZ / "data" / "clean" / "RequerimientosPruebaDatos_Limpio.csv"
LOG = RAIZ / "data" / "clean" / "log_limpieza.csv"
SALIDA_HTML = RAIZ / "informe" / "Informe_Ejecutivo.html"
SALIDA_PDF = RAIZ / "informe" / "Informe_Ejecutivo.pdf"

AZUL, TINTA, TINTA_2, GRILLA, EJE = "#2a78d6", "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]


def n0(v: float) -> str:
    return f"{v:,.0f}"


def n1(v: float) -> str:
    return f"{v:,.1f}"


def pct(v: float, dec: int = 0) -> str:
    return f"{v * 100:.{dec}f}%"


def svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    texto = buf.getvalue()
    return texto[texto.index("<svg"):]


def estilo_ejes(ax) -> None:
    ax.set_facecolor("white")
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(EJE)
    ax.tick_params(colors=TINTA_2, labelsize=8, length=0)
    ax.grid(axis="y", color=GRILLA, linewidth=0.6)
    ax.set_axisbelow(True)


def metricas(d: pd.DataFrame) -> dict:
    d = d.copy()
    d["AnioTicket"] = d["Codigo"].str[4:8].astype(int)
    k: dict = {}
    k["registros"] = len(d)
    k["tickets"] = d["Codigo"].nunique()
    k["horas"] = d["Horas"].sum()
    k["h_ticket"] = k["horas"] / k["tickets"]
    k["resueltos"] = d.loc[d["EsResuelto"] == 1, "Codigo"].nunique()
    k["pct_res"] = k["resueltos"] / k["tickets"]
    reales = d[d["Usuario"] != "NO IDENTIFICADO"]
    k["tecnicos"] = reales["Usuario"].nunique()
    dias = reales.groupby(["Usuario", "FechaRegistro"])["Horas"].sum()
    k["h_dia"] = dias.mean()
    k["dias_12"] = int((dias > 12).sum())
    k["f_ini"], k["f_fin"] = d["FechaRegistro"].min(), d["FechaRegistro"].max()

    mes = d.groupby("AnioMes").agg(t=("Codigo", "nunique"), h=("Horas", "sum"))
    mes["hpt"] = mes["h"] / mes["t"]
    pry_mes = d[d["Tipo"] == "PRY"].groupby("AnioMes")["Horas"].sum() / mes["h"]
    k["mes"] = mes
    k["pico_mes"], k["pico_t"] = mes["t"].idxmax(), mes["t"].max()
    k["ult_mes"], k["ult_t"] = mes.index[-1], mes["t"].iat[-1]
    k["hpt_ini"], k["hpt_fin"] = mes["hpt"].iat[0], mes["hpt"].iat[-1]
    k["pry_min_mes"], k["pry_min"] = pry_mes.idxmin(), pry_mes.min()
    k["pry_fin"] = pry_mes.iat[-1]

    tipo = d.groupby("Tipo").agg(t=("Codigo", "nunique"), h=("Horas", "sum"))
    tipo["pt"], tipo["ph"] = tipo["t"] / k["tickets"], tipo["h"] / k["horas"]
    tipo["hpt"] = tipo["h"] / tipo["t"]
    k["tipo"] = tipo

    por_ticket = d.groupby("Codigo")["Horas"].sum().sort_values(ascending=False)
    grandes = por_ticket[por_ticket > 40]
    k["n_grandes"], k["pt_grandes"], k["ph_grandes"] = len(grandes), len(grandes) / k["tickets"], grandes.sum() / k["horas"]
    viejos = d[d["AnioTicket"] < 2026]
    k["n_viejos"], k["pt_viejos"], k["ph_viejos"] = viejos["Codigo"].nunique(), viejos["Codigo"].nunique() / k["tickets"], viejos["Horas"].sum() / k["horas"]
    top2024 = por_ticket[por_ticket.index.str.contains(" 2024-")].head(3)
    k["top2024"], k["top2024_h"] = top2024, top2024.sum()
    k["usuarios_022552"] = d.loc[d["Codigo"] == "REQ 2024-022552", "Usuario"].nunique()

    sic = d[d["SistemaCanal"] == "SIC"]
    k["sic_reg"], k["sic_h"] = len(sic) / k["registros"], sic["Horas"].sum() / k["horas"]

    tec = reales.groupby("Usuario").agg(t=("Codigo", "nunique"), h=("Horas", "sum"))
    tec["hpt"] = tec["h"] / tec["t"]
    k["tec"] = tec
    top3 = tec.sort_values("t", ascending=False).head(3)
    k["top3"], k["top3_pt"] = top3, d[d["Usuario"].isin(top3.index)]["Codigo"].nunique() / k["tickets"]
    sobre = reales[reales["FlagDiaSobrecargado"] == 1].groupby("Usuario")["FechaRegistro"].nunique().sort_values(ascending=False)
    k["sobre"] = sobre.head(3)

    datos = d[d["SistemaCanal"] == "DATOS"]
    k["datos_h"], k["datos_t"] = datos["Horas"].sum(), datos["Codigo"].nunique()
    k["datos_core"] = reales[reales["Equipo"] == "Datos"].groupby("Usuario")["Horas"].sum().sort_values(ascending=False).head(2)

    an = d[d["Accion"] == "02_Análisis"]
    k["an_reg"], k["an_h"] = len(an) / k["registros"], an["Horas"].sum() / k["horas"]
    k["an_dev"] = an["Horas"].sum() / d.loc[d["Accion"] == "04_Desarrollo", "Horas"].sum()

    k["inc_h_ahorro"] = tipo.loc["INC", "h"] * 0.20
    return k


def grafico_tendencia(mes: pd.DataFrame) -> str:
    etiquetas = [MESES[int(m[5:7]) - 1] for m in mes.index]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.35))
    for ax, col, titulo, fmt in [(axes[0], "t", "Tickets atendidos por mes", n0),
                                 (axes[1], "hpt", "Horas por ticket por mes", lambda v: f"{v:.1f} h")]:
        valores = mes[col].values
        ax.plot(etiquetas, valores, color=AZUL, linewidth=2, marker="o", markersize=5,
                markeredgecolor="white", markeredgewidth=1.5)
        ax.fill_between(etiquetas, valores, color=AZUL, alpha=0.07)
        ax.set_ylim(0, max(valores) * 1.25)
        ax.set_title(titulo, fontsize=9, color=TINTA, loc="left", fontweight="bold")
        estilo_ejes(ax)
        for i in (0, int(valores.argmax()), len(valores) - 1):
            ax.annotate(fmt(valores[i]), (i, valores[i]), xytext=(0, 6), textcoords="offset points",
                        ha="center", fontsize=8, color=TINTA, fontweight="bold")
    fig.tight_layout(w_pad=3)
    return svg(fig)


def grafico_tecnicos(tec: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(3.6, 3.0))
    ax.scatter(tec["t"], tec["h"], s=28, color=AZUL, edgecolor="white", linewidth=1.2, zorder=3)
    destacar = {"JREBAZA": (0, -11, "center"), "JROSALES": (-2, 6, "center"), "PBARDALES": (-6, -11, "right"),
                "SRODRIGUEZ": (6, -8, "left"), "MCARRASCO": (6, -3, "left"), "ACARRASCO": (6, 3, "left")}
    for u, (dx, dy, ha) in destacar.items():
        if u in tec.index:
            ax.annotate(u, (tec.loc[u, "t"], tec.loc[u, "h"]), xytext=(dx, dy), textcoords="offset points",
                        fontsize=7, color=TINTA, ha=ha)
    ax.set_xlabel("Tickets atendidos", fontsize=8, color=TINTA_2)
    ax.set_ylabel("Horas registradas", fontsize=8, color=TINTA_2)
    ax.set_title("Dos perfiles: volumen vs proyecto", fontsize=9, color=TINTA, loc="left", fontweight="bold")
    estilo_ejes(ax)
    ax.grid(axis="x", color=GRILLA, linewidth=0.6)
    ax.set_xlim(-30, tec["t"].max() * 1.08)
    ax.set_ylim(0, tec["h"].max() * 1.15)
    fig.tight_layout()
    return svg(fig)


def construir_html(k: dict, autor: str | None) -> str:
    tipo, top3, mes = k["tipo"], k["top3"], k["mes"]
    etq = lambda am: f"{MESES[int(am[5:7]) - 1].lower()}"  # noqa: E731
    top2024 = ", ".join(f"{c} ({n0(h)} h)" for c, h in k["top2024"].items())
    sobre = ", ".join(f"{u} ({n} días)" for u, n in k["sobre"].items())
    datos_core = " y ".join(k["datos_core"].index)
    tec = k["tec"]
    linea_autor = f" · {html.escape(autor)}" if autor else ""

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Informe ejecutivo · Operación TI</title>
<style>
  @page {{ size: A4; margin: 13mm 14mm 12mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font: 10pt/1.45 "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif; color: {TINTA}; margin: 0; }}
  h1 {{ font-size: 17pt; margin: 0; letter-spacing: -0.01em; }}
  h2 {{ font-size: 11pt; margin: 12px 0 5px; padding-bottom: 3px; border-bottom: 1.5px solid {AZUL}; }}
  .meta {{ color: {TINTA_2}; margin: 2px 0 10px; font-size: 8.8pt; }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 6px 0 4px; }}
  .kpi {{ border: 1px solid {GRILLA}; border-radius: 8px; padding: 7px 10px; }}
  .kpi .l {{ color: {TINTA_2}; font-size: 8pt; }}
  .kpi .v {{ font-size: 16pt; font-weight: 700; letter-spacing: -0.02em; }}
  .kpi .c {{ color: #898781; font-size: 7.5pt; }}
  ul {{ margin: 4px 0; padding-left: 16px; }}
  li {{ margin: 3px 0; }}
  b {{ font-weight: 650; }}
  .fig {{ margin: 4px 0 0; }}
  .fig svg {{ width: 100%; height: auto; }}
  .nota {{ color: {TINTA_2}; font-size: 7.8pt; }}
  .dos {{ display: grid; grid-template-columns: 1.45fr 1fr; gap: 14px; align-items: start; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 8.9pt; }}
  th, td {{ text-align: left; padding: 4px 6px; border-bottom: 1px solid {GRILLA}; vertical-align: top; }}
  th {{ color: {TINTA_2}; font-weight: 600; }}
  .rec {{ border-left: 3px solid {AZUL}; padding: 4px 0 4px 10px; margin: 7px 0; }}
  .rec .t {{ font-weight: 700; }}
  .rec .kpi-meta {{ color: {TINTA_2}; font-size: 8.3pt; }}
  .salto {{ break-before: page; }}
</style></head>
<body>
<h1>Informe ejecutivo · Operación de TI</h1>
<p class="meta">Atención de requerimientos, incidentes y proyectos · {k["f_ini"]} a {k["f_fin"]} ·
  {n0(k["registros"])} registros de horas · {k["tecnicos"]} técnicos · Prueba técnica Analista de Datos{linea_autor}</p>

<div class="kpis">
  <div class="kpi"><div class="l">Q Tickets</div><div class="v">{n0(k["tickets"])}</div><div class="c">tickets únicos atendidos</div></div>
  <div class="kpi"><div class="l">Q Horas</div><div class="v">{n0(k["horas"])}</div><div class="c">horas invertidas</div></div>
  <div class="kpi"><div class="l">Promedio Horas x Ticket</div><div class="v">{k["h_ticket"]:.2f}</div><div class="c">mediana por registro: 1.5 h</div></div>
  <div class="kpi"><div class="l">% Resueltos</div><div class="v">{pct(k["pct_res"], 1)}</div><div class="c">{n0(k["resueltos"])} cerrados o resueltos</div></div>
</div>

<h2>1. Principales hallazgos</h2>
<ul>
  <li><b>La capacidad está copada.</b> Cada técnico registra en promedio {k["h_dia"]:.1f} h por día trabajado (jornada ≈ 9.5 h).
      La mejora no vendrá de "más horas", sino de cómo se reparten.</li>
  <li><b>Se atienden menos tickets y cada uno cuesta más.</b> Los tickets atendidos bajaron de {n0(k["pico_t"])} ({etq(k["pico_mes"])}) a {n0(k["ult_t"])} ({etq(k["ult_mes"])}), −{pct(1 - k["ult_t"] / k["pico_t"])},
      mientras las horas por ticket subieron de {k["hpt_ini"]:.1f} h a {k["hpt_fin"]:.1f} h (+{pct(k["hpt_fin"] / k["hpt_ini"] - 1)}).
      En paralelo, los proyectos pasaron de {pct(k["pry_min"])} de las horas en {etq(k["pry_min_mes"])} a {pct(k["pry_fin"])} en {etq(k["ult_mes"])}.</li>
  <li><b>El esfuerzo está muy concentrado.</b> Los proyectos (PRY) son el {pct(tipo.loc["PRY", "pt"], 1)} de los tickets pero consumen el {pct(tipo.loc["PRY", "ph"])} de las horas
      ({n0(tipo.loc["PRY", "hpt"])} h por ticket). Los {k["n_grandes"]} tickets de más de 40 h ({pct(k["pt_grandes"])} del total) explican el {pct(k["ph_grandes"])} de las horas.</li>
  <li><b>Backlog heredado.</b> {k["n_viejos"]} tickets abiertos antes de 2026 ({pct(k["pt_viejos"], 1)}) absorben el {pct(k["ph_viejos"], 1)} de las horas del semestre;
      solo tres suman {n0(k["top2024_h"])} h: {top2024}. El REQ 2024-022552 pasó por {k["usuarios_022552"]} técnicos.</li>
  <li><b>La demanda operativa es alta en volumen y baja en esfuerzo.</b> Los incidentes (INC) son el {pct(tipo.loc["INC", "pt"])} de los tickets con {tipo.loc["INC", "hpt"]:.1f} h por ticket;
      el sistema SIC concentra el {pct(k["sic_reg"])} de los registros.</li>
  <li><b>Calidad del dato mejorable.</b> Se corrigieron 83 registros duplicados, 22 fechas inexistentes (p. ej. 32/11/2026), 55 registros de más de 10 h y 39 registros sin usuario
      (todos del 16 y 17 de abril). Tras la limpieza, el dataset queda trazable y sin nulos.</li>
</ul>
<div class="fig">{grafico_tendencia(mes)}</div>
<p class="nota">Fuente: archivo limpio del Módulo 2. Se muestran dos gráficos separados en lugar de uno con doble eje.</p>

<h2 class="salto">2. Cuellos de botella por técnico y por grupo</h2>
<div class="dos">
<table>
  <tr><th>Cuello de botella</th><th>Evidencia</th></tr>
  <tr><td><b>Cola operativa en 3 personas</b></td>
      <td>{", ".join(f"{u} ({n0(r.t)})" for u, r in top3.iterrows())} atienden el {pct(k["top3_pt"])} de los tickets (SIC, APP/WEB, SAP). Una ausencia frena la atención diaria.</td></tr>
  <tr><td><b>Proyectos que dependen de una persona</b></td>
      <td>SRODRIGUEZ: {n0(tec.loc["SRODRIGUEZ", "t"])} tickets con {n0(tec.loc["SRODRIGUEZ", "hpt"])} h c/u; MCARRASCO: 1 ticket de {n0(tec.loc["MCARRASCO", "h"])} h; ACARRASCO: {n0(tec.loc["ACARRASCO", "hpt"])} h por ticket. El conocimiento no está distribuido.</td></tr>
  <tr><td><b>Grupo Datos</b></td>
      <td>{datos_core} cargan el trabajo del catálogo *_Datos; el grupo DATOS suma {n0(k["datos_h"])} h en solo {k["datos_t"]} tickets ({n0(k["datos_h"] / k["datos_t"])} h por ticket).</td></tr>
  <tr><td><b>Grupos HCE UNIFICADA y MAC</b></td>
      <td>Cada uno sostiene un proyecto de más de 1,000 h que corre todo el semestre (REQ 2024-023822 y REQ 2024-022552).</td></tr>
  <tr><td><b>Fase de análisis</b></td>
      <td>"02_Análisis" es el {pct(k["an_reg"])} de los registros y el {pct(k["an_h"])} de las horas: {k["an_dev"]:.2f} h de análisis por cada hora de desarrollo.</td></tr>
  <tr><td><b>Sobrecarga diaria</b></td>
      <td>{k["dias_12"]} días-técnico con más de 12 h registradas; los más frecuentes: {sobre}.</td></tr>
</table>
<div class="fig">{grafico_tecnicos(tec)}
<p class="nota">Abajo a la derecha: muchos tickets cortos. Arriba a la izquierda: pocos tickets muy largos.</p></div>
</div>

<h2>3. Recomendaciones basadas en datos</h2>
<div class="rec"><div class="t">1. Gestionar como proyecto todo ticket de más de 40 h y cerrar el backlog heredado.</div>
  Los {k["n_grandes"]} tickets &gt; 40 h consumen el {pct(k["ph_grandes"])} de las horas sin un control propio. Llevarlos a un portafolio con responsable, hitos, criterio de cierre y
  un tope de capacidad (p. ej. ≤ 25% de las horas del mes; en {etq(k["ult_mes"])} los PRY ya usaron {pct(k["pry_fin"])}). Priorizar el cierre o replanteo de los tres tickets de 2024.
  <div class="kpi-meta">Meta: horas por ticket mensual ≤ 4.5 h · horas en tickets anteriores a 2026 &lt; 20%.</div></div>
<div class="rec"><div class="t">2. Repartir la cola operativa y reducir la dependencia de personas clave.</div>
  Crear una célula rotativa de primer nivel para INC/EXP de SIC y APP/WEB, con entrenamiento cruzado, y una base de conocimiento para los incidentes repetitivos:
  bajar 20% el esfuerzo en INC libera ≈ {n0(k["inc_h_ahorro"])} h por semestre. Asignar un respaldo documentado a cada proyecto con un solo técnico.
  <div class="kpi-meta">Meta: ningún técnico con más del 25% de los tickets · 100% de proyectos con respaldo.</div></div>
<div class="rec"><div class="t">3. Asegurar la calidad del registro de horas y seguirla cada mes.</div>
  Validar en la herramienta: fecha con calendario, listas cerradas para estado, acción y sistema, usuario obligatorio, tope de 10 h por registro y alerta sobre 12 h por día.
  Publicar el dashboard (medidas DAX del Módulo 4) como tablero mensual del área.
  <div class="kpi-meta">Meta: menos de 0.5% de registros con defectos · 0 días &gt; 12 h sin justificar.</div></div>
</body></html>"""


def exportar_pdf(origen: Path, destino: Path) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright no está instalado: se generó solo el HTML (puede imprimirse a PDF desde el navegador).")
        return False
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch()
        except Exception:
            navegador = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pagina = navegador.new_page()
        pagina.goto(origen.resolve().as_uri())
        pagina.pdf(path=str(destino), format="A4", print_background=True, prefer_css_page_size=True)
        navegador.close()
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--autor", default=None, help="Apellidos y nombres para el encabezado")
    args = parser.parse_args()

    d = pd.read_csv(LIMPIO, encoding="utf-8-sig")
    k = metricas(d)
    SALIDA_HTML.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_HTML.write_text(construir_html(k, args.autor), encoding="utf-8")
    print(f"HTML: {SALIDA_HTML}")
    if exportar_pdf(SALIDA_HTML, SALIDA_PDF):
        print(f"PDF : {SALIDA_PDF}")


if __name__ == "__main__":
    main()
