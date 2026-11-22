"""Figuri (PNG + SVG) din tabelele agregate: trepte de durată (event-study bins), studiu pe luna depunerii
2024 vs 2023, evantaiul veniturilor la risc pe trimestre 2027. Doar agregate."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
TAB, FIG = HERE / "tables", HERE / "figures"
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#8a8984"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": .6, "axes.axisbelow": True,
                     "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False})


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def fig_bins():
    b = pd.read_csv(TAB / "event_bins.csv")
    order = ["0-2", "3-7", "8-14", "15-30", "31-60"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    fig.subplots_adjust(wspace=.32)
    for ax, (y, scale, lab) in zip(axes, [("bs", 100, "puncte procentuale"), ("taxB_w", 1, "lei pe firmă")]):
        for k, (kind, col, name, off) in enumerate([("OLS_own_wait", BLUE, "OLS pe durata proprie", -.12),
                                                   ("RF_instrument", ORANGE, "Formă redusă pe instrument (oficiu × săpt.)", .12)]):
            d = b[(b.outcome == y) & (b.kind == kind)].set_index("bin").reindex(order)
            x = np.arange(len(order)) + off
            ok = d.coef.notna().to_numpy()
            ax.errorbar(x[ok], d.coef[ok] * scale, yerr=[(d.coef - d.ci_lo)[ok] * scale, (d.ci_hi - d.coef)[ok] * scale],
                        fmt="o", ms=5, color=col, ecolor=col, elinewidth=1.4, capsize=0, label=name)
        ax.axhline(0, color=INK2, lw=.8)
        ax.set_xticks(range(len(order)), [o + " z" for o in order])
        ax.set_xlabel("Durata (zile calendaristice): proprie / mediana LOO a celulei")
        ax.set_ylabel(lab)
    axes[0].set_title("A depus bilanț pe 2025 (vs 0–2 zile)", loc="left", color=INK, fontsize=10.5)
    axes[1].set_title("Impozit direct proxy 2025 (vs 0–2 zile)", loc="left", color=INK, fontsize=10.5)
    axes[0].legend(loc="lower left", fontsize=8.5)
    fig.text(0, -.08, "Firme J depuse și înmatriculate în 2024 (n≈90.000), FE săptămâna depunerii + oficiu, IC 95% cluster pe oficiu (42)." + chr(10) +
                      "Treapta >60 z omisă (<30 obs.). Instrument 31–60 z: 12 obs., omis.", fontsize=7.5, color=INK2)
    save(fig, "fig1_trepte_durata")


def fig_month():
    e = pd.read_csv(TAB / "event_month_2024_vs_2023.csv")
    names = {3: "mar", 4: "apr", 5: "mai", 6: "iun", 7: "iul", 8: "aug", 9: "sep", 10: "oct", 11: "nov"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    fig.subplots_adjust(wspace=.28)
    for ax, (y, scale, lab, title) in zip(axes, [("wait", 1, "zile", "Durată: 2024 minus 2023 (prima etapă)"),
                                                 ("bs", 100, "puncte procentuale", "A depus bilanț în anul următor: 2024 minus 2023")]):
        d = e[e.outcome == y].sort_values("month")
        x = d.month.to_numpy()
        ax.axvspan(7.5, 11.5, color="#f3f2ee", zorder=0)
        ax.errorbar(x, d.coef * scale, yerr=[(d.coef - d.ci_lo) * scale, (d.ci_hi - d.coef) * scale], fmt="o-", ms=5,
                    color=BLUE, lw=1.6, elinewidth=1.4)
        ax.axhline(0, color=INK2, lw=.8)
        ax.set_xticks(x, [names[m] for m in x])
        ax.set_ylabel(lab)
        ax.set_title(title, loc="left", color=INK, fontsize=10.5)
    fig.text(0, -.08, "Luna depunerii; referință iunie. Zona gri: aug.–nov. (lansarea portalului, 26.07.2024). FE săptămâna-din-an + oficiu × cohortă;" + chr(10) +
                      "IC 95% cluster pe oficiu. Rezultat: anul complet următor (FY2025 pentru 2024, FY2024 pentru 2023).", fontsize=7.5, color=INK2)
    save(fig, "fig3_studiu_luna_depunerii")


def fig_fan():
    t = pd.read_csv(TAB / "revenue_at_risk_2027.csv")
    q = ["T1_2027", "T2_2027", "T3_2027", "T4_2027"]
    x = np.arange(4)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    series = [("continuitate", "B_nerecuperat_impact_(1a+2)", BLUE, "Continuitate, lectura B (venit nerecuperat)"),
              ("continuitate", "A_doar_amanat_impact_numerar_(1c+2)", ORANGE, "Continuitate, lectura A (doar amânat, efect de numerar)"),
              ("coada_eliminata_iun2027", "B_nerecuperat_impact_(1a+2)", GREY, "Coadă eliminată până la 30.06.2027, lectura B")]
    for sc, comp, col, name in series:
        d = t[(t.scenario == sc) & (t.component == comp)].set_index("period").reindex(q)
        ax.fill_between(x, d.p10, d.p90, color=col, alpha=.16, lw=0)
        ax.plot(x, d.p50, "-o", color=col, lw=2, ms=5, label=name)
    ax.axhline(0, color=INK2, lw=.8)
    ax.set_xticks(x, ["T1 2027", "T2 2027", "T3 2027", "T4 2027"])
    ax.set_ylabel("milioane lei pe trimestru")
    ax.set_title("Venituri ale administrației publice la risc, 2027 (P50, bandă P10–P90)", loc="left", color=INK, fontsize=10.5)
    ax.legend(loc="upper left", fontsize=8.3)
    fig.text(0, -.1, "2.000 de variante ale motorului de prognoză (audit_forecast.py, nemodificat) × incertitudinea efectelor" + chr(10) +
                      "din PARTEA A × volume. Durate de 55–150 zile: în afara suportului estimării (≤35 zile, p99).", fontsize=7.3, color=INK2)
    save(fig, "fig2_evantai_venituri_la_risc_2027")


if __name__ == "__main__":
    fig_bins()
    fig_month()
    fig_fan()
    print("figures written to", FIG)
