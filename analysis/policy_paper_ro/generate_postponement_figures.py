"""Figurile secțiunilor „6.4 Analiza amânărilor” și „6.5 De ce se resping dosarele”: i08 (motivele de amânare, pe nivel de
automatizare), i09 (intervalul evitabil la depunere) și i10 (respingerea ca sfârșit al unei amânări neîndeplinite; rejection_reasons.json). Citesc independent_audit/out/delay_reasons.json și
postponement_solutions.json. Aceeași paletă ca raportul principal (generate_lab_figures prin
generate_institutii_figures, ca generate_impact_figures.py).

Salvează în figures_impact/ și copiază SVG-ul și în figures_institutii/, pentru că fig() din
build_raport_institutii.py citește din LS.FIG_DIR = figures_institutii.

    ..\\..\\venv\\Scripts\\python -X utf8 generate_postponement_figures.py
"""
import os, json, shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import generate_institutii_figures as GI
G = GI.G
OUTD = os.path.join(GI.HERE, "figures_impact"); os.makedirs(OUTD, exist_ok=True)
COPY_TO = os.path.join(GI.HERE, "figures_institutii")
PS = json.load(open(os.path.join(GI.IA, "out", "postponement_solutions.json"), encoding="utf-8"))
DR = {x["id"]: x for x in json.load(open(os.path.join(GI.IA, "out", "delay_reasons.json"), encoding="utf-8"))["findings"]}
INK, INK2, INK3, RULE2 = G.INK, G.INK2, G.INK3, G.RULE2
W = G.W_IN
rd = lambda x, d=1: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
# validated order (dataviz validator): adjacent pairs separated for normal and CVD vision; level is also written as text
COL = {"Standard": G.SOL, "Doar cu AI": G.WARN, "Doar cu AI avansat": G.NAVY, "Nu se poate automatiza": G.ALERT}
ABBR = {"Standard": "S", "Doar cu AI": "AI", "Doar cu AI avansat": "AI+", "Nu se poate automatiza": "J"}
SHORT = {"CAEN": "Obiect de activitate / CAEN", "SEDIU": "Sediu (dovadă, acorduri, adresă)", "CERERE": "Cererea și anexa fiscală",
         "ACT": "Act constitutiv, hotărâri, mandat", "SOLICITANT": "Solicitant, împuternicire", "ASOC_ID": "Date de identificare asociați",
         "INSTIT": "Alte instituții (cazier fiscal, avize)", "CAPITAL": "Capital social", "SEMN": "Semnătura electronică",
         "BEN_REAL": "Beneficiari reali", "DENUM": "Denumire", "TARIF": "Tarif de publicare"}


def save(fig, stem):
    G.OUT_DIR = OUTD; G.save_svg_and_png(fig, stem)
    os.makedirs(COPY_TO, exist_ok=True)
    shutil.copy2(os.path.join(OUTD, f"{stem}.svg"), os.path.join(COPY_TO, f"{stem}.svg"))


def i08():
    rows = PS["matrix"]; n = len(rows); y = np.arange(n)
    sh = np.array([100 * r["share"] for r in rows]); lo = np.array([100 * r["ci95"][0] for r in rows]); hi = np.array([100 * r["ci95"][1] for r in rows])
    fig, (ax, axl) = plt.subplots(1, 2, figsize=(W, 3.55), gridspec_kw=dict(width_ratios=[4.6, 1.15], wspace=0.04))
    for i, r in enumerate(rows):
        ax.barh(i, sh[i], height=.62, color=COL[r["headline"]], zorder=2)
        ax.text(hi[i] + .6, i, rd(sh[i]) + "%", va="center", ha="left", fontsize=6.3, color=INK)
    ax.errorbar(sh, y, xerr=[sh - lo, hi - sh], fmt="none", ecolor=INK, elinewidth=.7, capsize=1.6, zorder=3)
    k = next(i for i, r in enumerate(rows) if r["code"] == "CERERE")
    adj = float(DR["DR.category.CERERE"]["method"].split("precision/recall-adjusted ")[1].split(";")[0])
    ax.plot([100 * adj], [k], marker="D", ms=3.6, mfc="white", mec=INK, mew=.8, ls="none", zorder=4)
    ax.annotate("ajustat pentru supra-atribuire", (100 * adj, k), xytext=(100 * adj + 9.5, k + .62), fontsize=5.6, color=INK2,
                arrowprops=dict(arrowstyle="-", color=INK3, lw=.5), va="center")
    ax.set_yticks(y); ax.set_yticklabels([SHORT[r["code"]] for r in rows], fontsize=6.5); ax.invert_yaxis()
    ax.set_xlim(0, 40); ax.set_xlabel("% din amânări care invocă motivul (o amânare poate avea mai multe motive); bara neagră = IC 95%", fontsize=6.1)
    G.style_axes(ax, ygrid=False, xgrid=True)
    # right panel: every automation level involved in the category (headline = filled, others = outline)
    lv = PS["levels"]
    for i, r in enumerate(rows):
        for j, L in enumerate(lv):
            if L in r["levels_involved"]:
                full = L == r["headline"]
                axl.scatter(j, i, s=26, marker="s", color=COL[L] if full else "white", edgecolors=COL[L], linewidths=1.0, zorder=3)
    axl.set_xticks(range(len(lv))); axl.set_xticklabels([ABBR[L] for L in lv], fontsize=6.2)
    axl.set_xlim(-.6, len(lv) - .4); axl.set_ylim(ax.get_ylim()); axl.set_yticks([])
    for s in ("top", "right", "left"): axl.spines[s].set_visible(False)
    axl.spines["bottom"].set_color(RULE2); axl.set_xlabel("niveluri implicate", fontsize=6.1)
    hand = [Patch(color=COL[L], label=f"{ABBR[L]} · {L}") for L in lv] + \
           [Line2D([], [], marker="s", ls="none", mfc="white", mec=INK3, label="pătrat gol = soluție secundară")]
    fig.legend(handles=hand, loc="upper center", ncol=5, frameon=False, fontsize=5.8, bbox_to_anchor=(.5, 1.0), handlelength=1.1, columnspacing=1.1)
    fig.subplots_adjust(left=.235, right=.985, top=.9, bottom=.13)
    save(fig, "i08_motive_amanare")


def i09():
    e = PS["effect"]; da = DR["DR.avoidable.da_or_partial_all"]
    items = [("toate motivele evitabile la depunere\n(amânarea n-ar mai avea loc)", e["strict_share"], e["strict_ci95"], G.SOL),
             ("cel puțin un motiv evitabil\n(amânare mai simplă)", e["any_share"], e["any_ci95"], G.SOL_SOFT),
             ("toate motivele evitabile sau parțial\nevitabile (o parte rămâne la registrator)", da["value"], da["ci95"], G.NAVY_SOFT)]
    fig, ax = plt.subplots(figsize=(W, 1.55))
    for i, (lab, v, ci, c) in enumerate(items):
        ax.barh(i, 100 * v, height=.56, color=c, edgecolor=G.SOL if i < 2 else G.NAVY, lw=.6, zorder=2)
        ax.errorbar(100 * v, i, xerr=[[100 * (v - ci[0])], [100 * (ci[1] - v)]], fmt="none", ecolor=INK, elinewidth=.7, capsize=1.6, zorder=3)
        ax.text(100 * ci[1] + 1, i, f"{rd(100 * v)}%", va="center", fontsize=6.4, color=INK)
    ax.set_yticks(range(3)); ax.set_yticklabels([x[0] for x in items], fontsize=6.2); ax.invert_yaxis()
    ax.set_xlim(0, 105); ax.set_xlabel("% din amânările cu motiv publicat, 19.10–18.11.2026; IC 95%", fontsize=6.1)
    G.style_axes(ax, ygrid=False, xgrid=True)
    fig.subplots_adjust(left=.3, right=.98, top=.95, bottom=.27)
    save(fig, "i09_evitabil_la_depunere")


RR = {x["id"]: x for x in json.load(open(os.path.join(GI.IA, "out", "rejection_reasons.json"), encoding="utf-8"))["findings"]}


def i10():
    """Rejections as the end of unfulfilled postponements: three 100% bars (archive census, decision texts, postponement outcomes)."""
    ap = RR["RR.archive_prior_postponement.ALL"]; uf = RR["RR.mechanism.unfulfilled.ALL"]["value"]; pt = RR["RR.mechanism.m_M_PARTIAL.ALL"]["value"]
    oc = RR["RR.postponement_outcomes"]["value"]["outcome_counts"]; n_oc = sum(oc.values())
    n_ap = RR["RR.archive_context"]["value"]["rejections"]; n_tx = RR["RR.coverage"]["value"]["parsed"]
    med = ap["method"].split("rejection ")[1].split(";")[0]
    bars = [
        ("Respingeri 19.10–18.11.2026\n(toată arhiva, " + f"{n_ap:,}".replace(",", ".") + " decizii)",
         [(ap["value"], "cu amânare anterioară a aceleiași cereri", G.ALERT, "white"), (1 - ap["value"], "fără", G.NAVY_SOFT, INK)]),
        (f"Ce scrie în încheierea de respingere\n({n_tx} texte publicate)",
         [(uf - pt, "lipsurile de la amânare nerezolvate", G.ALERT, "white"), (pt, "rezolvate parțial", G.WARN, "white"),
          (1 - uf, "altă formulare", G.NAVY_SOFT, INK)]),
        ("Cereri amânate 1.09–15.10.2026,\nsoluționate până la 20.11 (" + f"{n_oc:,}".replace(",", ".") + ")",
         [(oc["Admis"] / n_oc, "admise", G.SOL, "white"), (oc["Respins"] / n_oc, "respinse", G.ALERT, "white"), (oc["Renuntat"] / n_oc, "renunțate", G.NAVY_SOFT, INK)]),
    ]
    fig, ax = plt.subplots(figsize=(W, 1.95))
    for i, (lab, segs) in enumerate(bars):
        x0 = 0
        for v, t, c, tc in segs:
            ax.barh(i, 100 * v, left=x0, height=.56, color=c, edgecolor="white", lw=1.0, zorder=2)
            if v >= .2:
                ax.text(x0 + 1.2, i, f"{rd(100 * v)}% · {t}", va="center", ha="left", fontsize=6.2, color=tc, zorder=3)
            x0 += 100 * v
    tails = [f"{rd(100 * bars[0][1][1][0])}% fără", f"{rd(100 * bars[1][1][1][0])}% parțial ·\n{rd(100 * bars[1][1][2][0])}% altă formulare",
             f"{rd(100 * bars[2][1][2][0])}% renunțate"]
    for i, t in enumerate(tails):            # the small segments are labelled to the right of the bar
        ax.text(101, i, t, va="center", ha="left", fontsize=5.8, color=INK2)
    ax.text(0, -.52, f"Respingerea vine, la mijloc, la {med.split('.')[0]} zile după amânare: imediat după expirarea termenului de completare.",
            fontsize=6.1, color=INK2, va="bottom")
    ax.set_yticks(range(len(bars))); ax.set_yticklabels([b[0] for b in bars], fontsize=6.2); ax.invert_yaxis()
    ax.set_xlim(0, 122); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=6)
    G.style_axes(ax, ygrid=False, xgrid=False)
    fig.subplots_adjust(left=.27, right=.99, top=.86, bottom=.12)
    save(fig, "i10_motive_respingere")


if __name__ == "__main__":
    for f in (i08, i09, i10):
        f(); print("ok", f.__name__)
